"""
Classroom Simulator Engine — Runs N-minute class sessions with AI student agents.

Entry point for the simulation. Generates timestamped engagement data streams
that the instructor dashboard consumes.

v2: Added step() generator for live streaming, university presets, LLM toggle.

Usage:
    python3 -m simulator.engine --duration 45 --output data/session.json
    python3 -m simulator.engine --scenario confusion_cluster --seed 42
    python3 -m simulator.engine --intervention 20:breakout --intervention 35:poll
    python3 -m simulator.engine --university gatech --llm --live
"""

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Generator

from .profiles import STUDENT_PROFILES, StudentProfile, get_profiles
from .scoring import EngagementScorer, SignalSnapshot, ClassSnapshot
from .nlp import ChatAnalyzer


# ============================================================
# INTERVENTION TYPES
# ============================================================

INTERVENTION_TYPES = {
    "breakout": {
        "name": "Breakout Rooms",
        "duration_minutes": 5,
        "description": "Small group activity (3-4 students per room)",
    },
    "poll": {
        "name": "Quick Poll",
        "duration_minutes": 2,
        "description": "Multiple choice or open-ended poll question",
    },
    "cold_call": {
        "name": "Cold Call",
        "duration_minutes": 1,
        "description": "Directly calling on a specific student",
        "target_student": None,  # Set at runtime
    },
    "pace_change": {
        "name": "Pace Change",
        "duration_minutes": 0,
        "description": "Switch from lecture to discussion or vice versa",
    },
    "think_pair_share": {
        "name": "Think-Pair-Share",
        "duration_minutes": 3,
        "description": "Individual reflection → partner discussion → class share",
    },
}


# ============================================================
# SCENARIOS
# ============================================================

SCENARIOS = {
    "baseline": {
        "description": "Normal class session with natural engagement variation",
        "interventions": [],
        "overrides": {},
    },
    "energy_decay": {
        "description": "Long lecture with no activities — tests energy decay detection",
        "interventions": [],
        "overrides": {
            "global_drift_multiplier": 1.5,
        },
    },
    "equity_imbalance": {
        "description": "Two students dominate discussion — tests equity detection",
        "interventions": [],
        "overrides": {
            "boost_students": ["S13", "S02"],  # The Dominator + Marcus
            "boost_speak": 0.6,
            "suppress_others_speak": 0.03,
        },
    },
    "confusion_cluster": {
        "description": "Difficult topic at minute 20 triggers widespread confusion",
        "interventions": [],
        "overrides": {
            "confusion_spike_minute": 20,
            "confusion_spike_strength": 0.4,
        },
    },
    "intervention_test": {
        "description": "Baseline with breakout at min 20 and poll at min 35",
        "interventions": [
            {"minute": 20, "type": "breakout"},
            {"minute": 35, "type": "poll"},
        ],
        "overrides": {},
    },
    "full_scenario": {
        "description": "Energy decay + confusion + intervention responses",
        "interventions": [
            {"minute": 25, "type": "breakout"},
            {"minute": 40, "type": "poll"},
        ],
        "overrides": {
            "global_drift_multiplier": 1.3,
            "confusion_spike_minute": 18,
            "confusion_spike_strength": 0.3,
        },
    },
}


@dataclass
class Intervention:
    """An instructor intervention event."""
    minute: int
    intervention_type: str
    target_student: Optional[str] = None
    data: Optional[Dict] = None


@dataclass
class SimulationEvent:
    """A single event in the simulation timeline."""
    minute: int
    event_type: str  # "signal", "chat", "intervention", "pattern", "recommendation"
    student_id: Optional[str]
    data: Dict


