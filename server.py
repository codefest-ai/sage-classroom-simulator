"""
SAGE v2 Live Server — SSE streaming + REST API for dashboard.

Stdlib only (http.server). No pip dependencies.

Usage:
    python3 server.py
    python3 server.py --port 8080 --scenario full_scenario --llm
"""

import argparse
import json
import os
import queue
import threading
import time
import uuid
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env file if present (stdlib only — no dotenv dependency)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.isfile(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from simulator.engine import SimulationEngine, SCENARIOS, CONTENT_TIMELINES
from simulator.university_presets import list_presets, get_university_info
from simulator.zoom_adapter import ZoomWebhookHandler


# ============================================================
# GLOBAL STATE
# ============================================================

KNOWN_PATTERN_TYPES = frozenset({
    "energy_decay", "equity_imbalance", "confusion_cluster",
    "silent_majority", "fade_cascade",
})

ZOOM_PROBE_FLAG = "ENABLE_ZOOM_API_PROBE"


def _empty_metrics():
    """Performance-metric telemetry container. See _build_metrics_snapshot
    for derived values.

    Tracks the four metrics defined in the Phase 4 paper Performance Metrics
    section (pattern-detection precision, throttle effectiveness, latency,
    5-way taxonomy adoption). Reset alongside session state.

    Note: response distribution and total are derived at query time from
    state.professor_actions rather than maintained as a counter, so that
    instructor edits (e.g., changing accept→reject) reflect correctly in
    the distribution without needing decrement bookkeeping.
    """
    return {
        "session_started_at": None,
        "tick_count": 0,
        "tick_latencies_ms": [],          # one entry per simulated minute
        "pattern_triggers_total": 0,      # patterns the scorer surfaced (pre-throttle)
        "pattern_triggers_emitted": 0,    # patterns that became recommendations (post-throttle)
        "pattern_triggers_throttled": 0,  # patterns suppressed by 3-min cooldown
        "pattern_evidence_valid": 0,      # patterns whose evidence dict was structurally valid AND type is known
        "pattern_counts_by_type": {},     # detections per pattern type
        "throttle_counts_by_type": {},    # throttle hits per pattern type
    }


class SessionState:
    """Holds the current simulation state."""
    def __init__(self):
        self.session_id = None
        self.engine = None
        self.is_running = False
        self.current_minute = 0
        self.current_frame = None
        self.all_frames = []
        self.events = []
        self.recommendations = []
        self.recent_rec_minutes = {}
        self.professor_actions = []
        self.metadata = {}
        self.students = []
        self.metrics = _empty_metrics()
        self.sse_queues = []  # List of queue.Queue for SSE clients
        self.lock = threading.Lock()
        self.last_touched = time.time()

    def touch(self):
        self.last_touched = time.time()

    def reset(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.is_running = False
        self.current_minute = 0
        self.current_frame = None
        self.all_frames = []
        self.events = []
        self.recommendations = []
        self.recent_rec_minutes = {}
        self.professor_actions = []
        self.metadata = {}
        self.students = []
        self.metrics = _empty_metrics()
        self.touch()

    def add_sse_client(self):
        q = queue.Queue()
        self.sse_queues.append(q)
        self.touch()
        return q

    def remove_sse_client(self, q):
        if q in self.sse_queues:
            self.sse_queues.remove(q)
        self.touch()

    def broadcast(self, event_type, data):
        self.touch()
        msg = f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"
        dead = []
        for q in self.sse_queues:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            self.sse_queues.remove(q)


SESSIONS = {}
SESSIONS_LOCK = threading.Lock()
SESSION_MAX_AGE_SEC = int(os.environ.get("SESSION_MAX_AGE_SEC", "7200"))
ZOOM = ZoomWebhookHandler(secret_token=os.environ.get("ZOOM_WEBHOOK_SECRET", ""))
SERVER_STARTED_AT = time.time()
VALID_RESPONSE_CATEGORIES = {"ignore", "acknowledge", "accept", "modify", "reject"}
VALID_INTERVENTION_TYPES = {
    "breakout", "poll", "cold_call", "pace_change", "think_pair_share", "clarification"
}
RECOMMENDATION_ACTION_MAP = {
    "equity_intervention": "think_pair_share",
    "activation": "poll",
}


def _extract_session_id(parsed=None, data=None):
    """Accept either ?session_id= / ?sid= or JSON body session_id."""
    if parsed:
        qs = parse_qs(parsed.query)
        sid = (qs.get("session_id") or qs.get("sid") or [None])[0]
        if sid:
            return sid
    if isinstance(data, dict):
        return data.get("session_id") or data.get("sid")
    return None


def _cleanup_sessions():
    now = time.time()
    stale = []
    with SESSIONS_LOCK:
        for sid, state in list(SESSIONS.items()):
            if not state.is_running and (now - state.last_touched) > SESSION_MAX_AGE_SEC:
                stale.append(sid)
        for sid in stale:
            del SESSIONS[sid]


def _normalize_intervention_type(intervention_type):
    if not intervention_type:
        return None
    normalized = RECOMMENDATION_ACTION_MAP.get(intervention_type, intervention_type)
    return normalized if normalized in VALID_INTERVENTION_TYPES else None


def _get_session(session_id=None, create=False):
    _cleanup_sessions()

    if session_id:
        with SESSIONS_LOCK:
            state = SESSIONS.get(session_id)
            if state:
                state.touch()
                return state
        if not create:
            return None

    if not create:
        return None

    state = SessionState()
    state.reset(session_id=session_id)
    with SESSIONS_LOCK:
        while state.session_id in SESSIONS:
            state.reset()
        SESSIONS[state.session_id] = state
    return state


def _percentile(values, pct):
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _build_intervention_deltas(state, window_minutes=3):
    """Compute per-response participation-index deltas around interventions.

    For each instructor response logged in state.professor_actions, looks up
    the class_engagement value at the response minute and the value
    `window_minutes` later, and reports the delta. Used by the Phase 4 paper's
    behavioral-impact paragraph to back the claim that the artifact produces
    measurable behavioral change around instructor decisions.

    Returns a list of {minute, response_category, intervention_type, before,
    after, delta} dicts, plus aggregate means by response_category.
    """
    if not state or not state.all_frames:
        return {"available": False, "window_minutes": window_minutes, "deltas": [], "means_by_category": {}}

    # Build a minute -> frame index for quick lookups. Frames are appended in
    # order, so the index is monotonic but may have gaps if a tick was skipped.
    minute_to_frame = {f.get("minute", -1): f for f in state.all_frames}

    deltas = []
    cat_aggregates = {}  # category -> [delta1, delta2, ...]

    for action in state.professor_actions:
        if not action:
            continue
        m = action.get("minute")
        if m is None:
            continue
        before_frame = minute_to_frame.get(m)
        after_frame = minute_to_frame.get(m + window_minutes)
        if not before_frame or not after_frame:
            continue
        before = before_frame.get("class_engagement")
        after = after_frame.get("class_engagement")
        if before is None or after is None:
            continue
        delta = after - before
        category = action.get("response_category", "unknown")
        deltas.append({
            "minute": m,
            "response_category": category,
            "intervention_type": action.get("intervention_type"),
            "before": round(before, 4),
            "after": round(after, 4),
            "delta": round(delta, 4),
        })
        cat_aggregates.setdefault(category, []).append(delta)

    means = {}
    for cat, values in cat_aggregates.items():
        if values:
            means[cat] = {
                "mean_delta": round(sum(values) / len(values), 4),
                "count": len(values),
            }

    return {
        "available": True,
        "window_minutes": window_minutes,
        "deltas": deltas,
        "means_by_category": means,
    }


def _build_metrics_snapshot(state):
    """Compute derived performance metrics from raw counters.

    Operationalizes the four metrics in the Phase 4 paper Performance Metrics
    section for a rule-based advisory system (not a classifier):
      - pattern_detection_precision: structurally-valid evidence dicts /
        total triggers. Deterministic; expected at 1.0.
      - throttle_effectiveness: throttled / (throttled + emitted).
      - latency_mean_ms / latency_p95_ms: per-tick processing time excluding
        the inter-tick sleep.
      - taxonomy_adoption_rate: total responses logged / total recs emitted.
      - taxonomy_distribution: counts and proportions of the five categories.
    """
    if not state:
        return {"available": False}
    m = state.metrics
    triggers_total = m["pattern_triggers_total"]
    emitted = m["pattern_triggers_emitted"]
    throttled = m["pattern_triggers_throttled"]

    if triggers_total > 0:
        precision = m["pattern_evidence_valid"] / triggers_total
    else:
        precision = None

    if (emitted + throttled) > 0:
        throttle_eff = throttled / (emitted + throttled)
    else:
        throttle_eff = None

    latencies = m["tick_latencies_ms"]
    if latencies:
        latency_mean = sum(latencies) / len(latencies)
        latency_p50 = _percentile(latencies, 50)
        latency_p95 = _percentile(latencies, 95)
    else:
        latency_mean = latency_p50 = latency_p95 = None

    # Derive response distribution + total from professor_actions at query
    # time so that instructor edits (e.g., changing accept→reject on the same
    # rec) are reflected in the latest distribution. Each rec is counted at
    # most once: if multiple action rows share a recommendation_id, the
    # latest wins (later rows overwrite earlier ones in latest_by_rec).
    # Anonymous rows (no recommendation_id) count individually.
    response_categories = {cat: 0 for cat in VALID_RESPONSE_CATEGORIES}
    latest_by_rec = {}
    anon_counter = 0
    for action in (state.professor_actions or []):
        if not action:
            continue
        cat = action.get("response_category")
        if cat not in VALID_RESPONSE_CATEGORIES:
            continue
        rec_id = action.get("recommendation_id") or action.get("rec_id")
        if not rec_id:
            rec_id = f"__anon_{anon_counter}"
            anon_counter += 1
        latest_by_rec[rec_id] = cat
    response_total = len(latest_by_rec)
    for cat in latest_by_rec.values():
        response_categories[cat] += 1

    if emitted > 0:
        adoption_rate = response_total / emitted
    else:
        adoption_rate = None

    distribution = {}
    for cat, count in response_categories.items():
        distribution[cat] = {
            "count": count,
            "proportion": (count / response_total) if response_total > 0 else 0.0,
        }

    started = m.get("session_started_at")
    session_duration_sec = (time.time() - started) if started else 0.0

    return {
        "available": True,
        "session_id": state.session_id,
        "is_running": state.is_running,
        "tick_count": m["tick_count"],
        "session_duration_sec": round(session_duration_sec, 2),
        "pattern_detection_precision": precision,
        "pattern_triggers_total": triggers_total,
        "pattern_triggers_emitted": emitted,
        "pattern_triggers_throttled": throttled,
        "pattern_counts_by_type": dict(m["pattern_counts_by_type"]),
        "throttle_counts_by_type": dict(m["throttle_counts_by_type"]),
        "throttle_effectiveness": throttle_eff,
        "latency_mean_ms": round(latency_mean, 2) if latency_mean is not None else None,
        "latency_p50_ms": round(latency_p50, 2) if latency_p50 is not None else None,
        "latency_p95_ms": round(latency_p95, 2) if latency_p95 is not None else None,
        "response_taxonomy_distribution": distribution,
        "response_total": response_total,
        "taxonomy_adoption_rate": adoption_rate,
        "behavioral_impact": _build_intervention_deltas(state, window_minutes=3),
    }


def _service_summary():
    with SESSIONS_LOCK:
        total_sessions = len(SESSIONS)
        active_sessions = sum(1 for state in SESSIONS.values() if state.is_running)
    return {
        "status": "ok",
        "service": "sage-server",
        "uptime_sec": int(time.time() - SERVER_STARTED_AT),
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "session_ttl_sec": SESSION_MAX_AGE_SEC,
        "zoom_webhook_configured": bool(os.environ.get("ZOOM_WEBHOOK_SECRET")),
        "groq_configured": bool(os.environ.get("GROQ_API_KEY")),
    }


# ============================================================
# SIMULATION RUNNER (background thread)
# ============================================================

def run_simulation_live(state, config):
    """Run simulation tick-by-tick, broadcasting each frame via SSE."""
    state.reset(session_id=config.get("session_id") or state.session_id)
    state.is_running = True
    state.touch()

    duration = config.get("duration", 45)
    scenario = config.get("scenario", "baseline")
    seed = config.get("seed", 42)
    university = config.get("university", "cgu")
    use_llm = config.get("llm", False)
    use_claude = config.get("claude", False)
    professor_style = config.get("professor_style", "adaptive")
    speed = config.get("speed", 0.5)  # seconds between ticks
    content_key = config.get("content_timeline", "sa_theory")
    content_timeline = CONTENT_TIMELINES.get(content_key, {}).get("timeline")

    # Create engine
    engine = SimulationEngine(
        duration=duration,
        seed=seed,
        scenario=scenario,
        university=university,
        use_llm=use_llm,
        use_claude=use_claude,
        content_timeline=content_timeline,
    )
    state.engine = engine
    llm_requested = bool(use_llm)
    llm_available = False
    llm_backend = None
    if getattr(engine, "_llm_client", None):
        try:
            llm_available = bool(engine._llm_client.is_available())
            llm_backend = engine._llm_client.backend_name
        except Exception:
            llm_available = False
            llm_backend = None

    # Store student metadata
    state.students = [
        {
            "student_id": p.student_id,
            "name": p.name,
            "engagement_baseline": p.engagement_baseline,
            "demographic": p.demographic,
            "archetype": getattr(p, 'archetype', None),
        }
        for p in engine.profiles
    ]
    state.metadata = {
        "session_id": state.session_id,
        "duration_minutes": duration,
        "scenario": scenario,
        "university": university,
        "professor_style": professor_style,
        "seed": seed,
        "student_count": len(engine.profiles),
        "use_llm": use_llm,
        "llm_requested": llm_requested,
        "llm_available": llm_available,
        "llm_effective": llm_requested and llm_available,
        "llm_backend": llm_backend,
        "runtime_mode": "ai" if (llm_requested and llm_available) else "rules",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # Broadcast session start
    state.metrics["session_started_at"] = time.time()
    state.broadcast("session_start", {
        "metadata": state.metadata,
        "students": state.students,
    })

    # Import professor
    from simulator.professor import SimulatedProfessor
    try:
        from simulator.professor_agent import LLMProfessor
        has_llm_prof = True
    except ImportError:
        has_llm_prof = False

    if use_llm and has_llm_prof and professor_style != "none":
        prof = LLMProfessor(style=professor_style)
    elif professor_style != "none":
        prof = SimulatedProfessor(style=professor_style)
    else:
        prof = None

    # Run tick by tick
    for frame in engine.step():
        if not state.is_running:
            break

        tick_start = time.time()

        with state.lock:
            state.touch()
            state.current_minute = frame["minute"]
            state.current_frame = frame
            state.all_frames.append(frame)
            state.metrics["tick_count"] += 1

            # Collect events for this minute
            minute_events = [e for e in engine.events if hasattr(e, 'minute') and e.minute == frame["minute"]]
            # Also store serialized events in state
            for e in minute_events:
                state.events.append({"minute": e.minute, "event_type": e.event_type, "student_id": e.student_id, "data": e.data})

            # Get recommendations, with per-pattern throttling so the same
            # rule-based advisory doesn't spam the log every minute.
            REC_COOLDOWN_MINUTES = 3
            raw_recs = engine.scorer.get_recommendations(engine._last_class_snapshot) if hasattr(engine, '_last_class_snapshot') and engine._last_class_snapshot else []
            recs = []
            metrics = state.metrics
            for idx, r in enumerate(raw_recs):
                pattern_type = (r.get("evidence") or {}).get("type") or r.get("action") or "unknown"
                metrics["pattern_triggers_total"] += 1
                metrics["pattern_counts_by_type"][pattern_type] = (
                    metrics["pattern_counts_by_type"].get(pattern_type, 0) + 1
                )
                # Pattern-detection precision sanity-check: scorer-emitted recs
                # must carry a structurally valid evidence dict whose type is
                # in the known pattern set. An unknown type counts as invalid
                # (a regression signal) rather than silently passing.
                evidence = r.get("evidence") or {}
                if (isinstance(evidence, dict)
                        and evidence.get("type") in KNOWN_PATTERN_TYPES):
                    metrics["pattern_evidence_valid"] += 1
                last_minute = state.recent_rec_minutes.get(pattern_type, -10**9)
                if frame["minute"] - last_minute < REC_COOLDOWN_MINUTES:
                    metrics["pattern_triggers_throttled"] += 1
                    metrics["throttle_counts_by_type"][pattern_type] = (
                        metrics["throttle_counts_by_type"].get(pattern_type, 0) + 1
                    )
                    continue
                state.recent_rec_minutes[pattern_type] = frame["minute"]
                r["rec_id"] = r.get("rec_id") or f"{frame['minute']}-{len(state.recommendations) + idx}"
                r["minute"] = frame["minute"]
                r["pattern_type"] = pattern_type
                state.recommendations.append(r)
                metrics["pattern_triggers_emitted"] += 1
                recs.append(r)

            # Professor decisions
            prof_action = None
            if prof and recs:
                try:
                    if hasattr(prof, 'decide_from_dashboard'):
                        # LLM professor — pass content block with instructor notes
                        dashboard_state = _build_dashboard_state(state)
                        from simulator.engine import get_content_at_minute
                        content_block = get_content_at_minute(engine.content_timeline, frame["minute"])
                        prof_action = prof.decide_from_dashboard(dashboard_state, frame["minute"], content_block=content_block)
                    else:
                        # Rule-based professor
                        actions = prof.process_recommendations(recs, frame["minute"])
                        if actions:
                            source_rec = recs[0] if recs else {}
                            prof_action = {
                                "minute": actions[0].minute,
                                "response_category": actions[0].response_category,
                                "intervention_type": actions[0].intervention_type,
                                "rationale": actions[0].rationale,
                                "spoken_text": actions[0].spoken_text,
                                "rec_id": source_rec.get("rec_id"),
                                "recommendation_message": source_rec.get("message"),
                                "priority": source_rec.get("priority"),
                                "source": "simulated_professor",
                            }
                except Exception as e:
                    prof_action = None

            if prof_action:
                state.professor_actions.append(prof_action)
                # If professor acts, inject intervention
                if prof_action.get("intervention_type"):
                    engine.add_intervention(
                        frame["minute"] + 1,
                        prof_action["intervention_type"]
                    )

        # Record tick latency (work-only, excludes the speed-sleep below).
        # Cap retention at 1024 entries so a long session doesn't grow unbounded.
        # Acquire the lock so a concurrent /api/metrics read sees a consistent
        # latencies list (avoids torn-read against the reassignment trim).
        tick_latency_ms = (time.time() - tick_start) * 1000.0
        with state.lock:
            state.metrics["tick_latencies_ms"].append(tick_latency_ms)
            if len(state.metrics["tick_latencies_ms"]) > 1024:
                state.metrics["tick_latencies_ms"] = state.metrics["tick_latencies_ms"][-1024:]

        # Broadcast frame
        state.broadcast("frame", {
            "frame": frame,
            "events": [{"minute": e.minute, "event_type": e.event_type, "student_id": e.student_id, "data": e.data} for e in minute_events],
            "recommendations": recs,
            "professor_action": prof_action,
        })

        time.sleep(speed)

    # Session complete
    state.is_running = False
    state.broadcast("session_end", {
        "session_id": state.session_id,
        "total_minutes": state.current_minute,
        "total_recommendations": len(state.recommendations),
        "total_professor_actions": len(state.professor_actions),
    })


def _build_dashboard_state(state):
    """Build the exact JSON the frontend renders — this is what the professor sees."""
    if not state:
        return {}
    frame = state.current_frame
    if not frame:
        return {}
    return {
        "minute": frame["minute"],
        "class_engagement": frame["class_engagement"],
        "speaking_gini": frame.get("speaking_gini", 0),
        "active_speakers": frame.get("active_speakers", 0),
        "patterns": frame.get("patterns", []),
        "students": frame.get("students", []),
        "recent_recommendations": state.recommendations[-5:] if state.recommendations else [],
        "recent_chat": [e for e in state.events if e.get("event_type") == "chat"][-10:],
        "professor_actions": state.professor_actions[-5:] if state.professor_actions else [],
        "metadata": state.metadata,
    }


# ============================================================
# HTTP HANDLER
# ============================================================

class SAGEHandler(SimpleHTTPRequestHandler):
    """Custom handler for SAGE API + static files."""

    def __init__(self, *args, **kwargs):
        # Serve from the project directory
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        session_id = _extract_session_id(parsed)
        state = _get_session(session_id, create=False) if session_id else None

        if path == "/" or path == "/index.html":
            # Serve dashboard
            self._serve_file("dashboard/index.html", "text/html")

        elif path == "/api/stream":
            self._handle_sse(parsed)

        elif path == "/api/state":
            self._json_response(_build_dashboard_state(state))

        elif path == "/api/dashboard-state":
            self._json_response(_build_dashboard_state(state))

        elif path == "/api/session":
            self._json_response({
                "session_id": state.session_id if state else session_id,
                "is_running": state.is_running if state else False,
                "current_minute": state.current_minute if state else 0,
                "metadata": state.metadata if state else {},
                "students": state.students if state else [],
                "service": "ok",
            })

        elif path == "/api/health":
            self._json_response(_service_summary())

        elif path == "/api/metrics":
            # Performance-metric telemetry for the active session. Backs the
            # paper's Performance Metrics section; consumed by the dashboard
            # live-metrics panel and the SAGE evaluation-run export.
            # Acquire state.lock to avoid torn reads while a tick is mutating
            # the metrics dict (latencies list trim + counter increments).
            if state:
                with state.lock:
                    snapshot = _build_metrics_snapshot(state)
            else:
                snapshot = _build_metrics_snapshot(state)
            self._json_response(snapshot)

        elif path == "/api/export":
            # SAGE evaluation-run export — single-shot citable artifact for
            # the paper's Analytical (Simulation) section. JSON only; the
            # CSV view of the timeline is included as a string field so the
            # whole run is one downloadable file.
            self._handle_export(parsed, state)

        elif path == "/api/presets":
            presets = {}
            for key in list_presets():
                presets[key] = get_university_info(key)
            self._json_response(presets)

        elif path == "/api/content-timelines":
            self._json_response({
                key: {"name": val["name"], "blocks": len(val["timeline"])}
                for key, val in CONTENT_TIMELINES.items()
            })

        elif path == "/api/history":
            self._json_response({
                "timeline": state.all_frames if state else [],
                "events": state.events if state else [],
                "recommendations": state.recommendations if state else [],
                "professor_actions": state.professor_actions if state else [],
            })

        elif path == "/api/zoom/state":
            # Live Zoom meeting state as dashboard frame.
            # Return 200 with an explicit inactive payload so the dashboard can
            # distinguish "no meeting yet" from a live-path failure.
            frame = ZOOM.get_active_frame()
            if frame:
                self._json_response(frame)
            else:
                self._json_response({
                    "active": False,
                    "reason": "No active Zoom meeting has been seen on this server yet.",
                    "students": [],
                    "patterns": [],
                })

        elif path == "/api/zoom/history":
            history = ZOOM.get_active_history()
            if history:
                self._json_response(history)
            else:
                self._json_response({
                    "active": False,
                    "reason": "No active Zoom meeting history is available.",
                    "participants": [],
                    "chat_messages": [],
                })

        elif path == "/api/zoom/debug":
            self._json_response(ZOOM.get_debug_snapshot())

        elif path == "/api/zoom/probe":
            self._handle_zoom_probe(parsed)

        elif path == "/api/zoom/probe/meetings":
            self._handle_zoom_probe_meetings(parsed)

        elif path == "/api/zoom/probe/participants":
            self._handle_zoom_probe_participants(parsed)

        elif path.startswith("/dashboard/"):
            # Serve static dashboard files
            rel_path = path.lstrip("/")
            self._serve_file(rel_path, self._guess_type(rel_path))

        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if path == "/api/start":
            self._handle_start(data)

        elif path == "/api/stop":
            session_id = _extract_session_id(parsed, data)
            state = _get_session(session_id, create=False)
            if state:
                state.is_running = False
            self._json_response({"status": "stopped", "session_id": session_id})

        elif path == "/api/intervention":
            self._handle_intervention(data)

        elif path == "/api/response":
            self._handle_response(data)

        elif path == "/api/zoom/response":
            self._handle_zoom_response(data)

        elif path == "/api/zoom/webhook":
            # Zoom sends webhook events here
            event_name = data.get("event", "")
            signature = self.headers.get("x-zm-signature", "")
            timestamp = self.headers.get("x-zm-request-timestamp", "")
            secret_configured = bool(getattr(ZOOM, "secret_token", None))
            if secret_configured:
                # When a secret is configured, require signed requests — do not
                # silently accept requests that omit the signature headers.
                if not signature or not timestamp or not ZOOM.verify_webhook(body, signature, timestamp):
                    print(f"[zoom webhook] signature verification failed event={event_name or 'unknown'} (missing_headers={not signature or not timestamp})")
                    self._json_response({"error": "Invalid Zoom webhook signature"}, status=401)
                    return
            elif signature and timestamp and not ZOOM.verify_webhook(body, signature, timestamp):
                print(f"[zoom webhook] signature verification failed event={event_name or 'unknown'}")
                self._json_response({"error": "Invalid Zoom webhook signature"}, status=401)
                return
            payload_obj = data.get("payload", {}).get("object", {}) or {}
            meeting_id = payload_obj.get("id", "")
            print(f"[zoom webhook] event={event_name or 'unknown'} meeting_id={meeting_id or 'n/a'}")
            result = ZOOM.handle_event(data)
            if result:
                self._json_response(result)
            else:
                self._json_response({"status": "ok"})

        else:
            self.send_error(404, "Not found")

    default_llm = False  # Set by CLI --llm flag

    def _handle_start(self, config):
        """Start a new simulation in a background thread."""
        session_id = _extract_session_id(data=config)
        state = _get_session(session_id, create=True)

        if state.is_running:
            self._json_response({"error": "Simulation already running"}, status=409)
            return

        # Apply CLI default if dashboard didn't specify
        if "llm" not in config:
            config["llm"] = self.default_llm
        config["session_id"] = state.session_id

        thread = threading.Thread(
            target=run_simulation_live,
            args=(state, config),
            daemon=True,
        )
        thread.start()

        # Wait briefly for session_id to be set
        time.sleep(0.1)

        self._json_response({
            "status": "started",
            "session_id": state.session_id,
            "config": config,
        })

    def _handle_intervention(self, data):
        """Inject an intervention mid-simulation."""
        session_id = _extract_session_id(data=data)
        state = _get_session(session_id, create=False)

        if not state or not state.is_running or not state.engine:
            self._json_response({"error": "No active simulation"}, status=400)
            return

        itype = data.get("type", "poll")
        target = data.get("target_student")
        minute = state.current_minute + 1

        state.engine.add_intervention(minute, itype, target)
        self._json_response({
            "status": "intervention_scheduled",
            "minute": minute,
            "type": itype,
            "session_id": state.session_id,
        })

    def _handle_response(self, data):
        """Record a manual instructor response and optionally schedule an intervention."""
        session_id = _extract_session_id(data=data)
        state = _get_session(session_id, create=False)

        if not state:
            self._json_response({"error": "No active session"}, status=400)
            return

        category = data.get("response_category") or data.get("category")
        if category not in VALID_RESPONSE_CATEGORIES:
            self._json_response({"error": "Invalid response category"}, status=400)
            return

        recommendation = data.get("recommendation") or {}
        recommendation_id = data.get("recommendation_id") or recommendation.get("rec_id")
        recommended_action = (
            data.get("recommended_action")
            or recommendation.get("action")
        )
        intervention_type = _normalize_intervention_type(
            data.get("intervention_type") or recommended_action
        ) if category in {"accept", "modify"} else None

        try:
            minute = int(data.get("minute") or state.current_minute or 0)
        except (TypeError, ValueError):
            minute = state.current_minute or 0

        action = {
            "minute": minute,
            "recommendation_id": recommendation_id,
            "response_category": category,
            "intervention_type": intervention_type,
            "rationale": data.get("rationale") or f"Manual instructor chose {category}",
            "spoken_text": data.get("spoken_text"),
            "recommendation": data.get("recommendation_message") or recommendation.get("message"),
            "recommendation_action": recommended_action,
            "recommendation_priority": data.get("recommendation_priority") or recommendation.get("priority"),
            "response_source": "manual",
        }

        with state.lock:
            existing = None
            if recommendation_id:
                for idx, old in enumerate(state.professor_actions):
                    if old.get("response_source") == "manual" and old.get("recommendation_id") == recommendation_id:
                        existing = idx
                        break
            if existing is None:
                state.professor_actions.append(action)
            else:
                state.professor_actions[existing] = action
            # Note: response distribution + total are derived from
            # state.professor_actions at /api/metrics query time (see
            # _build_metrics_snapshot) so instructor edits are reflected
            # in the latest distribution without needing decrement
            # bookkeeping here.

        scheduled_minute = None
        if intervention_type and state.is_running and state.engine:
            scheduled_minute = state.current_minute + 1
            state.engine.add_intervention(scheduled_minute, intervention_type)

        state.touch()
        self._json_response({
            "status": "response_logged",
            "session_id": state.session_id,
            "scheduled_minute": scheduled_minute,
            "action": action,
        })

    def _handle_zoom_response(self, data):
        """Record a manual instructor response against the active live Zoom meeting."""
        frame = ZOOM.get_active_frame()
        if not frame or frame.get("active") is False:
            self._json_response({"error": "No active Zoom meeting"}, status=400)
            return

        category = data.get("response_category") or data.get("category")
        if category not in VALID_RESPONSE_CATEGORIES:
            self._json_response({"error": "Invalid response category"}, status=400)
            return

        recommendation = data.get("recommendation") or {}
        recommendation_id = data.get("recommendation_id") or recommendation.get("rec_id")
        recommended_action = (
            data.get("recommended_action")
            or recommendation.get("action")
        )
        intervention_type = _normalize_intervention_type(
            data.get("intervention_type") or recommended_action
        ) if category in {"accept", "modify"} else None

        try:
            minute = int(data.get("minute") or frame.get("minute") or 0)
        except (TypeError, ValueError):
            minute = frame.get("minute") or 0

        action = {
            "minute": minute,
            "recommendation_id": recommendation_id,
            "response_category": category,
            "intervention_type": intervention_type,
            "rationale": data.get("rationale") or f"Live instructor chose {category}",
            "spoken_text": data.get("spoken_text"),
            "recommendation": data.get("recommendation_message") or recommendation.get("message"),
            "recommendation_action": recommended_action,
            "recommendation_priority": data.get("recommendation_priority") or recommendation.get("priority"),
            "response_source": "live_manual",
        }

        result = ZOOM.record_active_professor_action(action)
        if not result:
            self._json_response({"error": "No active Zoom meeting"}, status=400)
            return

        self._json_response({
            "status": "response_logged",
            "meeting_id": result["meeting_id"],
            "scheduled_minute": None,
            "action": result["action"],
            "note": "Decision recorded for the live evaluation receipt. Execute any chosen instructional move directly in Zoom.",
        })

    def _zoom_client_from_request(self, parsed):
        """Build a ZoomAPIClient from query-string token override or env."""
        from simulator.zoom_api_client import ZoomAPIClient
        if os.environ.get(ZOOM_PROBE_FLAG, "").lower() not in {"1", "true", "yes"}:
            return None, (
                f"Zoom API probe endpoints are disabled. Set {ZOOM_PROBE_FLAG}=1 "
                "for local development only; do not enable on public demo hosts."
            )
        qs = parse_qs(parsed.query)
        token = (qs.get("token") or [None])[0] or os.environ.get("ZOOM_API_TOKEN", "")
        token = (token or "").strip()
        if not token:
            return None, "ZOOM_API_TOKEN not set in env and no ?token= override provided. Paste a Zoom OAuth or JWT bearer to test the integration locally."
        try:
            return ZoomAPIClient(token=token), None
        except ValueError as e:
            return None, str(e)

    def _handle_zoom_probe(self, parsed):
        from simulator.zoom_api_client import ZoomAPIError
        client, err = self._zoom_client_from_request(parsed)
        if not client:
            self._json_response({"ok": False, "error": err}, status=400)
            return
        try:
            me = client.get_me()
            self._json_response({"ok": True, "me": me, "endpoint": "/users/me"})
        except ZoomAPIError as e:
            self._json_response({"ok": False, "error": str(e), "status": e.status, "body": e.body[:500]}, status=502)

    def _handle_zoom_probe_meetings(self, parsed):
        from simulator.zoom_api_client import ZoomAPIError
        qs = parse_qs(parsed.query)
        meeting_type = (qs.get("type") or ["scheduled"])[0]
        client, err = self._zoom_client_from_request(parsed)
        if not client:
            self._json_response({"ok": False, "error": err}, status=400)
            return
        try:
            data = client.list_my_meetings(meeting_type=meeting_type)
            self._json_response({"ok": True, "type": meeting_type, "data": data})
        except ZoomAPIError as e:
            self._json_response({"ok": False, "error": str(e), "status": e.status, "body": e.body[:500]}, status=502)

    def _handle_zoom_probe_participants(self, parsed):
        from simulator.zoom_api_client import ZoomAPIError
        qs = parse_qs(parsed.query)
        meeting_id = (qs.get("id") or qs.get("meeting_id") or [""])[0]
        if not meeting_id:
            self._json_response({"ok": False, "error": "Missing ?id=<meeting_id>"}, status=400)
            return
        client, err = self._zoom_client_from_request(parsed)
        if not client:
            self._json_response({"ok": False, "error": err}, status=400)
            return
        try:
            data = client.get_past_meeting_participants(meeting_id)
            self._json_response({"ok": True, "meeting_id": meeting_id, "data": data})
        except ZoomAPIError as e:
            self._json_response({"ok": False, "error": str(e), "status": e.status, "body": e.body[:500]}, status=502)

    def _handle_export(self, parsed, state):
        """Build a single-shot SAGE evaluation-run export.

        Returns the entire run as a structured artifact so the Phase 4 paper's
        Analytical (Simulation) section can cite a concrete, reproducible
        file. Includes metadata, per-tick timeline, events, recommendations
        with evidence, professor responses, and the performance-metrics
        snapshot in one payload. Format = json (default).
        """
        if not state:
            self._json_response({"error": "No active session"}, status=404)
            return

        qs = parse_qs(parsed.query)
        fmt = (qs.get("format") or ["json"])[0].lower()
        if fmt not in ("json", "csv"):
            self._json_response({"error": f"Unsupported format '{fmt}'. Use json or csv."}, status=400)
            return

        # Snapshot under lock so we don't race with the live tick path that
        # appends to all_frames / events / recommendations / professor_actions.
        with state.lock:
            timeline_snap = list(state.all_frames or [])
            events_snap = list(state.events)
            recs_snap = list(state.recommendations)
            prof_snap = list(state.professor_actions)
            metrics_snap = _build_metrics_snapshot(state)
            metadata_snap = dict(state.metadata)
            students_snap = list(state.students)
            session_id = state.session_id
        timeline = timeline_snap
        # Inline CSV for the per-tick timeline so the paper can reference it
        # without requiring a separate download path.
        csv_rows = ["minute,observable_participation,active_speakers,speaking_gini,patterns"]
        for f in timeline:
            patterns = "|".join(p.get("type", "") for p in (f.get("patterns") or []))
            csv_rows.append(
                f"{f.get('minute', 0)},"
                f"{f.get('class_engagement', 0):.4f},"
                f"{f.get('active_speakers', 0)},"
                f"{f.get('speaking_gini', 0):.4f},"
                f"{patterns}"
            )
        timeline_csv = "\n".join(csv_rows)

        export = {
            "export_format_version": 1,
            "export_generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_id": session_id,
            "metadata": metadata_snap,
            "students": students_snap,
            "timeline": timeline,
            "events": events_snap,
            "recommendations": recs_snap,
            "professor_actions": prof_snap,
            "metrics": metrics_snap,
            "timeline_csv": timeline_csv,
        }

        if fmt == "csv":
            # CSV export = the timeline only; metadata header in comments.
            csv_text = (
                f"# SAGE evaluation-run export · session={session_id} · "
                f"university={metadata_snap.get('university', 'cgu')} · "
                f"scenario={metadata_snap.get('scenario', 'baseline')} · "
                f"seed={metadata_snap.get('seed', 42)}\n"
                f"{timeline_csv}\n"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f"attachment; filename=sage_run_{session_id}.csv")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(csv_text.encode("utf-8"))
            return

        body = json.dumps(export, default=str, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Disposition", f"attachment; filename=sage_run_{session_id}.json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _handle_sse(self, parsed):
        """Server-Sent Events endpoint."""
        session_id = _extract_session_id(parsed)
        state = _get_session(session_id, create=False)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Accel-Buffering", "no")  # Disable Nginx/reverse proxy buffering
        self.end_headers()

        if not state:
            self.wfile.write(b": no-session\n\n")
            self.wfile.flush()
            return

        client_queue = state.add_sse_client()

        # Send current state if session exists
        if state.session_id:
            init_msg = f"event: init\ndata: {json.dumps({'session_id': state.session_id, 'metadata': state.metadata, 'students': state.students, 'frames': state.all_frames}, default=str)}\n\n"
            self.wfile.write(init_msg.encode())
            self.wfile.flush()

        try:
            while True:
                try:
                    msg = client_queue.get(timeout=30)
                    self.wfile.write(msg.encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Send keepalive
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            state.remove_sse_client(client_queue)

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _serve_file(self, rel_path, content_type):
        base = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base, rel_path)
        if os.path.isfile(full_path):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"File not found: {rel_path}")

    def _guess_type(self, path):
        if path.endswith(".html"): return "text/html"
        if path.endswith(".js"): return "application/javascript"
        if path.endswith(".css"): return "text/css"
        if path.endswith(".json"): return "application/json"
        if path.endswith(".png"): return "image/png"
        if path.endswith(".svg"): return "image/svg+xml"
        return "application/octet-stream"

    def log_message(self, format, *args):
        """Suppress default logging for SSE keepalives."""
        first_arg = str(args[0]) if args else ""
        if "/api/stream" not in first_arg:
            super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description="SAGE v2 Live Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8080)))
    parser.add_argument("--host", type=str, default="0.0.0.0" if os.environ.get("PORT") else "localhost")
    parser.add_argument("--llm", action="store_true", help="Enable LLM-powered student chat and professor agent (requires GROQ_API_KEY)")
    args = parser.parse_args()

    # Store LLM flag globally so dashboard runs use it by default
    SAGEHandler.default_llm = args.llm

    server = ThreadingHTTPServer((args.host, args.port), SAGEHandler)
    llm_status = "✅ LLM mode (Groq)" if args.llm else "⚡ Template mode (no LLM)"
    print(f"\n  SAGE v2 Server running at http://{args.host}:{args.port}")
    print(f"  Dashboard:  http://{args.host}:{args.port}/")
    print(f"  Mode:       {llm_status}")
    print(f"  API:        http://{args.host}:{args.port}/api/presets")
    print(f"  SSE Stream: http://{args.host}:{args.port}/api/stream")
    print(f"\n  Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
