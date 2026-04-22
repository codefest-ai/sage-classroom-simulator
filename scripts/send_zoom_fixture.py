#!/usr/bin/env python3
"""Send a signed synthetic Zoom webhook sequence to a local or hosted SAGE deployment.

Usage:
    python3 scripts/send_zoom_fixture.py http://localhost:8096
    python3 scripts/send_zoom_fixture.py https://your-app.onrender.com --secret "$ZOOM_WEBHOOK_SECRET"

This is for deployment/debug verification only. It does not replace a real Zoom meeting.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.request


FIXTURE_PARTICIPANTS = [
    {"user_id": "fixture-student-1", "user_name": "Alex Fixture", "email": "alex@example.com"},
    {"user_id": "fixture-student-2", "user_name": "Jordan Fixture", "email": "jordan@example.com"},
]


def build_signature(secret: str, body: bytes, timestamp: str) -> str:
    if not secret:
        return ""
    message = f"v0:{timestamp}:{body.decode('utf-8')}"
    return "v0=" + hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def post_json(base_url: str, path: str, payload: dict, secret: str = ""):
    body = json.dumps(payload).encode("utf-8")
    timestamp = str(int(time.time()))
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if secret:
        headers["x-zm-request-timestamp"] = timestamp
        headers["x-zm-signature"] = build_signature(secret, body, timestamp)

    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return exc.code, payload


def fetch_json(base_url: str, path: str):
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return exc.code, payload


def zoom_event(event_name: str, meeting_id: str, **object_fields):
    payload_object = {"id": meeting_id, **object_fields}
    return {"event": event_name, "payload": {"object": payload_object}}


def fixture_sequence(meeting_id: str, rich: bool):
    events = [
        zoom_event("meeting.started", meeting_id),
        zoom_event("meeting.participant_joined", meeting_id, participant=FIXTURE_PARTICIPANTS[0]),
        zoom_event("meeting.participant_joined", meeting_id, participant=FIXTURE_PARTICIPANTS[1]),
    ]
    if rich:
        events.extend([
            zoom_event(
                "meeting.chat_message_sent",
                meeting_id,
                sender=FIXTURE_PARTICIPANTS[0],
                message="Could you clarify the distinction between simulation and live deployment?",
            ),
            zoom_event(
                "meeting.participant_raised_hand",
                meeting_id,
                participant={**FIXTURE_PARTICIPANTS[1], "reaction": "raised_hand"},
            ),
            zoom_event(
                "meeting.reaction_received",
                meeting_id,
                participant={**FIXTURE_PARTICIPANTS[0], "reaction": "thumbs_up"},
            ),
        ])
    return events


def main():
    parser = argparse.ArgumentParser(description="Send synthetic Zoom webhook events to a SAGE deployment.")
    parser.add_argument("base_url", help="Deployment base URL, e.g. http://localhost:8096 or https://your-app.onrender.com")
    parser.add_argument("--secret", default="", help="Zoom webhook secret used for signing requests")
    parser.add_argument("--meeting-id", default="fixture-meeting-505", help="Meeting id to reuse for the synthetic sequence")
    parser.add_argument(
        "--mode",
        choices=("presence", "rich"),
        default="rich",
        help="Presence sends started/joined only. Rich also sends chat, hand raise, and reaction events.",
    )
    args = parser.parse_args()

    print(f"Sending synthetic Zoom fixture to: {args.base_url.rstrip('/')}")
    print(f"Meeting id: {args.meeting_id}")
    print(f"Mode: {args.mode}")
    print(f"Signed requests: {'yes' if args.secret else 'no'}")

    ok = True
    for idx, payload in enumerate(fixture_sequence(args.meeting_id, rich=args.mode == "rich"), start=1):
        status, response = post_json(args.base_url, "/api/zoom/webhook", payload, secret=args.secret)
        print(f"\n[{idx}] {payload['event']} -> status {status}")
        print(json.dumps(response, indent=2, sort_keys=True))
        if not (200 <= status < 300):
            ok = False

    debug_status, debug = fetch_json(args.base_url, "/api/zoom/debug")
    state_status, state = fetch_json(args.base_url, "/api/zoom/state")

    print(f"\n[debug] status {debug_status}")
    print(json.dumps(debug, indent=2, sort_keys=True))
    print(f"\n[state] status {state_status}")
    print(json.dumps(state, indent=2, sort_keys=True))

    if not (200 <= debug_status < 300):
        print(f"[fail] /api/zoom/debug returned {debug_status}", file=sys.stderr)
        ok = False
    if not (200 <= state_status < 300):
        print(f"[fail] /api/zoom/state returned {state_status}", file=sys.stderr)
        ok = False

    participant_count = 0
    if isinstance(state, dict):
        participant_count = len(state.get("students") or [])
        if state.get("active") is False:
            print("[fail] /api/zoom/state reports no active meeting after fixture ingestion", file=sys.stderr)
            ok = False
    if participant_count < 2:
        print(f"[fail] expected at least 2 fixture participants in state, saw {participant_count}", file=sys.stderr)
        ok = False

    if args.mode == "rich" and isinstance(debug, dict):
        live_debug = debug.get("live_debug") or {}
        if live_debug.get("signal_status") != "rich":
            print(
                f"[fail] rich fixture expected signal_status=rich, saw {live_debug.get('signal_status')!r}",
                file=sys.stderr,
            )
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
