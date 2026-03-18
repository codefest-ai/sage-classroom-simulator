"""
LLM-Powered Professor Agent — Makes decisions through the IDSS dashboard.

The professor receives the EXACT same JSON the dashboard renders and makes
taxonomy-classified decisions. This closes the DSR evaluation loop:
if the professor makes good decisions → the dashboard design works.

Produces:
- response_category: ignore | acknowledge | accept | modify | reject
- intervention_type: breakout | poll | cold_call | pace_change | think_pair_share | clarification
- rationale: why the professor made this decision
- spoken_text: what the professor SAYS to the class (feeds into student context)
"""

import json
from typing import Dict, Optional, List

from .llm_client import LLMClient
from .professor import PROFESSOR_STYLES, SimulatedProfessor, ProfessorAction


class LLMProfessor:
    """
    Professor agent that reads the dashboard and decides via LLM.

    Falls back to rule-based SimulatedProfessor if LLM is unavailable.
    """

    def __init__(
        self,
        style: str = "adaptive",
        llm: Optional[LLMClient] = None,
    ):
        self.style_key = style
        self.style = PROFESSOR_STYLES.get(style, PROFESSOR_STYLES["adaptive"])
        self.llm = llm or LLMClient()
        self._fallback = SimulatedProfessor(style=style)
        self.actions: List[Dict] = []
        self._last_intervention_minute = -10
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build professor personality from style profile."""
        s = self.style
        lines = [
            f"You are {s.name}, a professor teaching a graduate seminar.",
            f"Teaching philosophy: {s.description}",
            "",
            "You are using an Instructional Decision Support System (IDSS) dashboard",
            "that shows you real-time engagement data about your students.",
            "",
            "The dashboard shows:",
            "- Class-wide engagement percentage",
            "- Individual student engagement states (engaged/drifting/disengaged/confused)",
            "- Detected patterns (energy decay, equity imbalance, confusion clusters)",
            "- AI-generated recommendations with priority levels",
            "- Recent student chat messages",
            "",
            "When you see a recommendation, you must decide:",
            "1. RESPONSE CATEGORY (exactly one of): ignore, acknowledge, accept, modify, reject",
            "2. INTERVENTION TYPE (if acting): breakout, poll, cold_call, pace_change, think_pair_share, clarification, or none",
            "3. RATIONALE: A brief explanation of your decision (1 sentence)",
            "4. SPOKEN TEXT: What you actually say to the class (1-2 sentences). This is what students hear.",
            "",
            "Respond in this exact JSON format:",
            '{"response_category": "...", "intervention_type": "...", "rationale": "...", "spoken_text": "..."}',
            "",
            "RULES:",
            "- Stay in character as this professor type",
            "- Don't stack interventions within 3 minutes of each other",
            "- Your spoken_text should sound like a real professor talking to a class",
            "- If ignoring, spoken_text can be null (you say nothing)",
            "- Base decisions on the actual data, not just the recommendation",
        ]
        return "\n".join(lines)

    def decide_from_dashboard(
        self,
        dashboard_state: Dict,
        minute: int,
    ) -> Optional[Dict]:
        """
        Make a decision based on the dashboard state.

        Args:
            dashboard_state: Same JSON the frontend renders
            minute: Current simulation minute

        Returns:
            Decision dict or None
        """
        # Build the context the professor sees
        recs = dashboard_state.get("recent_recommendations", [])
        if not recs:
            # No recommendations — check if self-initiation needed
            return self._check_self_initiation(dashboard_state, minute)

        # Build user prompt from dashboard data
        context_lines = [
            f"MINUTE {minute} — Dashboard State:",
            f"  Class engagement: {dashboard_state.get('class_engagement', 0):.0%}",
            f"  Active speakers: {dashboard_state.get('active_speakers', 0)}",
            f"  Speaking equity (Gini): {dashboard_state.get('speaking_gini', 0):.2f}",
        ]

        # Patterns
        patterns = dashboard_state.get("patterns", [])
        if patterns:
            context_lines.append("  Detected patterns:")
            for p in patterns:
                context_lines.append(f"    - {p.get('type', '?')} ({p.get('severity', '?')}): {p.get('message', '')}")

        # Student states summary
        students = dashboard_state.get("students", [])
        if students:
            states = {}
            for s in students:
                st = "confused" if s.get("is_confused") else s.get("state", "?")
                states[st] = states.get(st, 0) + 1
            context_lines.append(f"  Student states: {states}")

        # Recommendations
        context_lines.append("\n  RECOMMENDATIONS:")
        for r in recs[-3:]:  # Show latest 3
            context_lines.append(f"    [{r.get('priority', '?')} priority] {r.get('message', '')}")
            context_lines.append(f"    Suggested action: {r.get('action', '?')}")

        # Recent chat
        recent_chat = dashboard_state.get("recent_chat", [])
        if recent_chat:
            context_lines.append("\n  Recent chat:")
            for c in recent_chat[-5:]:
                sid = c.get("student_id", "?")
                text = c.get("data", {}).get("text", "") if isinstance(c.get("data"), dict) else ""
                context_lines.append(f"    {sid}: {text}")

        # Minutes since last intervention
        gap = minute - self._last_intervention_minute
        context_lines.append(f"\n  Minutes since your last intervention: {gap}")
        if gap < 3:
            context_lines.append("  (Too soon to intervene again — consider acknowledging or ignoring)")

        user_prompt = "\n".join(context_lines)

        # Call LLM
        response = self.llm.generate(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            max_tokens=150,
            temperature=0.7,
        )

        if response is None:
            # Fallback to rule-based
            return self._fallback_decide(recs, minute)

        # Parse JSON response
        decision = self._parse_decision(response, minute)
        if decision is None:
            return self._fallback_decide(recs, minute)

        # Track intervention timing
        if decision.get("intervention_type") and decision["intervention_type"] != "none":
            self._last_intervention_minute = minute

        self.actions.append(decision)
        return decision

    def _check_self_initiation(self, dashboard_state: Dict, minute: int) -> Optional[Dict]:
        """Check if professor should self-initiate without a recommendation."""
        engagement = dashboard_state.get("class_engagement", 0.5)
        gap = minute - self._last_intervention_minute

        if engagement > self.style.self_initiation_threshold or gap < 5:
            return None

        # Low engagement, no recommendation — ask LLM what to do
        context = (
            f"MINUTE {minute}: Class engagement is {engagement:.0%} which is below your comfort threshold. "
            f"No recommendation from the dashboard. Last intervention was {gap} minutes ago. "
            f"Do you want to do something? If yes, what intervention and what do you say to the class?"
        )

        response = self.llm.generate(
            system_prompt=self._system_prompt,
            user_prompt=context,
            max_tokens=120,
            temperature=0.7,
        )

        if response:
            decision = self._parse_decision(response, minute)
            if decision:
                decision["response_category"] = "self_initiated"
                if decision.get("intervention_type"):
                    self._last_intervention_minute = minute
                self.actions.append(decision)
                return decision

        return None

    def _parse_decision(self, response: str, minute: int) -> Optional[Dict]:
        """Parse LLM response into structured decision."""
        # Try JSON parsing
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                # Validate required fields
                valid_categories = {"ignore", "acknowledge", "accept", "modify", "reject", "self_initiated"}
                category = data.get("response_category", "acknowledge")
                if category not in valid_categories:
                    category = "acknowledge"

                valid_interventions = {"breakout", "poll", "cold_call", "pace_change",
                                      "think_pair_share", "clarification", "none", None}
                intervention = data.get("intervention_type")
                if intervention not in valid_interventions:
                    intervention = None

                return {
                    "minute": minute,
                    "response_category": category,
                    "intervention_type": intervention if intervention != "none" else None,
                    "rationale": data.get("rationale", "No rationale provided"),
                    "spoken_text": data.get("spoken_text"),
                }
        except (json.JSONDecodeError, ValueError):
            pass

        # If JSON parsing fails, try to extract from natural language
        response_lower = response.lower()
        category = "acknowledge"
        intervention = None
        for cat in ["accept", "modify", "reject", "ignore"]:
            if cat in response_lower:
                category = cat
                break

        for iv in ["breakout", "poll", "cold_call", "pace_change", "think_pair_share", "clarification"]:
            if iv.replace("_", " ") in response_lower or iv in response_lower:
                intervention = iv
                break

        return {
            "minute": minute,
            "response_category": category,
            "intervention_type": intervention,
            "rationale": response[:100],
            "spoken_text": response if category != "ignore" else None,
        }

    def _fallback_decide(self, recs: List[Dict], minute: int) -> Optional[Dict]:
        """Fall back to rule-based professor when LLM is unavailable."""
        actions = self._fallback.process_recommendations(recs, minute)
        if not actions:
            return None

        a = actions[0]
        return {
            "minute": a.minute,
            "response_category": a.response_category,
            "intervention_type": a.intervention_type,
            "rationale": a.rationale,
            "spoken_text": None,  # Rule-based professor doesn't speak
        }

    def get_action_summary(self) -> Dict:
        """Summarize all professor actions for analysis."""
        if not self.actions:
            return {"total_actions": 0, "style": self.style_key}

        category_counts = {}
        intervention_counts = {}
        for a in self.actions:
            cat = a.get("response_category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
            iv = a.get("intervention_type")
            if iv:
                intervention_counts[iv] = intervention_counts.get(iv, 0) + 1

        acting = sum(category_counts.get(c, 0) for c in ["accept", "modify", "self_initiated"])
        total = len(self.actions)

        return {
            "total_actions": total,
            "style": self.style_key,
            "style_name": self.style.name,
            "category_distribution": category_counts,
            "interventions_used": intervention_counts,
            "acceptance_rate": round(acting / max(1, total) * 100),
        }
