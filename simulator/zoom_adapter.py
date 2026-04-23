"""
Zoom Webhook Adapter — Translates live Zoom meeting events into SAGE dashboard frames.

Receives Zoom webhook events (participant join/leave, chat, reactions)
and maps them to the same signal format the IDSS dashboard consumes.

The dashboard doesn't know if data comes from simulation or Zoom — same interface.

Setup:
1. Create a Zoom App at marketplace.zoom.us (Webhook Only type)
2. Set Event Notification URL to: https://your-server.onrender.com/api/zoom/webhook
3. Subscribe to: meeting.started, meeting.ended, meeting.participant_joined,
   meeting.participant_left, meeting.chat_message_sent,
   meeting.participant_raised_hand, meeting.participant_lowered_hand,
   meeting.reaction_received
4. Copy the Secret Token for verification
"""

import hashlib
import hmac
import json
import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass


SEVERITY_ORDER = {
    "mild": 0,
    "moderate": 1,
    "severe": 2,
}


@dataclass
class ZoomParticipant:
    """Tracks a single Zoom participant's state."""
    user_id: str
    name: str
    email: str = ""
    joined_at: float = 0
    left_at: float = 0
    is_present: bool = True
    chat_count: int = 0
    reaction_count: int = 0
    hand_raised: bool = False
    camera_on: bool = True  # Zoom doesn't always expose this via webhook
    last_chat_minute: int = 0
    last_active_minute: int = 0


