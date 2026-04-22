"""
Simulated Professor — AI professor agent that responds to dashboard recommendations.

Enables fully closed-loop testing: student agents generate engagement data,
the scoring model detects patterns, the dashboard shows recommendations,
and the professor agent responds — all without human participants.

Professor styles map to the instructor heterogeneity finding from Li et al. (2025):
- adaptive: high recommendation acceptance, modifies based on context
- lecture_focused: low acceptance, maintains planned pacing
- discussion_based: high acceptance for discussion-promoting interventions
- hands_off: minimal intervention, wait-and-see posture (Wise & Jung, 2019)
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .scoring import ClassSnapshot


# ============================================================
# PROFESSOR STYLES
# ============================================================

@dataclass
class ProfessorStyle:
    """Configuration for a simulated professor's teaching approach."""
    name: str
    description: str

    # Response probabilities per recommendation priority (high/medium/low)
    # Maps to the 5-category taxonomy: ignore, acknowledge, accept, modify, reject
    high_priority_response: Dict[str, float]
    medium_priority_response: Dict[str, float]
    low_priority_response: Dict[str, float]

    # Preference for specific intervention types (0.0-1.0)
    intervention_preferences: Dict[str, float]

    # Delay in minutes before acting on a recommendation
    response_delay_range: Tuple[int, int]

    # Threshold for acting without recommendation (self-initiated)
    self_initiation_threshold: float


PROFESSOR_STYLES = {
    "adaptive": ProfessorStyle(
        name="Dr. Adaptive",
        description="Responsive instructor who engages deeply with recommendations and modifies them for context",
        high_priority_response={"ignore": 0.05, "acknowledge": 0.10, "accept": 0.30, "modify": 0.45, "reject": 0.10},
        medium_priority_response={"ignore": 0.10, "acknowledge": 0.20, "accept": 0.25, "modify": 0.35, "reject": 0.10},
        low_priority_response={"ignore": 0.25, "acknowledge": 0.30, "accept": 0.15, "modify": 0.20, "reject": 0.10},
        intervention_preferences={
            "breakout": 0.8, "poll": 0.7, "cold_call": 0.5,
            "pace_change": 0.9, "think_pair_share": 0.85,
            "clarification": 0.9, "equity_intervention": 0.7, "activation": 0.8,
        },
        response_delay_range=(0, 2),
        self_initiation_threshold=0.4,
    ),

    "lecture_focused": ProfessorStyle(
        name="Dr. Lecturer",
        description="Content-driven instructor who prioritizes coverage and rarely deviates from plan",
        high_priority_response={"ignore": 0.15, "acknowledge": 0.30, "accept": 0.15, "modify": 0.15, "reject": 0.25},
        medium_priority_response={"ignore": 0.30, "acknowledge": 0.30, "accept": 0.10, "modify": 0.10, "reject": 0.20},
        low_priority_response={"ignore": 0.50, "acknowledge": 0.25, "accept": 0.05, "modify": 0.05, "reject": 0.15},
        intervention_preferences={
            "breakout": 0.2, "poll": 0.4, "cold_call": 0.6,
            "pace_change": 0.3, "think_pair_share": 0.3,
            "clarification": 0.7, "equity_intervention": 0.3, "activation": 0.4,
        },
        response_delay_range=(2, 5),
        self_initiation_threshold=0.6,
    ),

    "discussion_based": ProfessorStyle(
        name="Dr. Discussion",
        description="Socratic instructor who emphasizes student voice and group dialogue",
        high_priority_response={"ignore": 0.05, "acknowledge": 0.10, "accept": 0.35, "modify": 0.40, "reject": 0.10},
        medium_priority_response={"ignore": 0.10, "acknowledge": 0.15, "accept": 0.30, "modify": 0.35, "reject": 0.10},
        low_priority_response={"ignore": 0.20, "acknowledge": 0.25, "accept": 0.20, "modify": 0.25, "reject": 0.10},
        intervention_preferences={
            "breakout": 0.9, "poll": 0.5, "cold_call": 0.7,
            "pace_change": 0.6, "think_pair_share": 0.95,
            "clarification": 0.8, "equity_intervention": 0.9, "activation": 0.9,
        },
        response_delay_range=(0, 1),
        self_initiation_threshold=0.35,
    ),

    "hands_off": ProfessorStyle(
        name="Dr. Observer",
        description="Minimal-intervention instructor with wait-and-see posture (Wise & Jung 2019 finding)",
        high_priority_response={"ignore": 0.20, "acknowledge": 0.35, "accept": 0.15, "modify": 0.15, "reject": 0.15},
        medium_priority_response={"ignore": 0.40, "acknowledge": 0.30, "accept": 0.10, "modify": 0.10, "reject": 0.10},
        low_priority_response={"ignore": 0.60, "acknowledge": 0.25, "accept": 0.05, "modify": 0.05, "reject": 0.05},
        intervention_preferences={
            "breakout": 0.3, "poll": 0.3, "cold_call": 0.2,
            "pace_change": 0.4, "think_pair_share": 0.3,
            "clarification": 0.5, "equity_intervention": 0.3, "activation": 0.3,
        },
        response_delay_range=(3, 8),
        self_initiation_threshold=0.7,
    ),
}

