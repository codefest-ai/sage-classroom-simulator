"""
LLM-Powered Student Agent — Generates in-character chat from room context.

Each student perceives:
- Their own profile (personality, major, engagement state)
- Room context (last 5 messages, professor action, active intervention)
- Affinity-weighted messages from 2-3 "nearby" students

The LLM decides WHAT to say (or [SILENT] for nothing).
The engagement MODEL (scoring.py) still decides the numbers.

Social contagion is implicit: if 3 students just said "I'm confused,"
the next student's context window contains those messages, and the LLM
naturally generates a contagion response. No explicit contagion matrix.
"""

import random
from typing import List, Dict, Optional

from .profiles import StudentProfile
from .llm_client import LLMClient


class StudentAgent:
    """Wraps a StudentProfile with LLM-powered chat generation."""

    def __init__(self, profile: StudentProfile, llm: LLMClient):
        self.profile = profile
        self.llm = llm
        self._affinity_peers: List[str] = []  # student_ids this student pays attention to
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build character prompt from profile data."""
        p = self.profile
        d = p.demographic

        # Core identity
        lines = [
            f"You are {p.name}, a graduate student in {d.get('major', 'Information Systems')}.",
            f"Age: {d.get('age', 25)}. Learning style: {d.get('learning_style', 'mixed')}.",
        ]

        # Background flavor
        if d.get("is_working_professional"):
            lines.append("You work full-time and attend class in the evenings/online.")
        if d.get("origin_country"):
            lines.append(f"You're an international student from {d['origin_country']}.")

        # Personality from archetype
        archetype = getattr(p, 'archetype', None) or ''
        personality_map = {
            "Engaged Leader": "You're enthusiastic, ask clarifying questions, and build on others' points.",
            "Critical Thinker": "You challenge ideas, ask about methodology, and push back on weak arguments.",
            "Collaborative Learner": "You thrive in groups, seek practical examples, and connect ideas to real-world applications.",
            "Hands-On Builder": "You prefer code and demos over lecture. You get restless during theory-heavy sessions.",
            "Reflective Processor": "You need time to think before speaking. You go quiet when processing, not disengaged.",
            "Pragmatist": "You focus on business cases, ROI, and practical takeaways. Theory bores you unless applied.",
            "Visual Learner": "You love diagrams and visualizations. You express yourself through reactions more than words.",
            "Social Connector": "You build bridges between ideas and people. You want group discussion and peer learning.",
            "Withdrawn": "You rarely participate. When you do speak, it's brief. Cold calls make you anxious.",
            "Creative Observer": "You think in metaphors and visuals. You prefer reactions to speaking up.",
            "The Lurker": "You're invisible but attentive. You absorb everything but almost never speak or chat.",
            "The Fader": "You start strong but lose focus fast. You're self-aware about drifting and sometimes joke about it.",
            "The Dominator": "You have a LOT to say. You respond to everything, challenge others, and want to share your experience.",
            "The Confused": "You struggle with the material. You signal confusion frequently and need things explained differently.",
            "The Ideal": "You're balanced — you speak, listen, ask questions, and build on others' points. You're consistently engaged.",
        }
        if archetype in personality_map:
            lines.append(personality_map[archetype])

        # Behavior rules
        lines.extend([
            "",
            "RULES:",
            "- You are in a live graduate class. Respond naturally as this student would.",
            "- Keep responses to 1-2 SHORT sentences max. This is chat, not an essay.",
            "- If you have nothing to say, respond with exactly: [SILENT]",
            "- DO NOT start with 'As a student' or 'I think that'. Just speak naturally.",
            "- You can reference other students by first name if responding to them.",
            "- Match your engagement level: if bored, your responses should be minimal or absent.",
            "- If confused, say so directly — don't pretend to understand.",
        ])

        return "\n".join(lines)

    def set_affinity_peers(self, all_profiles: List[StudentProfile]):
        """
        Set 2-3 peers this student pays attention to.
        Affinity based on shared major category or similar engagement level.
        """
        my_major = self.profile.demographic.get("major", "")
        my_baseline = self.profile.engagement_baseline
        candidates = []

        for p in all_profiles:
            if p.student_id == self.profile.student_id:
                continue
            score = 0.0
            # Same or similar major
            if p.demographic.get("major", "") == my_major:
                score += 2.0
            # Similar engagement level
            if p.engagement_baseline == my_baseline:
                score += 1.0
            # Random factor (people notice random people)
            score += random.random() * 0.5
            candidates.append((p.student_id, score))

        candidates.sort(key=lambda x: -x[1])
        self._affinity_peers = [c[0] for c in candidates[:3]]

    def generate_state_and_chat(
        self,
        current_engagement: float,
        room_context: List[Dict],
        content_block: Optional[Dict] = None,
        professor_action: Optional[str] = None,
        active_intervention: Optional[str] = None,
        minutes_elapsed: int = 0,
    ) -> Dict:
        """
        Combined LLM call — agent decides BOTH engagement level and chat.
        Returns {"engagement": float 0-1, "chat": str or None}
        """
        context_lines = [f"It is minute {minutes_elapsed} of a 45-minute class."]

        # What's being taught right now
        if content_block:
            ctype = content_block.get("type", "lecture")
            topic = content_block.get("topic", "")
            complexity = content_block.get("complexity", "medium")
            mins_in = minutes_elapsed - content_block.get("minute", 0)
            type_desc = {
                "lecture": f"The professor has been lecturing for {mins_in} minutes",
                "discussion": "The class is in open discussion",
                "breakout": "You're in a small breakout group",
                "presentation": "Students are presenting their group work",
                "wrapup": "The professor is wrapping up the session",
            }
            context_lines.append(f"{type_desc.get(ctype, ctype)} on: {topic}")
            if complexity == "high":
                context_lines.append("This material is complex and dense.")
            elif complexity == "low":
                context_lines.append("This material is straightforward.")

        # Professor action
        if professor_action:
            context_lines.append(f"The professor just said: \"{professor_action}\"")
        if active_intervention:
            intervention_desc = {
                "breakout": "The class just split into breakout rooms.",
                "poll": "The professor just posted a poll question.",
                "cold_call": "The professor is calling on students directly.",
                "pace_change": "The professor just switched the activity format.",
                "think_pair_share": "Think-pair-share: reflect, discuss with a partner, then share.",
            }
            context_lines.append(intervention_desc.get(active_intervention, f"Activity: {active_intervention}"))

        # Room messages
        if room_context:
            context_lines.append("\nRecent chat:")
            affinity_msgs = [m for m in room_context if m.get("student_id") in self._affinity_peers]
            other_msgs = [m for m in room_context if m.get("student_id") not in self._affinity_peers]
            shown = (affinity_msgs[-3:] + other_msgs[-2:])[-5:]
            for msg in shown:
                name = msg.get("name", "Someone")
                text = msg.get("text", "")
                if text:
                    context_lines.append(f"  {name}: {text}")

        context_lines.append(f"\nYour current engagement: {int(current_engagement * 100)}%")
        context_lines.append("")
        context_lines.append("Respond in this EXACT format (two lines):")
        context_lines.append("ENGAGEMENT: [number 0-100]")
        context_lines.append("CHAT: [your message or SILENT]")

        user_prompt = "\n".join(context_lines)

        response = self.llm.generate(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            max_tokens=60,
            temperature=0.85,
        )

        if response is None:
            return {"engagement": current_engagement, "chat": None}

        # Parse the two-line response
        engagement = current_engagement
        chat = None

        for line in response.split("\n"):
            line = line.strip()
            if line.upper().startswith("ENGAGEMENT:"):
                try:
                    val = int(''.join(c for c in line.split(":", 1)[1] if c.isdigit()))
                    engagement = max(0, min(100, val)) / 100.0
                except (ValueError, IndexError):
                    pass
            elif line.upper().startswith("CHAT:"):
                text = line.split(":", 1)[1].strip() if ":" in line else ""
                if text and "[SILENT]" not in text.upper() and "SILENT" != text.upper().strip() and len(text) > 1:
                    chat = text.strip('"').strip("'")

        return {"engagement": engagement, "chat": chat}

    def generate_chat(
        self,
        engagement: float,
        room_context: List[Dict],
        professor_action: Optional[str] = None,
        active_intervention: Optional[str] = None,
        is_confused: bool = False,
    ) -> Optional[str]:
        """
        Generate a chat message using the LLM.

        Args:
            engagement: Current engagement score (0-1)
            room_context: Recent chat messages [{student_id, name, text, minute}]
            professor_action: What the professor just said/did
            active_intervention: Current active intervention type
            is_confused: Whether engagement model says student is confused

        Returns:
            Chat message string, or None if student is silent
        """
        # Build context prompt
        context_lines = []

        # Engagement state
        if engagement >= 0.65:
            context_lines.append("You are currently ENGAGED and following along well.")
        elif engagement >= 0.40:
            context_lines.append("You are currently DRIFTING — losing focus a bit.")
        else:
            context_lines.append("You are currently DISENGAGED — having trouble paying attention.")

        if is_confused:
            context_lines.append("You are CONFUSED about what's being discussed.")

        # Professor action
        if professor_action:
            context_lines.append(f"\nThe professor just said: \"{professor_action}\"")
        if active_intervention:
            intervention_desc = {
                "breakout": "The class just split into breakout rooms for small group discussion.",
                "poll": "The professor just posted a quick poll question.",
                "cold_call": "The professor is cold-calling students to answer.",
                "pace_change": "The professor switched from lecture to discussion mode.",
                "think_pair_share": "The professor asked everyone to think, discuss with a partner, then share.",
            }
            context_lines.append(intervention_desc.get(active_intervention, f"Activity: {active_intervention}"))

        # Recent room messages (prioritize affinity peers)
        if room_context:
            context_lines.append("\nRecent chat messages:")
            # Sort: affinity peers first, then others
            affinity_msgs = [m for m in room_context if m.get("student_id") in self._affinity_peers]
            other_msgs = [m for m in room_context if m.get("student_id") not in self._affinity_peers]
            # Show up to 5: prioritize affinity
            shown = (affinity_msgs[-3:] + other_msgs[-2:])[-5:]
            for msg in shown:
                name = msg.get("name", msg.get("student_id", "Someone"))
                text = msg.get("text", "")
                if text:
                    context_lines.append(f"  {name}: {text}")

        context_lines.append("\nWhat do you say in the chat? (or [SILENT] if nothing)")

        user_prompt = "\n".join(context_lines)

        # Call LLM
        response = self.llm.generate(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            max_tokens=40,
            temperature=0.85,
        )

        if response is None:
            return None  # LLM unavailable — caller falls back to templates

        # Check for silence
        if "[SILENT]" in response or "[silent]" in response:
            return None

        # Clean up
        response = response.strip().strip('"').strip("'")
        if not response or len(response) < 2:
            return None

        return response