class ZoomMeetingState:
    """Tracks live state of a Zoom meeting mapped to SAGE dashboard format."""

    def __init__(self, meeting_id: str):
        self.meeting_id = meeting_id
        self.started_at: float = time.time()
        self.participants: Dict[str, ZoomParticipant] = {}
        self.chat_messages: List[Dict] = []
        self.reactions: List[Dict] = []
        self.events: List[Dict] = []
        self.event_counts: Dict[str, int] = {}
        self.event_trace: List[Dict] = []
        self.timeline: List[Dict] = []
        self.recommendations: List[Dict] = []
        self.professor_actions: List[Dict] = []
        self._last_recommendation_by_pattern: Dict[str, Dict] = {}
        self.last_event_at: float = 0
        self.last_raw_event_type: str = ""
        self.is_active: bool = True

    @property
    def elapsed_minutes(self) -> int:
        return max(1, int((time.time() - self.started_at) / 60))

    def participant_joined(self, user_id: str, name: str, email: str = ""):
        minute = self.elapsed_minutes
        if user_id not in self.participants:
            self.participants[user_id] = ZoomParticipant(
                user_id=user_id, name=name, email=email,
                joined_at=time.time(),
            )
        else:
            self.participants[user_id].is_present = True
            self.participants[user_id].left_at = 0
        # Presence is not observable participation. last_active_minute only ticks
        # on actual signals (chat, reaction, hand) so a fresh joiner does not
        # score as engaged before any observable activity has occurred.
        self._record_event("join", user_id=user_id, name=name, data={"name": name}, raw_event_type="meeting.participant_joined")

    def participant_left(self, user_id: str):
        if user_id in self.participants:
            self.participants[user_id].is_present = False
            self.participants[user_id].left_at = time.time()
            name = self.participants[user_id].name
        else:
            name = ""
        self._record_event("leave", user_id=user_id, name=name, data={}, raw_event_type="meeting.participant_left")

    def chat_received(self, user_id: str, name: str, text: str):
        minute = self.elapsed_minutes
        self.chat_messages.append({
            "minute": minute,
            "student_id": user_id,
            "name": name,
            "text": text,
        })
        if user_id in self.participants:
            self.participants[user_id].chat_count += 1
            self.participants[user_id].last_chat_minute = minute
            self.participants[user_id].last_active_minute = minute
        self._record_event("chat", user_id=user_id, name=name, data={"text": text}, raw_event_type="meeting.chat_message_sent")

    def reaction_received(self, user_id: str, reaction_type: str):
        minute = self.elapsed_minutes
        normalized = self._normalize_reaction_type(reaction_type)
        self.reactions.append({
            "minute": minute,
            "student_id": user_id,
            "type": normalized,
        })
        if user_id in self.participants:
            self.participants[user_id].last_active_minute = minute
            if normalized == "raised_hand":
                self.participants[user_id].hand_raised = True
            else:
                self.participants[user_id].reaction_count += 1
            name = self.participants[user_id].name
        else:
            name = ""
        if normalized == "raised_hand":
            self._record_event("hand_raise", user_id=user_id, name=name, data={"type": normalized}, raw_event_type="meeting.participant_raised_hand")
        else:
            self._record_event("reaction", user_id=user_id, name=name, data={"type": normalized}, raw_event_type="meeting.reaction_received")

    def hand_lowered(self, user_id: str):
        if user_id in self.participants:
            self.participants[user_id].hand_raised = False
            self.participants[user_id].last_active_minute = self.elapsed_minutes
            name = self.participants[user_id].name
        else:
            name = ""
        self._record_event("hand_lower", user_id=user_id, name=name, data={"type": "lowered_hand"}, raw_event_type="meeting.participant_lowered_hand")

    def record_meeting_started(self):
        self.is_active = True
        self._record_event("meeting_started", data={}, raw_event_type="meeting.started")

    def record_meeting_ended(self):
        self._record_event("meeting_ended", data={}, raw_event_type="meeting.ended")
        self.is_active = False

    def _normalize_reaction_type(self, reaction_type: str) -> str:
        raw = str(reaction_type or "").strip().lower().replace(" ", "_")
        if raw in {"raised_hand", "participant_raised_hand", "raise_hand"}:
            return "raised_hand"
        if raw in {"lowered_hand", "participant_lowered_hand", "lower_hand"}:
            return "lowered_hand"
        return raw or "reaction"

    def _record_event(
        self,
        event_type: str,
        user_id: str = "",
        name: str = "",
        data: Optional[Dict] = None,
        raw_event_type: str = "",
    ):
        minute = self.elapsed_minutes
        payload = data or {}
        event = {
            "minute": minute,
            "event_type": event_type,
            "student_id": user_id,
            "data": payload,
        }
        self.events.append(event)
        trace = {
            "minute": minute,
            "event_type": event_type,
            "raw_event_type": raw_event_type or event_type,
            "student_id": user_id,
            "name": name,
            "data": payload,
        }
        self.event_trace.append(trace)
        self.event_trace = self.event_trace[-40:]
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
        self.last_event_at = time.time()
        self.last_raw_event_type = raw_event_type or event_type

    def build_observability_snapshot(self) -> Dict:
        present = [p for p in self.participants.values() if p.is_present]
        supported_signal_types = ["presence", "chat", "hand", "reaction"]
        signal_counts = {
            "presence": self.event_counts.get("join", 0) + self.event_counts.get("leave", 0),
            "chat": self.event_counts.get("chat", 0),
            "hand": self.event_counts.get("hand_raise", 0) + self.event_counts.get("hand_lower", 0),
            "reaction": self.event_counts.get("reaction", 0),
        }
        signal_coverage = {key: value > 0 for key, value in signal_counts.items()}
        received_signal_types = [key for key in supported_signal_types if signal_coverage.get(key)]
        rich_signal_types = [key for key in ("chat", "hand", "reaction") if signal_coverage.get(key)]
        recent_events = [dict(event) for event in self.event_trace[-12:]]
        recent_raw_event_types = list(dict.fromkeys(
            event.get("raw_event_type")
            for event in reversed(recent_events)
            if event.get("raw_event_type")
        ))
        if rich_signal_types:
            signal_status = "rich"
            signal_status_reason = "Chat, hand, or reaction signals are reaching the live pipeline."
        elif signal_coverage["presence"]:
            signal_status = "presence_only"
            signal_status_reason = "Only join/leave presence events have reached the live pipeline so far."
        else:
            signal_status = "waiting"
            signal_status_reason = "No Zoom meeting events have reached the server yet."

        return {
            "meeting_id": self.meeting_id,
            "active": self.is_active,
            "participant_count": len(present),
            "signal_status": signal_status,
            "signal_status_reason": signal_status_reason,
            "supported_signal_types": supported_signal_types,
            "received_signal_types": received_signal_types,
            "signal_counts": signal_counts,
            "signal_coverage": signal_coverage,
            "rich_signal_types": rich_signal_types,
            "event_counts": dict(self.event_counts),
            "last_event_at": int(self.last_event_at) if self.last_event_at else 0,
            "last_raw_event_type": self.last_raw_event_type or None,
            "recent_raw_event_types": recent_raw_event_types,
            "recent_events": recent_events,
        }

    def to_dashboard_frame(self) -> Dict:
        """Convert current Zoom state to SAGE dashboard frame format."""
        minute = self.elapsed_minutes
        present = [p for p in self.participants.values() if p.is_present]
        total = len(present)

        if total == 0:
            return {
                "minute": minute,
                "class_engagement": 0.0,
                "engagement_std": 0,
                "speaking_gini": 0,
                "active_speakers": 0,
                "patterns": [],
                "students": [],
                "participant_count": 0,
                "source": "zoom_live",
                "recommendation_mode": "limited_live_heuristic",
                "live_debug": self.build_observability_snapshot(),
            }

        # Observable-participation heuristics from Zoom signals
        students = []
        engagement_sum = 0
        active_speakers = 0
        chat_counts = []
        signal_count = 0
        presence_only_count = 0

        for p in present:
            has_observable_signal = (
                p.chat_count > 0
                or p.reaction_count > 0
                or p.hand_raised
                or p.last_active_minute > 0
            )

            if not has_observable_signal:
                # Presence is not engagement. Render explicitly as "no observable
                # signal yet" rather than scoring presence as participation.
                presence_only_count += 1
                students.append({
                    "student_id": p.user_id,
                    "name": p.name,
                    "engagement": 0.0,
                    "state": "no_signal",
                    "is_confused": False,
                    "signals": {
                        "chat_count": 0,
                        "reaction_count": 0,
                        "hand_raised": False,
                        "minutes_since_active": None,
                        "presence_only": True,
                    },
                })
                chat_counts.append(0)
                continue

            minutes_since_active = minute - p.last_active_minute if p.last_active_minute > 0 else minute
            minutes_since_chat = minute - p.last_chat_minute if p.last_chat_minute > 0 else minute

            # Limited observable-participation heuristic from Zoom signals.
            # Camera state is intentionally not scored: camera-off can reflect
            # privacy, bandwidth, culture, disability, or access constraints.
            eng = 0.5  # baseline once at least one observable signal has fired
            if minutes_since_active <= 2:
                eng += 0.3  # recently active
            elif minutes_since_active <= 5:
                eng += 0.15
            if p.chat_count > 0:
                eng += min(0.2, p.chat_count * 0.05)
            if p.reaction_count > 0:
                eng += min(0.12, p.reaction_count * 0.04)
            if p.hand_raised:
                eng += 0.1
            eng = max(0.05, min(1.0, eng))

            # State classification
            if eng >= 0.65:
                state = "engaged"
            elif eng >= 0.4:
                state = "drifting"
            else:
                state = "disengaged"

            students.append({
                "student_id": p.user_id,
                "name": p.name,
                "engagement": eng,
                "state": state,
                "is_confused": False,  # Can't detect from Zoom alone
                "signals": {
                    "chat_count": p.chat_count,
                    "reaction_count": p.reaction_count,
                    "hand_raised": p.hand_raised,
                    "minutes_since_active": minutes_since_active,
                    "presence_only": False,
                },
            })

            engagement_sum += eng
            chat_counts.append(p.chat_count)
            signal_count += 1
            if minutes_since_active <= 1:
                active_speakers += 1

        class_engagement = (engagement_sum / signal_count) if signal_count > 0 else 0.0

        if total < 2 or signal_count == 0:
            return {
                "minute": minute,
                "class_engagement": 0.0,
                "engagement_std": 0,
                "speaking_gini": 0,
                "active_speakers": active_speakers,
                "patterns": [],
                "students": students,
                "participant_count": total,
                "participants_with_signal": signal_count,
                "presence_only_count": presence_only_count,
                "source": "zoom_live",
                "recommendation_mode": "limited_live_heuristic",
                "insufficient_signal": True,
                "insufficient_signal_reason": (
                    "All participants are presence-only — no chat, hand, or reaction signals yet."
                    if signal_count == 0 and total >= 1
                    else "Need at least 2 participants for stable live observable-participation estimates."
                ),
                "live_debug": self.build_observability_snapshot(),
            }

        # Speaking equity (Gini on chat counts)
        gini = 0
        if chat_counts and sum(chat_counts) > 0:
            sorted_counts = sorted(chat_counts)
            n = len(sorted_counts)
            cumulative = sum((i + 1) * c for i, c in enumerate(sorted_counts))
            gini = (2 * cumulative) / (n * sum(sorted_counts)) - (n + 1) / n if n > 0 else 0
            gini = max(0, min(1, gini))

        # Pattern detection
        patterns = []
        if class_engagement < 0.4:
            patterns.append({"type": "energy_decay", "severity": "moderate",
                           "message": f"Live observable participation at {class_engagement:.0%}", "value": class_engagement})
        if gini > 0.5 and sum(chat_counts) > 5:
            patterns.append({"type": "equity_imbalance", "severity": "moderate",
                           "message": f"Discussion dominated by few voices (Gini={gini:.2f})", "value": gini})
        silent = sum(1 for s in students if s["state"] == "disengaged")
        silent_ratio = (silent / len(students)) if students else 0
        if silent >= len(students) * 0.4:
            patterns.append({"type": "silent_majority", "severity": "moderate",
                           "message": f"{silent} participants show low observable activity", "value": round(silent_ratio, 3), "count": silent})

        return {
            "minute": minute,
            "class_engagement": class_engagement,
            "engagement_std": 0,
            "speaking_gini": gini,
            "active_speakers": active_speakers,
            "patterns": patterns,
            "students": students,
            "participant_count": total,
            "participants_with_signal": signal_count,
            "presence_only_count": presence_only_count,
            "source": "zoom_live",
            "recommendation_mode": "limited_live_heuristic",
            "insufficient_signal": False,
            "live_debug": self.build_observability_snapshot(),
        }

    def refresh_live_state(self) -> Dict:
        """Build the current frame and update live artifact history."""
        frame = self.to_dashboard_frame()
        frame_copy = dict(frame)
        frame_copy["patterns"] = [dict(p) for p in frame.get("patterns", [])]
        frame_copy["students"] = [dict(s) for s in frame.get("students", [])]
        live_debug = frame.get("live_debug", {}) or {}
        frame_copy["live_debug"] = {
            **live_debug,
            "supported_signal_types": list(live_debug.get("supported_signal_types", []) or []),
            "received_signal_types": list(live_debug.get("received_signal_types", []) or []),
            "signal_counts": dict(live_debug.get("signal_counts", {}) or {}),
            "signal_coverage": dict(live_debug.get("signal_coverage", {}) or {}),
            "event_counts": dict(live_debug.get("event_counts", {}) or {}),
            "rich_signal_types": list(live_debug.get("rich_signal_types", []) or []),
            "recent_raw_event_types": list(live_debug.get("recent_raw_event_types", []) or []),
            "recent_events": [dict(event) for event in (live_debug.get("recent_events", []) or [])],
        }

        if self.timeline and self.timeline[-1]["minute"] == frame_copy["minute"]:
            self.timeline[-1] = frame_copy
        else:
            self.timeline.append(frame_copy)

        self._update_recommendations(frame_copy)
        return frame_copy

    def _update_recommendations(self, frame: Dict):
        """Generate throttled live recommendations from current webhook-derived patterns."""
        patterns = frame.get("patterns", [])
        if not patterns:
            return

        recs = self._build_live_recommendations(frame, patterns)

        for rec in recs:
            evidence = rec.get("evidence", {}) or {}
            pattern_type = evidence.get("type") or rec.get("action") or "pattern"
            severity = evidence.get("severity", "mild")
            last = self._last_recommendation_by_pattern.get(pattern_type)
            should_emit = (
                last is None
                or frame["minute"] - last["minute"] >= 3
                or SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER.get(last.get("severity"), 0)
            )
            if not should_emit:
                continue

            live_rec = dict(rec)
            live_rec["minute"] = frame["minute"]
            live_rec["rec_id"] = f"zoom-{self.meeting_id}-{frame['minute']}-{len(self.recommendations) + 1}"
            live_rec["source"] = "zoom_live"
            live_rec["mode"] = "limited_live_heuristic"
            self.recommendations.append(live_rec)
            self._last_recommendation_by_pattern[pattern_type] = {
                "minute": frame["minute"],
                "severity": severity,
            }

    def _build_live_recommendations(self, frame: Dict, patterns: List[Dict]) -> List[Dict]:
        """Map Zoom-derived live patterns into the artifact's recommendation space."""
        recommendations: List[Dict] = []
        class_engagement = frame.get("class_engagement", 0.0)

        for pattern in patterns:
            ptype = pattern.get("type")
            severity = pattern.get("severity", "moderate")

            if ptype == "energy_decay":
                if class_engagement < 0.25:
                    recommendations.append({
                        "priority": "high",
                        "action": "breakout",
                        "message": f"Live observable participation is low ({class_engagement:.0%}). Consider a low-stakes activity shift; use instructor judgment before choosing breakout rooms.",
                        "evidence": pattern,
                    })
                else:
                    recommendations.append({
                        "priority": "medium",
                        "action": "poll",
                        "message": f"Live observable participation is trending low ({class_engagement:.0%}). A quick poll or discussion prompt could help check the room.",
                        "evidence": pattern,
                    })

            elif ptype == "equity_imbalance":
                recommendations.append({
                    "priority": "high" if severity == "severe" else "medium",
                    "action": "equity_intervention",
                    "message": f"Live participation appears concentrated in a few voices (Gini={pattern.get('value', 0):.2f}). Consider think-pair-share or inviting quieter students in.",
                    "evidence": pattern,
                })

            elif ptype == "silent_majority":
                silent_ratio = pattern.get("value", 0)
                silent_count = pattern.get("count")
                count_text = f"{silent_count} students" if silent_count is not None else f"{silent_ratio:.0%} of the class"
                recommendations.append({
                    "priority": "medium",
                    "action": "activation",
                    "message": f"{count_text} show low observable activity in the live feed. Try a poll, chat prompt, or reflective pause before assuming disengagement.",
                    "evidence": pattern,
                })

        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.get("priority"), 3))
        return recommendations


