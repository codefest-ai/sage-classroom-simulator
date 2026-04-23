#!/usr/bin/env python3
"""Smoke-check a hosted or local Zoom live deployment.

Usage:
    python3 scripts/check_zoom_live.py https://your-app.onrender.com
    python3 scripts/check_zoom_live.py http://localhost:8080
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


def fetch_json(base_url: str, path: str):
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}
        return exc.code, payload
    except Exception as exc:  # pragma: no cover - smoke script
        return None, {"error": str(exc)}


def print_section(title: str, status, payload):
    marker = "OK" if isinstance(status, int) and 200 <= status < 300 else "WARN"
    print(f"\n[{marker}] {title}")
    print(f"status: {status}")
    print(json.dumps(payload, indent=2, sort_keys=True))


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check_zoom_live.py <base-url>", file=sys.stderr)
        return 1

    base_url = sys.argv[1].rstrip("/")
    print(f"Checking Zoom live deployment at: {base_url}")

    health_status, health = fetch_json(base_url, "/api/health")
    print_section("Service health", health_status, health)

    debug_status, debug = fetch_json(base_url, "/api/zoom/debug")
    print_section("Zoom debug", debug_status, debug)

    state_status, state = fetch_json(base_url, "/api/zoom/state")
    print_section("Live state", state_status, state)

    history_status, history = fetch_json(base_url, "/api/zoom/history")
    print_section("Live history", history_status, history)

    if isinstance(debug, dict):
        live_debug = debug.get("live_debug") or {}
        signal_status = live_debug.get("signal_status")
        webhook_configured = debug.get("webhook_configured")
        print("\nSummary:")
        print(f"- webhook secret configured: {webhook_configured}")
        print(f"- signal status: {signal_status or 'unknown'}")
        print(f"- active meeting: {debug.get('active_meeting_id') or 'none'}")
        recent = live_debug.get("recent_raw_event_types") or []
        print(f"- recent raw events: {', '.join(recent) if recent else 'none yet'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