class SimulationEngine:
    """
    Runs a classroom simulation session.

    For each time step (1 minute):
    1. Each student agent generates engagement signals per their profile
    2. Signals are scored by the EngagementScorer
    3. Chat messages are analyzed by the ChatAnalyzer
    4. Interventions are applied if scheduled
    5. Class-level patterns are detected
    6. Recommendations are generated
    """

    def __init__(self, duration: int = 45, seed: Optional[int] = None,
                 scenario: str = "baseline", university: str = "",
                 use_llm: bool = False):
        self.duration = duration
        self.scenario = SCENARIOS.get(scenario, SCENARIOS["baseline"])
        self.scorer = EngagementScorer()
        self.chat_analyzer = ChatAnalyzer()
        self.events: List[SimulationEvent] = []
        self.interventions: List[Intervention] = []
        self._active_interventions: List[Intervention] = []
        self._last_class_snapshot: Optional[ClassSnapshot] = None
        self.use_llm = use_llm

        # Per-student engagement state (modified by interventions)
        self._engagement_boosts: Dict[str, float] = {}

        if seed is not None:
            random.seed(seed)

        # Load profiles — university preset or default
        if university:
            from .university_presets import generate_preset_profiles
            preset_data = generate_preset_profiles(university, seed=seed or 42)
            self.profiles = []
            for pd in preset_data:
                sp = StudentProfile(
                    name=pd["name"],
                    student_id=pd["student_id"],
                    demographic=pd["demographic"],
                    engagement_baseline=pd["engagement_baseline"],
                    chat_frequency=pd["chat_frequency"],
                    camera_on_rate=pd["camera_on_rate"],
                    speak_tendency=pd["speak_tendency"],
                    reaction_rate=pd["reaction_rate"],
                    poll_response_rate=pd["poll_response_rate"],
                    attention_span_minutes=pd["attention_span_minutes"],
                    drift_rate=pd["drift_rate"],
                    recovery_rate=pd["recovery_rate"],
                    confusion_threshold=pd["confusion_threshold"],
                    breakout_response=pd["breakout_response"],
                    poll_response=pd["poll_response"],
                    cold_call_response=pd["cold_call_response"],
                    pace_change_response=pd["pace_change_response"],
                )
                sp.archetype = pd.get("archetype", "")
                self.profiles.append(sp)
        else:
            self.profiles = get_profiles()

        # LLM student agents (optional)
        self._student_agents: Dict[str, 'StudentAgent'] = {}
        self._llm_client = None
        if use_llm:
            try:
                from .llm_client import LLMClient
                from .student_agent import StudentAgent
                self._llm_client = LLMClient()
                for p in self.profiles:
                    agent = StudentAgent(p, self._llm_client)
                    agent.set_affinity_peers(self.profiles)
                    self._student_agents[p.student_id] = agent
            except ImportError:
                self.use_llm = False

        # Room context for LLM agents
        self._room_context: List[Dict] = []

        # Load scenario interventions
        for iv in self.scenario.get("interventions", []):
            self.interventions.append(Intervention(
                minute=iv["minute"],
                intervention_type=iv["type"],
                target_student=iv.get("target_student"),
            ))

    def add_intervention(self, minute: int, intervention_type: str,
                         target_student: Optional[str] = None):
        """Schedule an intervention at a specific minute."""
        self.interventions.append(Intervention(
            minute=minute,
            intervention_type=intervention_type,
            target_student=target_student,
        ))

    def run(self) -> Dict:
        """
        Execute the full simulation.
        Returns a complete session data structure.
        """
        session_data = {
            "metadata": {
                "duration_minutes": self.duration,
                "scenario": self.scenario.get("description", "custom"),
                "student_count": len(self.profiles),
                "interventions_planned": len(self.interventions),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "students": [
                {
                    "student_id": p.student_id,
                    "name": p.name,
                    "engagement_baseline": p.engagement_baseline,
                    "demographic": p.demographic,
                }
                for p in self.profiles
            ],
            "timeline": [],
            "class_snapshots": [],
            "events": [],
            "recommendations": [],
        }

        overrides = self.scenario.get("overrides", {})

        for minute in range(1, self.duration + 1):
            # Check for scheduled interventions
            for iv in self.interventions:
                if iv.minute == minute:
                    self._apply_intervention(iv, minute)

            # Check for confusion spike (scenario override)
            confusion_active = False
            if overrides.get("confusion_spike_minute") and minute >= overrides["confusion_spike_minute"]:
                minutes_since = minute - overrides["confusion_spike_minute"]
                if minutes_since < 8:  # Confusion lasts ~8 minutes
                    confusion_active = True

            # Generate signals for each student
            student_scores = []
            minute_events = []

            for profile in self.profiles:
                # Calculate engagement for this minute
                drift_mult = overrides.get("global_drift_multiplier", 1.0)
                effective_profile = profile

                # Scenario overrides
                speak_override = None
                if overrides.get("boost_students") and profile.student_id in overrides["boost_students"]:
                    speak_override = overrides.get("boost_speak", profile.speak_tendency)
                elif overrides.get("suppress_others_speak") is not None and \
                     overrides.get("boost_students") and \
                     profile.student_id not in overrides["boost_students"]:
                    speak_override = overrides["suppress_others_speak"]

                engagement = profile.get_engagement_at(
                    minute * drift_mult,
                    noise=0.08
                )

                # Apply confusion spike
                if confusion_active:
                    spike_strength = overrides.get("confusion_spike_strength", 0.3)
                    engagement -= spike_strength * random.uniform(0.5, 1.0)
                    engagement = max(0.05, engagement)

                # Apply intervention boosts
                boost = self._engagement_boosts.get(profile.student_id, 0.0)
                engagement = min(1.0, engagement + boost)

                # Decay boosts
                if profile.student_id in self._engagement_boosts:
                    self._engagement_boosts[profile.student_id] *= 0.85

                # Generate signals
                signals = self._generate_signals(profile, minute, engagement, speak_override)
                score = self.scorer.score_student(signals, engagement)
                student_scores.append(score)

                # Generate chat message if applicable
                if signals.chat_sent and signals.chat_text:
                    chat_analysis = self.chat_analyzer.analyze_message(
                        profile.student_id, minute, signals.chat_text
                    )
                    minute_events.append(SimulationEvent(
                        minute=minute,
                        event_type="chat",
                        student_id=profile.student_id,
                        data={
                            "text": signals.chat_text,
                            "confusion_score": chat_analysis.confusion_score,
                            "sentiment": chat_analysis.sentiment,
                            "is_question": chat_analysis.is_question,
                        }
                    ))

            # Score the class
            class_snapshot = self.scorer.score_class(student_scores, minute)

            # Generate recommendations
            recommendations = self.scorer.get_recommendations(class_snapshot)

            # Store data
            timeline_entry = {
                "minute": minute,
                "class_engagement": class_snapshot.mean_engagement,
                "engagement_std": class_snapshot.std_engagement,
                "speaking_gini": class_snapshot.speaking_gini,
                "active_speakers": class_snapshot.active_speakers,
                "patterns": class_snapshot.patterns_detected,
                "students": [
                    {
                        "student_id": s.student_id,
                        "engagement": s.weighted_index,
                        "state": s.state,
                        "is_confused": s.is_confused,
                        "signals": s.contributing_signals,
                    }
                    for s in student_scores
                ],
            }

            session_data["timeline"].append(timeline_entry)
            session_data["events"].extend([asdict(e) for e in minute_events])

            if recommendations:
                for rec in recommendations:
                    rec["minute"] = minute
                    session_data["recommendations"].append(rec)

        # Final summary
        session_data["summary"] = self._generate_summary()

        return session_data

    def step(self) -> Generator[Dict, None, None]:
        """
        Generator that yields one frame per minute — for live streaming.

        Each frame has the same structure as a timeline entry from run().
        """
        overrides = self.scenario.get("overrides", {})

        for minute in range(1, self.duration + 1):
            # Check for scheduled interventions
            active_intervention = None
            for iv in self.interventions:
                if iv.minute == minute:
                    self._apply_intervention(iv, minute)
                    active_intervention = iv.intervention_type

            # Check for confusion spike
            confusion_active = False
            if overrides.get("confusion_spike_minute") and minute >= overrides["confusion_spike_minute"]:
                minutes_since = minute - overrides["confusion_spike_minute"]
                if minutes_since < 8:
                    confusion_active = True

            student_scores = []
            minute_events = []
            llm_chat_count = 0

            for profile in self.profiles:
                drift_mult = overrides.get("global_drift_multiplier", 1.0)

                speak_override = None
                if overrides.get("boost_students") and profile.student_id in overrides["boost_students"]:
                    speak_override = overrides.get("boost_speak", profile.speak_tendency)
                elif overrides.get("suppress_others_speak") is not None and \
                     overrides.get("boost_students") and \
                     profile.student_id not in overrides["boost_students"]:
                    speak_override = overrides["suppress_others_speak"]

                engagement = profile.get_engagement_at(minute * drift_mult, noise=0.08)

                if confusion_active:
                    spike_strength = overrides.get("confusion_spike_strength", 0.3)
                    engagement -= spike_strength * random.uniform(0.5, 1.0)
                    engagement = max(0.05, engagement)

                boost = self._engagement_boosts.get(profile.student_id, 0.0)
                engagement = min(1.0, engagement + boost)

                if profile.student_id in self._engagement_boosts:
                    self._engagement_boosts[profile.student_id] *= 0.85

                signals = self._generate_signals(profile, minute, engagement, speak_override)

                # LLM chat override (max 5 per tick for speed)
                if self.use_llm and signals.chat_sent and llm_chat_count < 5:
                    agent = self._student_agents.get(profile.student_id)
                    if agent:
                        is_confused = engagement < profile.confusion_threshold
                        professor_speech = None
                        for ev in self.events:
                            if hasattr(ev, 'minute') and ev.minute == minute and ev.event_type == "intervention":
                                professor_speech = ev.data.get("name", "")
                        llm_text = agent.generate_chat(
                            engagement=engagement,
                            room_context=self._room_context[-10:],
                            professor_action=professor_speech,
                            active_intervention=active_intervention,
                            is_confused=is_confused,
                        )
                        if llm_text:
                            signals = SignalSnapshot(
                                student_id=signals.student_id,
                                minute=signals.minute,
                                speaking=signals.speaking,
                                speaking_duration_sec=signals.speaking_duration_sec,
                                chat_sent=True,
                                chat_text=llm_text,
                                poll_responded=signals.poll_responded,
                                reaction_sent=signals.reaction_sent,
                                reaction_type=signals.reaction_type,
                                camera_on=signals.camera_on,
                                silence_duration_sec=signals.silence_duration_sec,
                            )
                            llm_chat_count += 1

                score = self.scorer.score_student(signals, engagement)
                student_scores.append(score)

                if signals.chat_sent and signals.chat_text:
                    chat_analysis = self.chat_analyzer.analyze_message(
                        profile.student_id, minute, signals.chat_text
                    )
                    minute_events.append(SimulationEvent(
                        minute=minute,
                        event_type="chat",
                        student_id=profile.student_id,
                        data={
                            "text": signals.chat_text,
                            "confusion_score": chat_analysis.confusion_score,
                            "sentiment": chat_analysis.sentiment,
                            "is_question": chat_analysis.is_question,
                        }
                    ))
                    # Update room context for LLM agents
                    self._room_context.append({
                        "student_id": profile.student_id,
                        "name": profile.name,
                        "text": signals.chat_text,
                        "minute": minute,
                    })
                    # Keep room context bounded
                    if len(self._room_context) > 30:
                        self._room_context = self._room_context[-20:]

            class_snapshot = self.scorer.score_class(student_scores, minute)
            self._last_class_snapshot = class_snapshot
            self.events.extend(minute_events)

            frame = {
                "minute": minute,
                "class_engagement": class_snapshot.mean_engagement,
                "engagement_std": class_snapshot.std_engagement,
                "speaking_gini": class_snapshot.speaking_gini,
                "active_speakers": class_snapshot.active_speakers,
                "patterns": class_snapshot.patterns_detected,
                "students": [
                    {
                        "student_id": s.student_id,
                        "engagement": s.weighted_index,
                        "state": s.state,
                        "is_confused": s.is_confused,
                        "signals": s.contributing_signals,
                    }
                    for s in student_scores
                ],
            }

            yield frame

    def _generate_signals(self, profile: StudentProfile, minute: int,
                          engagement: float, speak_override: Optional[float] = None) -> SignalSnapshot:
        """Generate engagement signals for one student at one time step."""
        speak_prob = speak_override if speak_override is not None else profile.speak_tendency
        speaking = random.random() < speak_prob * engagement
        speaking_duration = random.uniform(5, 45) if speaking else 0.0

        chat_sent = random.random() < profile.chat_frequency * (0.5 + 0.5 * engagement)
        chat_text = ""
        if chat_sent:
            chat_text = self._generate_chat(profile, engagement)

        poll_responded = random.random() < profile.poll_response_rate
        camera_on = random.random() < profile.camera_on_rate * (0.7 + 0.3 * engagement)
        reaction_sent = random.random() < profile.reaction_rate * engagement

        silence = 0.0 if (speaking or chat_sent or reaction_sent) else random.uniform(30, 90)

        return SignalSnapshot(
            student_id=profile.student_id,
            minute=minute,
            speaking=speaking,
            speaking_duration_sec=speaking_duration,
            chat_sent=chat_sent,
            chat_text=chat_text,
            poll_responded=poll_responded,
            reaction_sent=reaction_sent,
            reaction_type=random.choice(["thumbs_up", "heart", "clap", "laugh", "raised_hand"]) if reaction_sent else "",
            camera_on=camera_on,
            silence_duration_sec=silence,
        )

    def _generate_chat(self, profile: StudentProfile, engagement: float) -> str:
        """Generate a chat message based on profile and engagement state."""
        templates = profile.chat_templates
        if not templates:
            return ""

        # Pick template category based on engagement
        if engagement >= 0.65 and templates.get("engaged"):
            candidates = templates["engaged"]
        elif engagement >= 0.35 and templates.get("drifting"):
            candidates = templates["drifting"]
        elif templates.get("confused"):
            candidates = templates["confused"]
        else:
            candidates = templates.get("engaged", [""])

        if not candidates:
            return ""

        template = random.choice(candidates)

        # Fill in placeholders
        substitutions = {
            "{topic}": random.choice(["engagement metrics", "SA theory", "the evaluation method",
                                       "cognitive load", "breakout rooms", "the dashboard design"]),
            "{concept}": random.choice(["situational awareness", "cognitive load theory",
                                         "the scoring model", "learning analytics", "UDL"]),
            "{peer}": random.choice([p.name.split()[0] for p in self.profiles if p.student_id != profile.student_id]),
            "{observation}": random.choice(["the pattern shifts after intervention",
                                              "the engagement data shows decay",
                                              "this validates the hypothesis"]),
            "{domain}": random.choice(["healthcare", "education", "my program", "UX", "data science"]),
            "{reason}": random.choice(["the sample size is too small",
                                        "this doesn't account for cultural factors",
                                        "the methodology is sound but narrow"]),
            "{tech}": random.choice(["Python", "React", "TensorFlow", "D3.js"]),
            "{method}": random.choice(["agile sprints", "user testing", "A/B experiments"]),
            "{context}": random.choice(["a team of 20", "a school district", "my capstone"]),
            "{point}": random.choice(["unclear", "worth exploring", "debatable"]),
            "{n}": str(random.randint(5, 25)),
            "{insight}": random.choice(["nonlinear decay", "threshold effects", "group dynamics"]),
            "{term}": random.choice(["Gini coefficient", "SA Level 3", "extraneous load"]),
            "{metaphor}": random.choice(["a dashboard", "a control room", "a game"]),
            "{interpretation}": random.choice(["SA degrades under load",
                                                 "advisors outperform mirrors",
                                                 "instructors need comprehension support"]),
            "{a}": "the descriptive view",
            "{b}": "the prescriptive view",
            "{extension}": "how this scales to async",
            "{claim}": "one-size-fits-all works",
            "{concept_a}": "cognitive load",
            "{concept_b}": "situational awareness",
        }

        for key, value in substitutions.items():
            template = template.replace(key, value)

        return template

    def _apply_intervention(self, intervention: Intervention, minute: int):
        """Apply an intervention's effects to student engagement."""
        itype = intervention.intervention_type

        self.events.append(SimulationEvent(
            minute=minute,
            event_type="intervention",
            student_id=None,
            data={
                "type": itype,
                "name": INTERVENTION_TYPES.get(itype, {}).get("name", itype),
                "target_student": intervention.target_student,
            }
        ))

        for profile in self.profiles:
            if itype == "breakout":
                boost = profile.breakout_response * random.uniform(0.7, 1.3)
            elif itype == "poll":
                boost = profile.poll_response * random.uniform(0.7, 1.3)
            elif itype == "cold_call":
                if intervention.target_student == profile.student_id:
                    boost = profile.cold_call_response
                else:
                    boost = 0.02  # Slight engagement from watching
            elif itype == "pace_change":
                boost = profile.pace_change_response * random.uniform(0.5, 1.5)
            elif itype == "think_pair_share":
                boost = (profile.breakout_response + profile.poll_response) / 2
            else:
                boost = 0.0

            current = self._engagement_boosts.get(profile.student_id, 0.0)
            self._engagement_boosts[profile.student_id] = current + boost

    def _generate_summary(self) -> Dict:
        """Generate session summary statistics."""
        history = self.scorer.get_history()
        if not history:
            return {}

        all_engagements = [h.mean_engagement for h in history]
        peak_minute = max(range(len(all_engagements)), key=lambda i: all_engagements[i]) + 1
        trough_minute = min(range(len(all_engagements)), key=lambda i: all_engagements[i]) + 1

        # Per-student summary
        student_summaries = {}
        for profile in self.profiles:
            student_data = []
            for h in history:
                for s in h.student_scores:
                    if s.student_id == profile.student_id:
                        student_data.append(s.weighted_index)
            if student_data:
                student_summaries[profile.student_id] = {
                    "name": profile.name,
                    "mean_engagement": round(sum(student_data) / len(student_data), 3),
                    "min_engagement": round(min(student_data), 3),
                    "max_engagement": round(max(student_data), 3),
                }

        # Pattern frequency
        pattern_counts: Dict[str, int] = {}
        for h in history:
            for p in h.patterns_detected:
                ptype = p["type"]
                pattern_counts[ptype] = pattern_counts.get(ptype, 0) + 1

        return {
            "overall_mean_engagement": round(sum(all_engagements) / len(all_engagements), 3),
            "peak_minute": peak_minute,
            "peak_engagement": round(all_engagements[peak_minute - 1], 3),
            "trough_minute": trough_minute,
            "trough_engagement": round(all_engagements[trough_minute - 1], 3),
            "engagement_range": round(max(all_engagements) - min(all_engagements), 3),
            "pattern_frequency": pattern_counts,
            "student_summaries": student_summaries,
            "total_interventions": len(self.interventions),
            "total_recommendations": len([e for e in self.events if e.event_type == "recommendation"]),
            "confusion_timeline": self.chat_analyzer.get_confusion_timeline(),
        }


def main():
    parser = argparse.ArgumentParser(
        description="SAGE — Simulated Agent-Generated Engagement"
    )
    parser.add_argument("--duration", type=int, default=45,
                        help="Session duration in minutes (default: 45)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON file (default: stdout)")
    parser.add_argument("--scenario", type=str, default="baseline",
                        choices=list(SCENARIOS.keys()),
                        help="Predefined scenario (default: baseline)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--intervention", type=str, action="append", default=[],
                        help="Intervention as MIN:TYPE (e.g., 20:breakout)")
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty-print JSON output")
    parser.add_argument("--university", type=str, default="",
                        choices=["", "cgu", "gatech", "howard"],
                        help="University demographic preset")
    parser.add_argument("--llm", action="store_true",
                        help="Enable LLM-powered student chat (requires MLX server)")
    parser.add_argument("--live", action="store_true",
                        help="Stream frames to stdout (for server mode)")

    args = parser.parse_args()

    # Create engine
    engine = SimulationEngine(
        duration=args.duration,
        seed=args.seed,
        scenario=args.scenario,
        university=args.university,
        use_llm=args.llm,
    )

    # Parse interventions
    for iv_str in args.intervention:
        parts = iv_str.split(":")
        if len(parts) >= 2:
            minute = int(parts[0])
            itype = parts[1]
            target = parts[2] if len(parts) > 2 else None
            engine.add_intervention(minute, itype, target)

    # Run simulation
    mode = "live" if args.live else "batch"
    uni_label = f", {args.university} preset" if args.university else ""
    llm_label = ", LLM-powered" if args.llm else ""
    print(f"Running {args.duration}-minute simulation ({args.scenario}{uni_label}{llm_label}, {mode})...",
          file=sys.stderr)

    if args.live:
        # Stream mode: yield JSON frames to stdout
        for frame in engine.step():
            print(json.dumps(frame, default=str))
            sys.stdout.flush()
        print("Simulation complete.", file=sys.stderr)
        return

    result = engine.run()

    # Output
    indent = 2 if args.pretty else None
    output = json.dumps(result, indent=indent, default=str)

    if args.output:
        import os
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Session data written to {args.output}", file=sys.stderr)
        print(f"Summary: {json.dumps(result.get('summary', {}), indent=2)}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
