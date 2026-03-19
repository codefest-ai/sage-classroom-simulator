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
# CLASS CONTENT TIMELINE
# ============================================================

CONTENT_TIMELINES = {
    "sa_theory": {
        "name": "Situational Awareness Theory (IST 505)",
        "timeline": [
            {"minute": 1, "type": "lecture", "topic": "Introduction to Situational Awareness theory — Endsley's 3-level model", "complexity": "low",
             "instructor_note": "Set the stage. Keep it high-level — don't dive into details yet. Goal: everyone knows there are 3 levels."},
            {"minute": 5, "type": "lecture", "topic": "SA Level 1: Perception — what data do we notice and what do we miss?", "complexity": "medium",
             "instructor_note": "Use the air traffic control example. Ask 'what would YOU notice first?' before revealing the answer."},
            {"minute": 10, "type": "discussion", "topic": "Share an example where you had the data but missed the meaning", "complexity": "low",
             "instructor_note": "Let students talk. Don't correct — collect. If nobody speaks after 30 seconds, share your own example first."},
            {"minute": 15, "type": "lecture", "topic": "SA Level 2: Comprehension — pattern recognition and mental models", "complexity": "high",
             "instructor_note": "This is the hardest concept. Go slow. Check for confusion before advancing. Use the dashboard analogy — seeing numbers vs. understanding what they mean."},
            {"minute": 20, "type": "lecture", "topic": "SA Level 3: Projection — anticipating what happens next from current patterns", "complexity": "high",
             "instructor_note": "If energy is low, skip the formal definition and go straight to the weather forecaster example. Watch for glazed eyes."},
            {"minute": 25, "type": "breakout", "topic": "In groups: design a dashboard that supports all 3 SA levels for a classroom instructor", "complexity": "medium",
             "instructor_note": "Groups of 3-4. Walk around and check in. Don't let any group stall — give them a starter if needed: 'What would SA Level 1 look like for a teacher?'"},
            {"minute": 32, "type": "presentation", "topic": "Group presentations: share your dashboard designs", "complexity": "low",
             "instructor_note": "Keep to 2 min per group. After each, ask ONE question that connects back to the 3 levels. Don't critique — connect."},
            {"minute": 38, "type": "discussion", "topic": "What trade-offs did you make between showing more data vs. keeping it simple?", "complexity": "medium",
             "instructor_note": "This is the bridge to cognitive load theory. Let them discover the tension themselves before naming it."},
            {"minute": 42, "type": "lecture", "topic": "Cognitive load theory — why more information can reduce SA", "complexity": "high",
             "instructor_note": "Short and punchy — they're tired. One key idea: 'More data can mean less understanding.' Connect to their dashboard designs."},
            {"minute": 45, "type": "wrapup", "topic": "Key takeaways and preview of next week: evaluation methods", "complexity": "low",
             "instructor_note": "One sentence per takeaway. Preview next week. End on time — respect the clock."},
        ],
    },
    "dsr_methods": {
        "name": "Design Science Research Methods (IST 505)",
        "timeline": [
            {"minute": 1, "type": "lecture", "topic": "What is Design Science Research? Hevner's 3-cycle model", "complexity": "low"},
            {"minute": 6, "type": "lecture", "topic": "DSR vs. behavioral research — when do you build an artifact?", "complexity": "medium"},
            {"minute": 12, "type": "discussion", "topic": "Think of a problem you've encountered. Is it a DSR problem or a behavioral one?", "complexity": "low"},
            {"minute": 17, "type": "lecture", "topic": "Artifact types: constructs, models, methods, instantiations", "complexity": "high"},
            {"minute": 22, "type": "lecture", "topic": "FEDS framework — formative vs. summative evaluation", "complexity": "high"},
            {"minute": 27, "type": "breakout", "topic": "In pairs: define a DSR problem and sketch an artifact + evaluation plan", "complexity": "medium"},
            {"minute": 34, "type": "presentation", "topic": "Share your DSR problem + artifact + evaluation approach", "complexity": "low"},
            {"minute": 40, "type": "discussion", "topic": "What makes an evaluation 'rigorous enough'? When do you stop iterating?", "complexity": "medium"},
            {"minute": 45, "type": "wrapup", "topic": "Next week: your group projects — scope and artifact definition due", "complexity": "low"},
        ],
    },
    "data_ethics": {
        "name": "Data Ethics & AI Governance",
        "timeline": [
            {"minute": 1, "type": "lecture", "topic": "Algorithmic bias: how training data encodes historical discrimination", "complexity": "medium"},
            {"minute": 8, "type": "discussion", "topic": "Have you ever experienced or witnessed algorithmic bias? What happened?", "complexity": "low"},
            {"minute": 13, "type": "lecture", "topic": "Fairness metrics: demographic parity, equalized odds, individual fairness", "complexity": "high"},
            {"minute": 20, "type": "lecture", "topic": "The impossibility theorem — you can't satisfy all fairness criteria simultaneously", "complexity": "high"},
            {"minute": 25, "type": "breakout", "topic": "Case study: a hiring algorithm rejects candidates from certain zip codes. What do you do?",  "complexity": "medium"},
            {"minute": 33, "type": "presentation", "topic": "Group solutions to the hiring algorithm case", "complexity": "low"},
            {"minute": 38, "type": "discussion", "topic": "Who should be responsible — the developer, the company, or the regulator?", "complexity": "medium"},
            {"minute": 43, "type": "lecture", "topic": "EU AI Act and emerging governance frameworks", "complexity": "medium"},
            {"minute": 45, "type": "wrapup", "topic": "Reflection: where does your own work intersect with these issues?", "complexity": "low"},
        ],
    },
    "hci_dashboards": {
        "name": "HCI & Dashboard Design",
        "timeline": [
            {"minute": 1, "type": "lecture", "topic": "Principles of information visualization — Tufte, Few, Munzner", "complexity": "low"},
            {"minute": 7, "type": "lecture", "topic": "Cognitive load in dashboards — when more data means less understanding", "complexity": "medium"},
            {"minute": 12, "type": "discussion", "topic": "Show the worst dashboard you've ever used. What made it bad?", "complexity": "low"},
            {"minute": 17, "type": "lecture", "topic": "The data-ink ratio and principle of proportional ink", "complexity": "medium"},
            {"minute": 22, "type": "lecture", "topic": "Color theory for data: sequential, diverging, categorical palettes", "complexity": "high"},
            {"minute": 27, "type": "breakout", "topic": "Redesign the 'bad dashboard' examples using the principles discussed", "complexity": "medium"},
            {"minute": 35, "type": "presentation", "topic": "Before/after dashboard redesigns — what changed and why", "complexity": "low"},
            {"minute": 40, "type": "discussion", "topic": "When should a dashboard show less? When does simplification become distortion?", "complexity": "medium"},
            {"minute": 45, "type": "wrapup", "topic": "Next week: user testing your dashboard prototypes", "complexity": "low"},
        ],
    },
    "lecture_heavy": {
        "name": "Pure Lecture (Stress Test)",
        "timeline": [
            {"minute": 1, "type": "lecture", "topic": "Introduction to the topic", "complexity": "low"},
            {"minute": 8, "type": "lecture", "topic": "Core concepts and theoretical framework", "complexity": "medium"},
            {"minute": 16, "type": "lecture", "topic": "Advanced concepts building on the framework", "complexity": "high"},
            {"minute": 24, "type": "lecture", "topic": "Case studies and applications", "complexity": "high"},
            {"minute": 32, "type": "lecture", "topic": "Implications and open questions", "complexity": "medium"},
            {"minute": 40, "type": "lecture", "topic": "Summary and review", "complexity": "low"},
            {"minute": 45, "type": "wrapup", "topic": "Questions?", "complexity": "low"},
        ],
    },
    "active_learning": {
        "name": "Active Learning (Best Practice)",
        "timeline": [
            {"minute": 1, "type": "lecture", "topic": "Brief framing: today's question and why it matters", "complexity": "low"},
            {"minute": 5, "type": "discussion", "topic": "Quick round: what do you already know or assume about this topic?", "complexity": "low"},
            {"minute": 10, "type": "lecture", "topic": "Key concept #1 with worked example", "complexity": "medium"},
            {"minute": 15, "type": "breakout", "topic": "Apply concept #1 to a new scenario in pairs", "complexity": "medium"},
            {"minute": 20, "type": "presentation", "topic": "Pairs share their solutions — quick 1-minute each", "complexity": "low"},
            {"minute": 24, "type": "lecture", "topic": "Key concept #2 — builds on #1", "complexity": "high"},
            {"minute": 29, "type": "discussion", "topic": "Where does concept #2 break down? What are the edge cases?", "complexity": "medium"},
            {"minute": 34, "type": "breakout", "topic": "Groups: design something using both concepts", "complexity": "medium"},
            {"minute": 40, "type": "presentation", "topic": "Group showcase + peer feedback", "complexity": "low"},
            {"minute": 44, "type": "discussion", "topic": "What surprised you today? What's still unclear?", "complexity": "low"},
            {"minute": 45, "type": "wrapup", "topic": "One-sentence takeaway from each student", "complexity": "low"},
        ],
    },
}

