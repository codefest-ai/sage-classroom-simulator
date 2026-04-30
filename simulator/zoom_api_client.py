"""
Zoom REST API client — local development tool.

Lets a developer test the Zoom integration end-to-end from a laptop without
needing the public webhook + Render secret to be live. Accepts either an
OAuth access token (account-level) or a JWT (legacy app type) from
environment or per-request, and exposes a thin wrapper around the Zoom v2
endpoints the IDSS would use in a richer integration.

Scope: read-only probes (list user info, list meetings, fetch participants
of a past meeting). NOT used for production webhook handling — the live
production path is `simulator/zoom_adapter.py`.

Env:
    ZOOM_API_TOKEN   — preferred. Server-to-server OAuth access token, or
                       a JWT, or any bearer accepted by the Zoom REST API.
    ZOOM_API_BASE    — override base URL (default: https://api.zoom.us/v2)

Usage (Python):
    from simulator.zoom_api_client import ZoomAPIClient
    c = ZoomAPIClient.from_env()
    me = c.get_me()
    meetings = c.list_my_meetings(meeting_type="scheduled")
    parts = c.get_past_meeting_participants(meeting_id)

Usage (server endpoint):
    ENABLE_ZOOM_API_PROBE=1 must be set on the local dev server first.

    GET /api/zoom/probe                       — quick health check (uses env token)
    GET /api/zoom/probe?token=<bearer>        — explicit per-request token
    GET /api/zoom/probe/meetings              — list user's meetings
    GET /api/zoom/probe/participants?id=<m>   — list past-meeting participants

Do not enable the probe endpoints on a public demo/deployment host.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


DEFAULT_BASE = "https://api.zoom.us/v2"


class ZoomAPIError(Exception):
    """Raised when the Zoom API returns a non-2xx response or transport fails."""

    def __init__(self, status: int, body: str, message: str = ""):
        self.status = status
        self.body = body
        super().__init__(message or f"Zoom API error {status}: {body[:200]}")


class ZoomAPIClient:
    def __init__(self, token: str, base_url: str = DEFAULT_BASE, timeout: float = 10.0):
        if not token:
            raise ValueError("ZoomAPIClient requires a bearer token (OAuth access token or JWT).")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "ZoomAPIClient":
        token = os.environ.get("ZOOM_API_TOKEN", "").strip()
        base = os.environ.get("ZOOM_API_BASE", DEFAULT_BASE)
        return cls(token=token, base_url=base)

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None,
                 body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = resp.read().decode("utf-8") or "{}"
                return json.loads(payload)
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8")
            except Exception:
                pass
            raise ZoomAPIError(e.code, body_text)
        except urllib.error.URLError as e:
            raise ZoomAPIError(0, str(e), message=f"Network error contacting Zoom API: {e}")

    # --- Convenience wrappers ---

    def get_me(self) -> Dict[str, Any]:
        """GET /users/me — confirms the token is valid and returns the host profile."""
        return self._request("GET", "/users/me")

    def list_my_meetings(self, meeting_type: str = "scheduled",
                         page_size: int = 30) -> Dict[str, Any]:
        """GET /users/me/meetings — list meetings the token's user can see.

        meeting_type: "scheduled", "live", "upcoming", "previous_meetings"
        """
        return self._request(
            "GET",
            "/users/me/meetings",
            params={"type": meeting_type, "page_size": page_size},
        )

    def get_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """GET /meetings/{meetingId} — single-meeting details."""
        return self._request("GET", f"/meetings/{urllib.parse.quote(str(meeting_id))}")

    def get_past_meeting_participants(self, meeting_id: str,
                                      page_size: int = 100) -> Dict[str, Any]:
        """GET /past_meetings/{meetingId}/participants — historical participant list.

        Useful for backfilling SAGE with a recently-ended meeting's roster.
        """
        return self._request(
            "GET",
            f"/past_meetings/{urllib.parse.quote(str(meeting_id))}/participants",
            params={"page_size": page_size},
        )
