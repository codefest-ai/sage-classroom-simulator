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

        with state.lock:
            state.touch()
            state.current_minute = frame["minute"]
            state.current_frame = frame
            state.all_frames.append(frame)

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
            for idx, r in enumerate(raw_recs):
                pattern_type = (r.get("evidence") or {}).get("type") or r.get("action") or "unknown"
                last_minute = state.recent_rec_minutes.get(pattern_type, -10**9)
                if frame["minute"] - last_minute < REC_COOLDOWN_MINUTES:
                    continue
                state.recent_rec_minutes[pattern_type] = frame["minute"]
                r["rec_id"] = r.get("rec_id") or f"{frame['minute']}-{len(state.recommendations) + idx}"
                r["minute"] = frame["minute"]
                r["pattern_type"] = pattern_type
                state.recommendations.append(r)
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