RECOMMENDATION_ACTION_MAP = {
    "equity_intervention": "think_pair_share",
    "activation": "poll",
}


@dataclass
class ProfessorAction:
    """A recorded action from the simulated professor."""
    minute: int
    recommendation_id: Optional[int]
    response_category: str  # ignore, acknowledge, accept, modify, reject
    intervention_type: Optional[str]
    rationale: str
    spoken_text: Optional[str]
    delay_minutes: int


class SimulatedProfessor:
    """
    AI professor agent that processes engagement data and recommendations.

    The professor follows their style profile to decide:
    1. Whether to act on a recommendation (5-category taxonomy)
    2. What specific intervention to use
    3. When to self-initiate without a recommendation
    """

    def __init__(self, style: str = "adaptive"):
        if style not in PROFESSOR_STYLES:
            raise ValueError(f"Unknown style: {style}. Options: {list(PROFESSOR_STYLES.keys())}")
        self.style = PROFESSOR_STYLES[style]
        self.actions: List[ProfessorAction] = []
        self._pending_responses: List[Dict] = []
        self._last_intervention_minute: int = -10

    def process_recommendations(self, recommendations: List[Dict], minute: int,
                                class_snapshot: Optional[ClassSnapshot] = None) -> List[ProfessorAction]:
        """
        Process recommendations from the scoring model.
        Returns list of professor actions for this time step.
        """
        actions = []

        for i, rec in enumerate(recommendations):
            priority = rec.get("priority", "medium")

            # Select response distribution based on priority
            if priority == "high":
                dist = self.style.high_priority_response
            elif priority == "medium":
                dist = self.style.medium_priority_response
            else:
                dist = self.style.low_priority_response

            # Sample response category
            category = self._sample_category(dist)

            # Determine intervention type if acting
            intervention_type = None
            if category in ("accept", "modify"):
                intervention_type = self._select_intervention(rec, category)

            # Calculate delay
            delay = random.randint(*self.style.response_delay_range)

            # Don't stack interventions too close together
            if intervention_type and (minute - self._last_intervention_minute) < 3:
                category = "acknowledge"  # Downgrade to acknowledgment
                intervention_type = None

            # Generate rationale
            rationale = self._generate_rationale(category, rec, intervention_type)

            action = ProfessorAction(
                minute=minute + delay,
                recommendation_id=i,
                response_category=category,
                intervention_type=intervention_type,
                rationale=rationale,
                spoken_text=self._generate_spoken_text(category, intervention_type, rec),
                delay_minutes=delay,
            )

            actions.append(action)

            if intervention_type:
                self._last_intervention_minute = minute + delay

        self.actions.extend(actions)
        return actions

    def check_self_initiation(self, class_engagement: float, minute: int) -> Optional[ProfessorAction]:
        """
        Check if the professor would self-initiate an intervention
        without a dashboard recommendation.
        """
        if class_engagement > self.style.self_initiation_threshold:
            return None

        if (minute - self._last_intervention_minute) < 5:
            return None

        # Low engagement triggers self-initiation
        if random.random() < 0.3:  # 30% chance of noticing without dashboard
            intervention = random.choice(["poll", "pace_change", "think_pair_share"])
            action = ProfessorAction(
                minute=minute,
                recommendation_id=None,
                response_category="self_initiated",
                intervention_type=intervention,
                rationale=f"Self-initiated: noticed low engagement ({class_engagement:.2f}), trying {intervention}",
                spoken_text=self._generate_spoken_text("self_initiated", intervention, None),
                delay_minutes=0,
            )
            self.actions.append(action)
            self._last_intervention_minute = minute
            return action

        return None

    def _sample_category(self, distribution: Dict[str, float]) -> str:
        """Sample a response category from the distribution."""
        categories = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(categories, weights=weights, k=1)[0]

    def _select_intervention(self, recommendation: Dict, category: str) -> Optional[str]:
        """Select specific intervention type based on recommendation and style."""
        suggested = RECOMMENDATION_ACTION_MAP.get(
            recommendation.get("action", ""),
            recommendation.get("action", "")
        )

        if category == "accept":
            # Follow recommendation as given
            return suggested or None

        # Modify: choose based on preference
        options = sorted(
            self.style.intervention_preferences.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Weight by preference
        for option, pref in options:
            if random.random() < pref:
                return RECOMMENDATION_ACTION_MAP.get(option, option)

        return suggested or None  # Fallback to recommendation

    def _generate_rationale(self, category: str, recommendation: Dict,
                            intervention_type: Optional[str]) -> str:
        """Generate a human-readable rationale for the professor's action."""
        msg = recommendation.get("message", "")

        rationales = {
            "ignore": [
                "Monitoring situation — not yet ready to intervene",
                "Students may self-correct; waiting to see",
                "Maintaining lecture flow — will address later",
            ],
            "acknowledge": [
                f"Noted: {msg}. Will keep watching.",
                "Aware of the pattern — considering options",
                "Acknowledged the recommendation. Holding for now.",
            ],
            "accept": [
                f"Implementing recommended {intervention_type}",
                f"Good suggestion — running {intervention_type} now",
                f"Agreed with assessment. Launching {intervention_type}.",
            ],
            "modify": [
                f"Adapting recommendation: using {intervention_type} instead",
                f"Modified approach — {intervention_type} fits better here",
                f"Building on suggestion with {intervention_type} for this group",
            ],
            "reject": [
                "Overriding: students need to push through this difficulty",
                "Disagree — the current approach is working for my goals",
                "Context suggests different approach — continuing as planned",
            ],
        }

        options = rationales.get(category, ["Action recorded"])
        return random.choice(options)

    def _generate_spoken_text(self, category: str, intervention_type: Optional[str],
                              recommendation: Optional[Dict]) -> Optional[str]:
        """Generate what the professor would actually say to the class."""
        if category == "ignore":
            return None

        if intervention_type == "clarification":
            return random.choice([
                "Let me pause for a moment and clarify that idea before we move on.",
                "I want to slow down here and re-explain that concept in a simpler way.",
                "Before we keep going, let me clear up what this means in practice.",
            ])

        if intervention_type == "breakout":
            return random.choice([
                "Let's take a short breakout and talk this through in smaller groups, then we'll come back together.",
                "I want to shift us into brief breakout groups so everyone has a chance to process this.",
                "Take a few minutes in breakout rooms to work through this together, then we'll debrief.",
            ])

        if intervention_type == "poll":
            return random.choice([
                "Let me run a quick poll so I can see where everyone is before we continue.",
                "I want to check the room with a fast poll before we move on.",
                "Let's do a quick pulse check with a poll and use that to guide the next step.",
            ])

        if intervention_type == "think_pair_share":
            return random.choice([
                "Take a moment to think on your own, compare with a partner, and then we'll share out.",
                "Let's do a quick think-pair-share so more voices can come into the conversation.",
                "Pause for a minute, talk to a partner, and then we'll bring the ideas back to the full group.",
            ])

        if intervention_type == "pace_change":
            return random.choice([
                "Let's shift gears for a moment and change the pace before we keep going.",
                "I'm going to break the rhythm here and reset how we're approaching this.",
                "Let's pause the lecture flow and switch the pace for a minute so we can re-engage.",
            ])

        if intervention_type == "cold_call":
            return random.choice([
                "I want to bring another voice in here. Who hasn't spoken yet and wants to jump in?",
                "Let's hear from someone we haven't heard from yet.",
                "I'm going to invite a quieter voice into the conversation here.",
            ])

        if category == "acknowledge":
            return random.choice([
                "I'm noticing that pattern too, so I'm going to keep an eye on it as we continue.",
                "I see what's happening here, and I'm going to monitor it for another minute.",
                "That's worth noting. Let me watch it a little more before I intervene.",
            ])

        if category == "reject":
            return random.choice([
                "I'm going to stay the course for the moment and revisit this if needed.",
                "For now, I want to keep the current flow and see if the class self-corrects.",
                "I'm holding the current approach a bit longer before changing direction.",
            ])

        if category == "self_initiated":
            return random.choice([
                "I'm going to step in here and adjust our approach before we continue.",
                "Let me intervene for a moment based on what I'm seeing in the room.",
                "I want to make a quick adjustment here before we move on.",
            ])

        if recommendation and recommendation.get("message"):
            return recommendation["message"]

        return "Let me respond to what I'm seeing in the room before we continue."

    def get_action_summary(self) -> Dict:
        """Summarize professor actions for analysis."""
        if not self.actions:
            return {"total_actions": 0}

        category_counts = {}
        intervention_counts = {}
        for a in self.actions:
            category_counts[a.response_category] = category_counts.get(a.response_category, 0) + 1
            if a.intervention_type:
                intervention_counts[a.intervention_type] = intervention_counts.get(a.intervention_type, 0) + 1

        return {
            "total_actions": len(self.actions),
            "category_distribution": category_counts,
            "interventions_used": intervention_counts,
            "mean_delay": sum(a.delay_minutes for a in self.actions) / len(self.actions),
            "style": self.style.name,
        }


def run_closed_loop(duration: int = 45, professor_style: str = "adaptive",
                    scenario: str = "baseline", seed: Optional[int] = None) -> Dict:
    """
    Run a fully closed-loop simulation: students + scoring + professor.

    Returns complete session data with professor actions integrated.
    """
    from .engine import SimulationEngine

    engine = SimulationEngine(duration=duration, seed=seed, scenario=scenario)
    prof = SimulatedProfessor(style=professor_style)

    session_data = engine.run()

    # Now replay with professor responses
    professor_actions = []
    for entry in session_data["timeline"]:
        minute = entry["minute"]
        class_eng = entry["class_engagement"]

        # Get recommendations for this minute
        recs = [r for r in session_data["recommendations"] if r.get("minute") == minute]

        if recs:
            actions = prof.process_recommendations(recs, minute)
            for a in actions:
                professor_actions.append({
                    "minute": a.minute,
                    "response_category": a.response_category,
                    "intervention_type": a.intervention_type,
                    "rationale": a.rationale,
                    "spoken_text": a.spoken_text,
                    "delay": a.delay_minutes,
                })

        # Check self-initiation
        self_action = prof.check_self_initiation(class_eng, minute)
        if self_action:
            professor_actions.append({
                "minute": self_action.minute,
                "response_category": "self_initiated",
                "intervention_type": self_action.intervention_type,
                "rationale": self_action.rationale,
                "spoken_text": self_action.spoken_text,
                "delay": 0,
            })

    session_data["professor"] = {
        "style": professor_style,
        "actions": professor_actions,
        "summary": prof.get_action_summary(),
    }

    return session_data


def main():
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Closed-loop simulation with simulated professor")
    parser.add_argument("--duration", type=int, default=45)
    parser.add_argument("--style", type=str, default="adaptive",
                        choices=list(PROFESSOR_STYLES.keys()))
    parser.add_argument("--scenario", type=str, default="baseline")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args()

    print(f"Running closed-loop simulation: {args.style} professor, {args.scenario} scenario, {args.duration}min",
          file=sys.stderr)

    result = run_closed_loop(
        duration=args.duration,
        professor_style=args.style,
        scenario=args.scenario,
        seed=args.seed,
    )

    indent = 2 if args.pretty else None
    output = json.dumps(result, indent=indent, default=str)

    if args.output:
        import os
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Session data written to {args.output}", file=sys.stderr)
        print(f"Professor summary: {json.dumps(result['professor']['summary'], indent=2)}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
