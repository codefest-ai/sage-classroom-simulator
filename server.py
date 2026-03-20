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
from http.server import HTTPServer, SimpleHTTPRequestHandler
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
        self.professor_actions = []
        self.metadata = {}
        self.students = []
        self.sse_queues = []  # List of queue.Queue for SSE clients
        self.lock = threading.Lock()

    def reset(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.is_running = False
        self.current_minute = 0
        self.current_frame = None
        self.all_frames = []
        self.events = []
        self.recommendations = []
        self.professor_actions = []
        self.metadata = {}
        self.students = []

    def add_sse_client(self):
        q = queue.Queue()
        self.sse_queues.append(q)
        return q

    def remove_sse_client(self, q):
        if q in self.sse_queues:
            self.sse_queues.remove(q)

    def broadcast(self, event_type, data):
        msg = f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"
        dead = []
        for q in self.sse_queues:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            self.sse_queues.remove(q)


STATE = SessionState()
ZOOM = ZoomWebhookHandler(secret_token=os.environ.get("ZOOM_WEBHOOK_SECRET", ""))


# ============================================================
# SIMULATION RUNNER (background thread)
# ============================================================

def run_simulation_live(state, config):
    """Run simulation tick-by-tick, broadcasting each frame via SSE."""
    state.reset()
    state.is_running = True

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
            state.current_minute = frame["minute"]
            state.current_frame = frame
            state.all_frames.append(frame)

            # Collect events for this minute
            minute_events = [e for e in engine.events if hasattr(e, 'minute') and e.minute == frame["minute"]]
            # Also store serialized events in state
            for e in minute_events:
                state.events.append({"minute": e.minute, "event_type": e.event_type, "student_id": e.student_id, "data": e.data})

            # Get recommendations
            recs = engine.scorer.get_recommendations(engine._last_class_snapshot) if hasattr(engine, '_last_class_snapshot') and engine._last_class_snapshot else []
            for r in recs:
                r["minute"] = frame["minute"]
                state.recommendations.append(r)

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
                            prof_action = {
                                "minute": actions[0].minute,
                                "response_category": actions[0].response_category,
                                "intervention_type": actions[0].intervention_type,
                                "rationale": actions[0].rationale,
                                "spoken_text": None,
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

        if path == "/" or path == "/index.html":
            # Serve dashboard
            self._serve_file("dashboard/index.html", "text/html")

        elif path == "/api/stream":
            self._handle_sse()

        elif path == "/api/state":
            self._json_response(_build_dashboard_state(STATE))

        elif path == "/api/dashboard-state":
            self._json_response(_build_dashboard_state(STATE))

        elif path == "/api/session":
            self._json_response({
                "session_id": STATE.session_id,
                "is_running": STATE.is_running,
                "current_minute": STATE.current_minute,
                "metadata": STATE.metadata,
                "students": STATE.students,
            })

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
                "timeline": STATE.all_frames,
                "events": STATE.events,
                "recommendations": STATE.recommendations,
                "professor_actions": STATE.professor_actions,
            })

        elif path == "/api/zoom/state":
            # Live Zoom meeting state as dashboard frame
            meeting = ZOOM.get_active_meeting()
            if meeting:
                self._json_response(meeting.to_dashboard_frame())
            else:
                self._json_response({"error": "No active Zoom meeting"}, status=404)

        elif path == "/api/zoom/history":
            meeting = ZOOM.get_active_meeting()
            if meeting:
                self._json_response(ZOOM.get_meeting_history(meeting.meeting_id))
            else:
                self._json_response({"error": "No active Zoom meeting"}, status=404)

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
            STATE.is_running = False
            self._json_response({"status": "stopped"})

        elif path == "/api/intervention":
            self._handle_intervention(data)

        elif path == "/api/zoom/webhook":
            # Zoom sends webhook events here
            result = ZOOM.handle_event(data)
            if result:
                self._json_response(result)
            else:
                self._json_response({"status": "ok"})

        else:
            self.send_error(404, "Not found")

    def _handle_start(self, config):
        """Start a new simulation in a background thread."""
        if STATE.is_running:
            self._json_response({"error": "Simulation already running"}, status=409)
            return

        thread = threading.Thread(
            target=run_simulation_live,
            args=(STATE, config),
            daemon=True,
        )
        thread.start()

        # Wait briefly for session_id to be set
        time.sleep(0.1)

        self._json_response({
            "status": "started",
            "session_id": STATE.session_id,
            "config": config,
        })

    def _handle_intervention(self, data):
        """Inject an intervention mid-simulation."""
        if not STATE.is_running or not STATE.engine:
            self._json_response({"error": "No active simulation"}, status=400)
            return

        itype = data.get("type", "poll")
        target = data.get("target_student")
        minute = STATE.current_minute + 1

        STATE.engine.add_intervention(minute, itype, target)
        self._json_response({
            "status": "intervention_scheduled",
            "minute": minute,
            "type": itype,
        })

    def _handle_sse(self):
        """Server-Sent Events endpoint."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Accel-Buffering", "no")  # Disable Nginx/reverse proxy buffering
        self.end_headers()

        client_queue = STATE.add_sse_client()

        # Send current state if session exists
        if STATE.session_id:
            init_msg = f"event: init\ndata: {json.dumps({'session_id': STATE.session_id, 'metadata': STATE.metadata, 'students': STATE.students, 'frames': STATE.all_frames}, default=str)}\n\n"
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
            STATE.remove_sse_client(client_queue)

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
        if "/api/stream" not in (args[0] if args else ""):
            super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description="SAGE v2 Live Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8080)))
    parser.add_argument("--host", type=str, default="0.0.0.0" if os.environ.get("PORT") else "localhost")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), SAGEHandler)
    print(f"\n  SAGE v2 Server running at http://{args.host}:{args.port}")
    print(f"  Dashboard:  http://{args.host}:{args.port}/")
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
