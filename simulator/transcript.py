"""
Otter.ai-Style Transcript Generator — Post-hoc transcript from simulation events.

Generates a readable markdown transcript that looks like real meeting notes,
with timestamps, speaker labels, silence gaps, reactions, dashboard alerts,
and professor decision annotations.

Usage:
    from simulator.transcript import TranscriptWriter
    writer = TranscriptWriter()
    # Feed events during simulation...
    writer.add_chat(minute=5, speaker="Priya Sharma", text="Great point!")
    writer.add_professor_speech(minute=10, text="Let's take a 5-minute breakout.")
    # Generate output
    md = writer.to_markdown()
"""

import time
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TranscriptEvent:
    """A single event in the transcript."""
    minute: int
    second: int  # Within the minute (0-59)
    event_type: str  # chat, speak, reaction, silence, intervention, alert, professor
    speaker: Optional[str]
    text: str
    metadata: Dict = field(default_factory=dict)


class TranscriptWriter:
    """Accumulates simulation events and generates transcript output."""

    def __init__(self, session_metadata: Optional[Dict] = None):
        self.events: List[TranscriptEvent] = []
        self.metadata = session_metadata or {}
        self._last_event_time = (0, 0)  # (minute, second)

    def add_chat(self, minute: int, speaker: str, text: str,
                 is_confused: bool = False, student_id: str = ""):
        """Add a chat message."""
        second = self._next_second(minute)
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="chat",
            speaker=speaker,
            text=text,
            metadata={"is_confused": is_confused, "student_id": student_id},
        ))

    def add_speech(self, minute: int, speaker: str, duration_sec: float = 0,
                   student_id: str = ""):
        """Add a verbal speaking event."""
        second = self._next_second(minute)
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="speak",
            speaker=speaker,
            text=f"[Speaking for {duration_sec:.0f}s]",
            metadata={"duration": duration_sec, "student_id": student_id},
        ))

    def add_reaction(self, minute: int, speaker: str, reaction_type: str,
                     student_id: str = ""):
        """Add an emoji reaction."""
        second = self._next_second(minute)
        reaction_emoji = {
            "thumbs_up": "👍", "heart": "❤️", "clap": "👏",
            "laugh": "😄", "raised_hand": "✋",
        }
        emoji = reaction_emoji.get(reaction_type, f"[{reaction_type}]")
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="reaction",
            speaker=speaker,
            text=emoji,
            metadata={"reaction_type": reaction_type, "student_id": student_id},
        ))

    def add_professor_speech(self, minute: int, text: str, professor_name: str = "Professor"):
        """Add professor spoken text."""
        second = self._next_second(minute)
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="professor",
            speaker=professor_name,
            text=text,
        ))

    def add_professor_action(self, minute: int, category: str,
                             intervention: Optional[str] = None,
                             rationale: str = "",
                             professor_name: str = "Professor"):
        """Add a professor decision annotation."""
        second = self._next_second(minute)
        action_text = f"[Professor {category}"
        if intervention:
            action_text += f": {intervention}"
        action_text += "]"
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="professor_action",
            speaker=professor_name,
            text=action_text,
            metadata={"category": category, "intervention": intervention, "rationale": rationale},
        ))

    def add_intervention(self, minute: int, intervention_type: str):
        """Add an intervention event."""
        second = self._next_second(minute)
        labels = {
            "breakout": "🔀 Breakout rooms opened",
            "poll": "📊 Poll launched",
            "cold_call": "📢 Cold call",
            "pace_change": "⏩ Pace change",
            "think_pair_share": "🤝 Think-Pair-Share",
        }
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="intervention",
            speaker=None,
            text=labels.get(intervention_type, f"[Intervention: {intervention_type}]"),
        ))

    def add_pattern_alert(self, minute: int, pattern_type: str,
                          severity: str, message: str):
        """Add a dashboard pattern detection alert."""
        second = self._next_second(minute)
        severity_icon = {"mild": "🟡", "moderate": "🟠", "severe": "🔴"}.get(severity, "⚪")
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="alert",
            speaker=None,
            text=f"{severity_icon} Dashboard alert: {message}",
            metadata={"pattern": pattern_type, "severity": severity},
        ))

    def add_recommendation(self, minute: int, priority: str,
                           action: str, message: str):
        """Add a dashboard recommendation."""
        second = self._next_second(minute)
        self.events.append(TranscriptEvent(
            minute=minute, second=second,
            event_type="recommendation",
            speaker=None,
            text=f"[IDSS recommends ({priority}): {message}]",
            metadata={"priority": priority, "action": action},
        ))

    def _next_second(self, minute: int) -> int:
        """Generate a plausible second timestamp."""
        if minute > self._last_event_time[0]:
            self._last_event_time = (minute, 0)
            return 0
        else:
            next_sec = min(59, self._last_event_time[1] + 3)
            self._last_event_time = (minute, next_sec)
            return next_sec

    def to_markdown(self) -> str:
        """Generate Otter.ai-style markdown transcript."""
        lines = []

        # Header
        lines.append("# SAGE Simulation Transcript")
        lines.append("")

        if self.metadata:
            lines.append(f"**Session:** {self.metadata.get('session_id', 'N/A')}")
            lines.append(f"**Date:** {self.metadata.get('timestamp', time.strftime('%Y-%m-%d %H:%M'))}")
            lines.append(f"**Duration:** {self.metadata.get('duration_minutes', '?')} minutes")
            lines.append(f"**Scenario:** {self.metadata.get('scenario', 'N/A')}")
            university = self.metadata.get('university', '')
            if university:
                lines.append(f"**University preset:** {university}")
            prof = self.metadata.get('professor_style', '')
            if prof and prof != 'none':
                lines.append(f"**Professor:** {prof}")
            lines.append(f"**Students:** {self.metadata.get('student_count', '?')}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Sort events by time
        sorted_events = sorted(self.events, key=lambda e: (e.minute, e.second))

        # Track silence gaps
        last_speech_minute = 0
        current_minute = 0

        for event in sorted_events:
            # Insert silence gap markers
            if event.minute > last_speech_minute + 2 and event.event_type in ("chat", "speak", "professor"):
                gap = event.minute - last_speech_minute
                if gap >= 3:
                    lines.append(f"\n*[Silence — {gap} minutes]*\n")

            # Minute marker (every 5 minutes)
            if event.minute >= current_minute + 5:
                current_minute = (event.minute // 5) * 5
                lines.append(f"\n### — Minute {current_minute} —\n")

            # Format timestamp
            ts = f"**{event.minute:02d}:{event.second:02d}**"

            if event.event_type == "chat":
                confused_marker = " ❓" if event.metadata.get("is_confused") else ""
                lines.append(f"{ts} **{event.speaker}** *(chat)*: {event.text}{confused_marker}")

            elif event.event_type == "speak":
                lines.append(f"{ts} **{event.speaker}**: {event.text}")

            elif event.event_type == "reaction":
                lines.append(f"{ts} *[Reaction: {event.text} from {event.speaker}]*")

            elif event.event_type == "professor":
                lines.append(f"\n{ts} **🎓 {event.speaker}**: {event.text}\n")

            elif event.event_type == "professor_action":
                rationale = event.metadata.get("rationale", "")
                lines.append(f"{ts} *{event.text}*")
                if rationale:
                    lines.append(f"  > *Rationale: {rationale}*")

            elif event.event_type == "intervention":
                lines.append(f"\n{ts} **{event.text}**\n")

            elif event.event_type == "alert":
                lines.append(f"{ts} {event.text}")

            elif event.event_type == "recommendation":
                lines.append(f"{ts} {event.text}")

            # Track last speech
            if event.event_type in ("chat", "speak", "professor"):
                last_speech_minute = event.minute

        # Footer
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by SAGE v2 — {time.strftime('%Y-%m-%d %H:%M')}*")

        return "\n".join(lines)

    def to_json(self) -> List[Dict]:
        """Machine-readable event stream."""
        return [
            {
                "minute": e.minute,
                "second": e.second,
                "event_type": e.event_type,
                "speaker": e.speaker,
                "text": e.text,
                "metadata": e.metadata,
            }
            for e in sorted(self.events, key=lambda e: (e.minute, e.second))
        ]

    def save(self, directory: str = "transcripts", session_id: str = ""):
        """Save transcript to markdown and JSON files."""
        os.makedirs(directory, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        sid = session_id or self.metadata.get("session_id", "unknown")
        base = f"{directory}/sage_{sid}_{timestamp}"

        # Markdown
        md_path = f"{base}.md"
        with open(md_path, "w") as f:
            f.write(self.to_markdown())

        # JSON
        json_path = f"{base}.json"
        import json
        with open(json_path, "w") as f:
            json.dump({
                "metadata": self.metadata,
                "events": self.to_json(),
            }, f, indent=2, default=str)

        return md_path, json_path
