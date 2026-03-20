"""
Zoom Webhook Adapter — Translates live Zoom meeting events into SAGE dashboard frames.

Receives Zoom webhook events (participant join/leave, chat, reactions)
and maps them to the same signal format the IDSS dashboard consumes.

The dashboard doesn't know if data comes from simulation or Zoom — same interface.

Setup:
1. Create a Zoom App at marketplace.zoom.us (Webhook Only type)
2. Set Event Notification URL to: https://your-server.onrender.com/api/zoom/webhook
3. Subscribe to: meeting.participant_joined, meeting.participant_left,
   meeting.chat_message_sent, meeting.participant_raised_hand
4. Copy the Secret Token for verification
"""

import hashlib
import hmac
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


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
        self.is_active: bool = True

    @property
    def elapsed_minutes(self) -> int:
        return max(1, int((time.time() - self.started_at) / 60))

    def participant_joined(self, user_id: str, name: str, email: str = ""):
        if user_id not in self.participants:
            self.participants[user_id] = ZoomParticipant(
                user_id=user_id, name=name, email=email,
                joined_at=time.time(),
            )
        else:
            self.participants[user_id].is_present = True
            self.participants[user_id].left_at = 0
        self.events.append({
            "minute": self.elapsed_minutes,
            "event_type": "join",
            "student_id": user_id,
            "data": {"name": name},
        })

    def participant_left(self, user_id: str):
        if user_id in self.participants:
            self.participants[user_id].is_present = False
            self.participants[user_id].left_at = time.time()
        self.events.append({
            "minute": self.elapsed_minutes,
            "event_type": "leave",
            "student_id": user_id,
            "data": {},
        })

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
        self.events.append({
            "minute": minute,
            "event_type": "chat",
            "student_id": user_id,
            "data": {"text": text},
        })

    def reaction_received(self, user_id: str, reaction_type: str):
        minute = self.elapsed_minutes
        self.reactions.append({
            "minute": minute,
            "student_id": user_id,
            "type": reaction_type,
        })
        if user_id in self.participants:
            self.participants[user_id].reaction_count += 1
            self.participants[user_id].last_active_minute = minute
            if reaction_type == "raised_hand":
                self.participants[user_id].hand_raised = True

    def hand_lowered(self, user_id: str):
        if user_id in self.participants:
            self.participants[user_id].hand_raised = False

    def to_dashboard_frame(self) -> Dict:
        """Convert current Zoom state to SAGE dashboard frame format."""
        minute = self.elapsed_minutes
        present = [p for p in self.participants.values() if p.is_present]
        total = len(present) or 1

        # Engagement heuristics from Zoom signals
        students = []
        engagement_sum = 0
        active_speakers = 0
        chat_counts = []

        for p in present:
            minutes_since_active = minute - p.last_active_minute if p.last_active_minute > 0 else minute
            minutes_since_chat = minute - p.last_chat_minute if p.last_chat_minute > 0 else minute

            # Simple engagement model from Zoom signals
            eng = 0.5  # baseline: present
            if minutes_since_active <= 2:
                eng += 0.3  # recently active
            elif minutes_since_active <= 5:
                eng += 0.15
            if p.chat_count > 0:
                eng += min(0.2, p.chat_count * 0.05)
            if p.hand_raised:
                eng += 0.1
            if not p.camera_on:
                eng -= 0.15
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
                },
            })

            engagement_sum += eng
            chat_counts.append(p.chat_count)
            if minutes_since_active <= 1:
                active_speakers += 1

        class_engagement = engagement_sum / total

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
                           "message": f"Class engagement at {class_engagement:.0%}", "value": class_engagement})
        if gini > 0.5 and sum(chat_counts) > 5:
            patterns.append({"type": "equity_imbalance", "severity": "moderate",
                           "message": f"Discussion dominated by few voices (Gini={gini:.2f})", "value": gini})
        silent = sum(1 for s in students if s["state"] == "disengaged")
        if silent >= len(students) * 0.4:
            patterns.append({"type": "silent_majority", "severity": "moderate",
                           "message": f"{silent} students disengaged", "value": silent})

        return {
            "minute": minute,
            "class_engagement": class_engagement,
            "engagement_std": 0,
            "speaking_gini": gini,
            "active_speakers": active_speakers,
            "patterns": patterns,
            "students": students,
            "source": "zoom_live",
        }


class ZoomWebhookHandler:
    """Processes incoming Zoom webhook events."""

    def __init__(self, secret_token: str = ""):
        self.secret_token = secret_token
        self.meetings: Dict[str, ZoomMeetingState] = {}

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
        meeting_id = str(payload.get("id", ""))

        if not meeting_id:
            return None

        # Handle validation challenge (Zoom sends this on app setup)
        if event_type == "endpoint.url_validation":
            plain_token = event.get("payload", {}).get("plainToken", "")
            encrypted = hmac.new(
                self.secret_token.encode(), plain_token.encode(), hashlib.sha256
            ).hexdigest()
            return {"plainToken": plain_token, "encryptedToken": encrypted}

        if event_type == "meeting.started":
            self.meetings[meeting_id] = ZoomMeetingState(meeting_id)
            return {"status": "meeting_started", "meeting_id": meeting_id}

        if event_type == "meeting.ended":
            if meeting_id in self.meetings:
                self.meetings[meeting_id].is_active = False
            return {"status": "meeting_ended", "meeting_id": meeting_id}

        meeting = self.meetings.get(meeting_id)
        if not meeting:
            # Meeting started before server — create retroactively
            meeting = ZoomMeetingState(meeting_id)
            self.meetings[meeting_id] = meeting

        participant = payload.get("participant", {})
        user_id = participant.get("user_id", participant.get("id", ""))
        name = participant.get("user_name", participant.get("name", "Unknown"))
        email = participant.get("email", "")

        if event_type == "meeting.participant_joined":
            meeting.participant_joined(user_id, name, email)

        elif event_type == "meeting.participant_left":
            meeting.participant_left(user_id)

        elif event_type == "meeting.chat_message_sent":
            text = payload.get("message", "")
            sender = payload.get("sender", {})
            user_id = sender.get("user_id", sender.get("id", ""))
            name = sender.get("user_name", sender.get("name", "Unknown"))
            meeting.chat_received(user_id, name, text)

        elif event_type in ("meeting.participant_raised_hand", "meeting.reaction_received"):
            reaction = participant.get("reaction", event_type.split(".")[-1])
            meeting.reaction_received(user_id, reaction)

        elif event_type == "meeting.participant_lowered_hand":
            meeting.hand_lowered(user_id)

        # Return current dashboard frame
        return meeting.to_dashboard_frame()

    def get_active_meeting(self) -> Optional[ZoomMeetingState]:
        """Get the most recently active meeting."""
        for mid in reversed(list(self.meetings.keys())):
            if self.meetings[mid].is_active:
                return self.meetings[mid]
        return None

    def get_meeting_history(self, meeting_id: str) -> Dict:
        """Get full history for a meeting (for export)."""
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
            "chat_messages": meeting.chat_messages,
            "events": meeting.events,
            "timeline": [],  # Could accumulate frames over time
        }