DEFAULT_CONTENT_TIMELINE = CONTENT_TIMELINES["sa_theory"]["timeline"]

# How each content type modifies engagement per archetype tendency
CONTENT_TYPE_MODIFIERS = {
    "lecture":       {"engaged": 0.0, "builder": -0.15, "reflective": 0.05, "collaborative": -0.05, "withdrawn": -0.10},
    "discussion":    {"engaged": 0.10, "builder": 0.05, "reflective": -0.05, "collaborative": 0.15, "withdrawn": -0.15},
    "breakout":      {"engaged": 0.10, "builder": 0.15, "reflective": 0.0, "collaborative": 0.20, "withdrawn": -0.10},
    "presentation":  {"engaged": 0.05, "builder": 0.0, "reflective": 0.10, "collaborative": 0.10, "withdrawn": -0.20},
    "wrapup":        {"engaged": 0.0, "builder": 0.0, "reflective": 0.05, "collaborative": 0.0, "withdrawn": 0.0},
}

def get_content_at_minute(timeline, minute):
    """Get the active content block for a given minute."""
    current = None
    for block in timeline:
        if block["minute"] <= minute:
            current = block
        else:
            break
    return current


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
                 use_llm: bool = False, use_claude: bool = False,
                 content_timeline: Optional[List[Dict]] = None):
        self.duration = duration
        self.scenario = SCENARIOS.get(scenario, SCENARIOS["baseline"])
        self.content_timeline = content_timeline or DEFAULT_CONTENT_TIMELINE
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
                self._llm_client = LLMClient(use_claude=use_claude)
                for p in self.profiles:
                    agent = StudentAgent(p, self._llm_client)
                    agent.set_affinity_peers(self.profiles)
                    self._student_agents[p.student_id] = agent
            except ImportError:
                self.use_llm = False

        # Room context for LLM agents — seed with professor opening
        # Rotate topics so students don't always discuss SAGE itself
        _topics = [
            ("Today we're exploring situational awareness theory — how people perceive, comprehend, and project information in complex environments.", "What's an example from your own experience where situational awareness failed — where someone had the data but missed the meaning?"),
            ("Let's discuss learning analytics and how institutions use data to understand student behavior.", "When you think about your own learning — what signals would actually tell an observer whether you're engaged or checked out?"),
            ("Today's topic is design science research methodology — building artifacts that solve real problems and evaluating whether they work.", "What makes an artifact 'good enough' to evaluate? When do you stop building and start testing?"),
            ("We're looking at cognitive load theory today — how the design of information systems affects what people can actually process.", "Think about a tool you use regularly. Where does it create unnecessary cognitive load, and where does it reduce it?"),
            ("Let's explore human-computer interaction and dashboard design — how do you present complex data so people can act on it?", "What's the worst dashboard or data display you've ever seen, and what made it bad?"),
        ]
        _topic = _topics[random.randint(0, len(_topics) - 1)]
        self._room_context: List[Dict] = [
            {
                "student_id": "PROF",
                "name": "Professor",
                "text": f"Welcome everyone. {_topic[0]}",
                "minute": 0,
            },
            {
                "student_id": "PROF",
                "name": "Professor",
                "text": _topic[1],
                "minute": 0,
            },
        ]

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

            # Inject content transitions into room context
            content_block = get_content_at_minute(self.content_timeline, minute)
            if content_block and content_block.get("minute") == minute:
                self._room_context.append({
                    "student_id": "PROF",
                    "name": "Professor",
                    "text": f"[{content_block['type'].upper()}] {content_block['topic']}",
                    "minute": minute,
                })

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

                # LLM combined call — agent decides BOTH engagement and chat
                content_block = get_content_at_minute(self.content_timeline, minute)
                llm_eligible = self.use_llm and llm_chat_count < 8 and (
                    signals.chat_sent or random.random() < 0.45
                )
                if llm_eligible:
                    agent = self._student_agents.get(profile.student_id)
                    if agent:
                        professor_speech = None
                        for ev in self.events:
                            if hasattr(ev, 'minute') and ev.minute == minute and ev.event_type == "intervention":
                                professor_speech = ev.data.get("name", "")
                        if not professor_speech:
                            prof_msgs = [m for m in self._room_context if m.get("student_id") == "PROF"]
                            if prof_msgs:
                                professor_speech = prof_msgs[-1].get("text", "")

                        result = agent.generate_state_and_chat(
                            current_engagement=engagement,
                            room_context=self._room_context[-10:],
                            content_block=content_block,
                            professor_action=professor_speech,
                            active_intervention=active_intervention,
                            minutes_elapsed=minute,
                        )

                        # LLM decides engagement — override the formula
                        engagement = result["engagement"]
                        llm_text = result["chat"]

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