class ZoomWebhookHandler:
    """Processes incoming Zoom webhook events."""

    def __init__(self, secret_token: str = ""):
        self.secret_token = secret_token
        self.meetings: Dict[str, ZoomMeetingState] = {}
        self._lock = threading.RLock()

    def verify_webhook(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """Verify Zoom webhook signature."""
        if not self.secret_token:
            return True  # Skip verification if no token configured
        message = f"v0:{timestamp}:{payload.decode()}"
        expected = "v0=" + hmac.new(
            self.secret_token.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def handle_event(self, event: Dict) -> Optional[Dict]:
        """Process a Zoom webhook event, return dashboard update if applicable."""
        event_type = event.get("event", "")
        payload = event.get("payload", {}).get("object", {})

        # Handle validation challenge (Zoom sends this on app setup)
        if event_type == "endpoint.url_validation":
            plain_token = event.get("payload", {}).get("plainToken", "")
            encrypted = hmac.new(
                self.secret_token.encode(), plain_token.encode(), hashlib.sha256
            ).hexdigest()
            return {"plainToken": plain_token, "encryptedToken": encrypted}

        meeting_id = str(payload.get("id", ""))
        if not meeting_id:
            return None

        with self._lock:
            if event_type == "meeting.started":
                meeting = self.meetings.get(meeting_id)
                if meeting:
                    meeting.is_active = True
                    if not meeting.started_at:
                        meeting.started_at = time.time()
                else:
                    self.meetings[meeting_id] = ZoomMeetingState(meeting_id)
                    meeting = self.meetings[meeting_id]
                meeting.record_meeting_started()
                return {"status": "meeting_started", "meeting_id": meeting_id}

            if event_type == "meeting.ended":
                if meeting_id in self.meetings:
                    self.meetings[meeting_id].record_meeting_ended()
                return {"status": "meeting_ended", "meeting_id": meeting_id}

            meeting = self.meetings.get(meeting_id)
            if not meeting:
                # Meeting started before server — create retroactively
                meeting = ZoomMeetingState(meeting_id)
                self.meetings[meeting_id] = meeting

            participant = payload.get("participant", {}) or {}
            user_id, name, email = self._extract_identity(payload, prefer_sender=False)

            if event_type == "meeting.participant_joined":
                meeting.participant_joined(user_id, name, email)

            elif event_type == "meeting.participant_left":
                meeting.participant_left(user_id)

            elif event_type == "meeting.chat_message_sent":
                user_id, name, _ = self._extract_identity(payload, prefer_sender=True)
                text = self._extract_chat_text(payload)
                meeting.chat_received(user_id, name, text)

            elif event_type in ("meeting.participant_raised_hand", "meeting.reaction_received"):
                reaction = self._extract_reaction_type(payload, participant, event_type)
                meeting.reaction_received(user_id, reaction)

            elif event_type == "meeting.participant_lowered_hand":
                meeting.hand_lowered(user_id)

            else:
                meeting._record_event(
                    "other",
                    user_id=user_id,
                    name=name,
                    data={"raw_event_type": event_type},
                    raw_event_type=event_type,
                )

            # Return current dashboard frame
            return meeting.refresh_live_state()

    def _extract_identity(self, payload: Dict, prefer_sender: bool = False):
        participant = payload.get("participant", {}) or {}
        sender = payload.get("sender", {}) or {}
        candidates = [sender, participant, payload] if prefer_sender else [participant, sender, payload]
        for source in candidates:
            user_id = source.get("user_id") or source.get("id") or source.get("participant_user_id")
            name = source.get("user_name") or source.get("name") or source.get("display_name")
            email = source.get("email", "")
            if user_id or name:
                return str(user_id or name or "unknown"), name or "Unknown", email
        return "unknown", "Unknown", ""

    def _extract_chat_text(self, payload: Dict) -> str:
        return (
            payload.get("message")
            or payload.get("text")
            or payload.get("chat_message")
            or payload.get("chat_text")
            or ""
        )

    def _extract_reaction_type(self, payload: Dict, participant: Dict, event_type: str) -> str:
        reaction = (
            participant.get("reaction")
            or payload.get("reaction")
            or payload.get("reaction_type")
            or payload.get("emoji_type")
            or event_type.split(".")[-1]
        )
        return ZoomMeetingState("tmp")._normalize_reaction_type(reaction)

    def get_active_meeting(self) -> Optional[ZoomMeetingState]:
        """Get the most recently active meeting."""
        with self._lock:
            for mid in reversed(list(self.meetings.keys())):
                if self.meetings[mid].is_active:
                    return self.meetings[mid]
        return None

    def get_active_frame(self) -> Optional[Dict]:
        """Return a thread-safe snapshot of the most recently active meeting."""
        with self._lock:
            for mid in reversed(list(self.meetings.keys())):
                meeting = self.meetings[mid]
                if meeting.is_active:
                    return meeting.refresh_live_state()
        return None

    def get_active_history(self) -> Optional[Dict]:
        """Return a thread-safe history snapshot for the most recently active meeting."""
        with self._lock:
            for mid in reversed(list(self.meetings.keys())):
                meeting = self.meetings[mid]
                if meeting.is_active:
                    return self.get_meeting_history(mid)
        return None

    def get_debug_snapshot(self) -> Dict:
        """Return the latest available live-debug information for UI/debug use."""
        with self._lock:
            active = None
            latest = None
            for mid in reversed(list(self.meetings.keys())):
                latest = self.meetings[mid]
                if self.meetings[mid].is_active:
                    active = self.meetings[mid]
                    break
            subject = active or latest
            return {
                "webhook_configured": bool(self.secret_token),
                "known_meetings": len(self.meetings),
                "has_active_meeting": bool(active),
                "active_meeting_id": active.meeting_id if active else None,
                "latest_meeting_id": latest.meeting_id if latest else None,
                "live_debug": subject.build_observability_snapshot() if subject else None,
            }

    def get_meeting_history(self, meeting_id: str) -> Dict:
        """Get full history for a meeting (for export)."""
        with self._lock:
            meeting = self.meetings.get(meeting_id)
            if not meeting:
                return {}
            return {
                "meeting_id": meeting_id,
                "duration_minutes": meeting.elapsed_minutes,
                "participants": [
                    {
                        "user_id": p.user_id,
                        "name": p.name,
                        "chat_count": p.chat_count,
                        "reaction_count": p.reaction_count,
                    }
                    for p in meeting.participants.values()
                ],
                "chat_messages": list(meeting.chat_messages),
                "events": list(meeting.events),
                "timeline": list(meeting.timeline),
                "recommendations": list(meeting.recommendations),
                "professor_actions": list(meeting.professor_actions),
                "live_debug": meeting.build_observability_snapshot(),
            }
