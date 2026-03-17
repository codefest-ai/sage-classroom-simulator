"""
Student Agent Profiles — 15 AI students with distinct behavioral signatures.

Each profile is grounded in the Phase 2 literature:
- Behavioral archetypes from Kauffman (2019) learner population differences
- Participation patterns from Dell et al. (2015) UDL/diverse participation
- Engagement variability informed by Li et al. (2025) instructor analytics use

Profiles are parameterized dictionaries. The simulator engine reads these
and generates timestamped engagement signals accordingly.
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class StudentProfile:
    """A single student agent's behavioral configuration."""

    # Identity
    name: str
    student_id: str
    demographic: Dict  # age, major, learning_style, tech_comfort

    # Engagement baseline
    engagement_baseline: str  # "high", "medium", "low"
    engagement_score: float = 0.5  # 0.0-1.0, current engagement level

    # Behavioral parameters (all 0.0-1.0 probability per time step)
    chat_frequency: float = 0.1      # Probability of sending a chat message
    camera_on_rate: float = 0.5      # Probability camera stays on
    speak_tendency: float = 0.1      # Probability of unmuting to speak
    reaction_rate: float = 0.1       # Probability of using emoji reactions
    poll_response_rate: float = 0.7  # Probability of answering polls

    # Drift and attention
    attention_span_minutes: float = 25.0  # Minutes before attention drift begins
    drift_rate: float = 0.02             # Engagement decay per minute after span
    recovery_rate: float = 0.1           # Engagement recovery from interventions

    # Confusion signals
    confusion_threshold: float = 0.3  # Below this engagement, confusion signals appear
    confusion_chat_phrases: List[str] = field(default_factory=list)

    # Response to interventions
    breakout_response: float = 0.3    # Engagement boost from breakout rooms
    poll_response: float = 0.15       # Engagement boost from polls
    cold_call_response: float = 0.0   # Can be negative (anxiety) or positive
    pace_change_response: float = 0.1 # Engagement boost from pace changes

    # Chat message templates (weighted by engagement state)
    chat_templates: Dict[str, List[str]] = field(default_factory=dict)

    def get_engagement_at(self, minute: int, noise: float = 0.05) -> float:
        """Calculate engagement level at a given minute."""
        base = {"high": 0.85, "medium": 0.60, "low": 0.35}[self.engagement_baseline]

        # Attention drift
        if minute > self.attention_span_minutes:
            decay = (minute - self.attention_span_minutes) * self.drift_rate
            base = max(0.05, base - decay)

        # Add noise
        base += random.gauss(0, noise)
        return max(0.0, min(1.0, base))


# ============================================================
# THE 15 STUDENT AGENTS
# ============================================================

STUDENT_PROFILES: List[StudentProfile] = [

    # --- HIGH ENGAGEMENT CLUSTER ---

    StudentProfile(
        name="Priya Sharma",
        student_id="S01",
        demographic={"age": 24, "major": "Education Technology", "learning_style": "visual-verbal", "tech_comfort": "high"},
        engagement_baseline="high",
        chat_frequency=0.25,
        camera_on_rate=0.95,
        speak_tendency=0.30,
        reaction_rate=0.20,
        poll_response_rate=0.95,
        attention_span_minutes=40,
        drift_rate=0.01,
        recovery_rate=0.20,
        confusion_threshold=0.2,
        breakout_response=0.25,
        poll_response=0.15,
        cold_call_response=0.10,
        pace_change_response=0.10,
        confusion_chat_phrases=["Can you clarify the relationship between X and Y?", "I think I'm missing a step here"],
        chat_templates={
            "engaged": ["Great point about {topic}!", "This connects to the reading on {concept}", "I have a question about {topic}", "Building on what {peer} said..."],
            "drifting": ["Sorry, could you repeat that?", "Which slide are we on?"],
            "confused": ["I'm lost — can you walk through that again?", "Wait, how does that follow from {concept}?"]
        }
    ),

    StudentProfile(
        name="Marcus Chen",
        student_id="S02",
        demographic={"age": 28, "major": "Information Systems", "learning_style": "analytical", "tech_comfort": "high"},
        engagement_baseline="high",
        chat_frequency=0.20,
        camera_on_rate=0.90,
        speak_tendency=0.35,
        reaction_rate=0.10,
        poll_response_rate=0.90,
        attention_span_minutes=35,
        drift_rate=0.015,
        recovery_rate=0.15,
        confusion_threshold=0.25,
        breakout_response=0.30,
        poll_response=0.20,
        cold_call_response=0.15,
        pace_change_response=0.05,
        confusion_chat_phrases=["The methodology section seems contradictory", "How does this operationalize the construct?"],
        chat_templates={
            "engaged": ["Isn't this similar to {concept}?", "The data suggests {observation}", "What about the counterfactual?", "I'd push back on that — {reason}"],
            "drifting": ["Hmm, interesting", "+1"],
            "confused": ["I don't see how the evidence supports that claim", "Can we slow down on the methodology part?"]
        }
    ),

    StudentProfile(
        name="Amara Okafor",
        student_id="S03",
        demographic={"age": 26, "major": "Public Health Informatics", "learning_style": "collaborative", "tech_comfort": "medium"},
        engagement_baseline="high",
        chat_frequency=0.18,
        camera_on_rate=0.85,
        speak_tendency=0.25,
        reaction_rate=0.30,
        poll_response_rate=0.90,
        attention_span_minutes=30,
        drift_rate=0.02,
        recovery_rate=0.25,
        confusion_threshold=0.3,
        breakout_response=0.40,  # Thrives in small groups
        poll_response=0.15,
        cold_call_response=0.05,
        pace_change_response=0.15,
        confusion_chat_phrases=["Could we get a practical example?", "How would this apply in a clinical setting?"],
        chat_templates={
            "engaged": ["In my practicum experience, {observation}", "This is really relevant to {domain}", "I agree with {peer} and want to add..."],
            "drifting": ["Interesting perspective", "Thanks for sharing"],
            "confused": ["I'm following the theory but struggling with application", "Can someone give a real-world example?"]
        }
    ),

    # --- MEDIUM ENGAGEMENT CLUSTER ---

    StudentProfile(
        name="Tyler Morrison",
        student_id="S04",
        demographic={"age": 22, "major": "Computer Science", "learning_style": "hands-on", "tech_comfort": "very_high"},
        engagement_baseline="medium",
        chat_frequency=0.12,
        camera_on_rate=0.40,
        speak_tendency=0.10,
        reaction_rate=0.15,
        poll_response_rate=0.80,
        attention_span_minutes=20,  # Short attention span for lecture
        drift_rate=0.03,
        recovery_rate=0.30,  # Recovers fast with hands-on activities
        confusion_threshold=0.25,
        breakout_response=0.35,
        poll_response=0.25,
        cold_call_response=-0.10,  # Anxiety from cold calls
        pace_change_response=0.20,
        confusion_chat_phrases=["Can we see the code for this?", "Is there a demo?"],
        chat_templates={
            "engaged": ["What framework are we using?", "I built something similar with {tech}", "The implementation is interesting"],
            "drifting": ["...", "ok"],
            "confused": ["What's the input/output for this?", "I'd need to see it running to understand"]
        }
    ),

    StudentProfile(
        name="Sofia Reyes",
        student_id="S05",
        demographic={"age": 30, "major": "Education", "learning_style": "reflective", "tech_comfort": "medium"},
        engagement_baseline="medium",
        chat_frequency=0.08,
        camera_on_rate=0.70,
        speak_tendency=0.15,
        reaction_rate=0.05,
        poll_response_rate=0.85,
        attention_span_minutes=30,
        drift_rate=0.02,
        recovery_rate=0.10,
        confusion_threshold=0.35,
        breakout_response=0.20,
        poll_response=0.10,
        cold_call_response=0.05,
        pace_change_response=0.10,
        confusion_chat_phrases=["I need time to process this", "Can we revisit this next week?"],
        chat_templates={
            "engaged": ["This reminds me of {concept} from last week", "I've been thinking about how this connects to {topic}"],
            "drifting": [],  # Sofia goes quiet when drifting
            "confused": ["I want to make sure I understand — is the main idea {interpretation}?"]
        }
    ),

    StudentProfile(
        name="James Patterson",
        student_id="S06",
        demographic={"age": 35, "major": "MBA/IT Management", "learning_style": "pragmatic", "tech_comfort": "medium"},
        engagement_baseline="medium",
        chat_frequency=0.10,
        camera_on_rate=0.60,
        speak_tendency=0.20,
        reaction_rate=0.08,
        poll_response_rate=0.75,
        attention_span_minutes=25,
        drift_rate=0.025,
        recovery_rate=0.15,
        confusion_threshold=0.3,
        breakout_response=0.15,
        poll_response=0.20,
        cold_call_response=0.10,
        pace_change_response=0.05,
        confusion_chat_phrases=["What's the business case for this?", "How does this scale?"],
        chat_templates={
            "engaged": ["From an industry perspective, {observation}", "The ROI question here is {point}", "In my company we handle this by {method}"],
            "drifting": ["Makes sense", "Noted"],
            "confused": ["Can you translate this to a business context?", "What's the practical takeaway?"]
        }
    ),

    StudentProfile(
        name="Yuki Tanaka",
        student_id="S07",
        demographic={"age": 23, "major": "Data Science", "learning_style": "visual", "tech_comfort": "high"},
        engagement_baseline="medium",
        chat_frequency=0.15,
        camera_on_rate=0.50,
        speak_tendency=0.08,
        reaction_rate=0.25,  # Heavy reaction user
        poll_response_rate=0.90,
        attention_span_minutes=28,
        drift_rate=0.02,
        recovery_rate=0.20,
        confusion_threshold=0.3,
        breakout_response=0.25,
        poll_response=0.20,
        cold_call_response=-0.15,  # Strong anxiety
        pace_change_response=0.10,
        confusion_chat_phrases=["Is there a diagram for this?", "The chart on slide {n} doesn't match the explanation"],
        chat_templates={
            "engaged": ["The visualization shows {observation}", "Could we see this as a graph?", "The data pattern suggests {insight}"],
            "drifting": ["thumbs up emoji", "eyes emoji"],
            "confused": ["The numbers don't add up — check slide {n}", "Can you show this visually?"]
        }
    ),

    StudentProfile(
        name="Aisha Khalil",
        student_id="S08",
        demographic={"age": 27, "major": "Learning Sciences", "learning_style": "verbal-social", "tech_comfort": "medium"},
        engagement_baseline="medium",
        chat_frequency=0.14,
        camera_on_rate=0.75,
        speak_tendency=0.20,
        reaction_rate=0.12,
        poll_response_rate=0.80,
        attention_span_minutes=32,
        drift_rate=0.018,
        recovery_rate=0.20,
        confusion_threshold=0.3,
        breakout_response=0.35,  # Very collaborative
        poll_response=0.10,
        cold_call_response=0.05,
        pace_change_response=0.10,
        confusion_chat_phrases=["Can we discuss this as a group?", "I learn better when we talk it through"],
        chat_templates={
            "engaged": ["Does anyone else see a connection to {topic}?", "I want to build on {peer}'s point", "This challenges the assumption that {claim}"],
            "drifting": ["Interesting", "I see"],
            "confused": ["I think I need to hear another perspective on this", "Can we pause and discuss?"]
        }
    ),

    # --- LOW ENGAGEMENT CLUSTER ---

    StudentProfile(
        name="Derek Williams",
        student_id="S09",
        demographic={"age": 33, "major": "IT Management", "learning_style": "independent", "tech_comfort": "low"},
        engagement_baseline="low",
        chat_frequency=0.03,
        camera_on_rate=0.20,
        speak_tendency=0.02,
        reaction_rate=0.02,
        poll_response_rate=0.40,
        attention_span_minutes=15,
        drift_rate=0.04,
        recovery_rate=0.05,
        confusion_threshold=0.25,
        breakout_response=0.10,
        poll_response=0.15,
        cold_call_response=-0.20,  # Very negative response
        pace_change_response=0.05,
        confusion_chat_phrases=[],  # Doesn't signal confusion in chat
        chat_templates={
            "engaged": ["ok", "sure"],
            "drifting": [],
            "confused": []
        }
    ),

    StudentProfile(
        name="Luna Martinez",
        student_id="S10",
        demographic={"age": 21, "major": "UX Design", "learning_style": "creative", "tech_comfort": "high"},
        engagement_baseline="low",
        chat_frequency=0.05,
        camera_on_rate=0.30,
        speak_tendency=0.05,
        reaction_rate=0.20,  # Uses reactions instead of speaking
        poll_response_rate=0.60,
        attention_span_minutes=18,
        drift_rate=0.035,
        recovery_rate=0.25,  # Recovers well with creative activities
        confusion_threshold=0.3,
        breakout_response=0.30,
        poll_response=0.20,
        cold_call_response=-0.05,
        pace_change_response=0.15,
        confusion_chat_phrases=["I'm sketching this out and it doesn't click"],
        chat_templates={
            "engaged": ["What if we approached it like {metaphor}?", "The UX angle here is interesting"],
            "drifting": ["fire emoji", "100 emoji"],
            "confused": ["I'm visual — can someone draw this?"]
        }
    ),

    # --- ARCHETYPE PROFILES (designed for evaluation scenarios) ---

    StudentProfile(
        name="The Lurker (Alex Kim)",
        student_id="S11",
        demographic={"age": 25, "major": "Information Science", "learning_style": "observational", "tech_comfort": "high"},
        engagement_baseline="low",
        chat_frequency=0.01,
        camera_on_rate=0.10,
        speak_tendency=0.01,
        reaction_rate=0.03,
        poll_response_rate=0.50,
        attention_span_minutes=45,  # Actually paying attention — just invisible
        drift_rate=0.005,
        recovery_rate=0.05,
        confusion_threshold=0.15,
        breakout_response=0.20,
        poll_response=0.10,
        cold_call_response=0.15,  # Actually responds well when called on
        pace_change_response=0.02,
        confusion_chat_phrases=[],
        chat_templates={
            "engaged": [],  # Lurkers don't chat
            "drifting": [],
            "confused": []
        }
    ),

    StudentProfile(
        name="The Fader (Chris O'Brien)",
        student_id="S12",
        demographic={"age": 29, "major": "Health Informatics", "learning_style": "mixed", "tech_comfort": "medium"},
        engagement_baseline="high",  # Starts high
        chat_frequency=0.20,
        camera_on_rate=0.80,
        speak_tendency=0.15,
        reaction_rate=0.15,
        poll_response_rate=0.85,
        attention_span_minutes=15,  # But fades fast
        drift_rate=0.05,  # Steep decline
        recovery_rate=0.30,  # But recovers with intervention
        confusion_threshold=0.3,
        breakout_response=0.35,
        poll_response=0.25,
        cold_call_response=0.10,
        pace_change_response=0.20,
        confusion_chat_phrases=["Wait, where are we?", "I zoned out — what page?"],
        chat_templates={
            "engaged": ["This is great!", "Really interesting approach", "I have thoughts on this"],
            "drifting": ["Sorry, lost track", "Can you repeat the last part?"],
            "confused": ["Completely lost now", "I need to rewatch this section"]
        }
    ),

    StudentProfile(
        name="The Dominator (Rachel Torres)",
        student_id="S13",
        demographic={"age": 31, "major": "Education Leadership", "learning_style": "verbal-dominant", "tech_comfort": "high"},
        engagement_baseline="high",
        chat_frequency=0.35,  # Very high
        camera_on_rate=0.95,
        speak_tendency=0.45,  # Dominates discussion
        reaction_rate=0.10,
        poll_response_rate=0.95,
        attention_span_minutes=50,
        drift_rate=0.005,
        recovery_rate=0.30,
        confusion_threshold=0.2,
        breakout_response=0.15,  # Less engaged in small groups (less audience)
        poll_response=0.10,
        cold_call_response=0.20,
        pace_change_response=0.05,
        confusion_chat_phrases=["I think what you meant to say is...", "Actually, the literature says..."],
        chat_templates={
            "engaged": ["I want to respond to that — ", "In my experience leading {context}...", "This is exactly what I've been saying about {topic}", "Let me add three points..."],
            "drifting": ["I disagree with the premise", "Can I respond to that?"],
            "confused": ["I think the framing is wrong here", "That's not how I read the literature"]
        }
    ),

    StudentProfile(
        name="The Confused (Sam Rivera)",
        student_id="S14",
        demographic={"age": 22, "major": "Undeclared/Exploring", "learning_style": "struggling", "tech_comfort": "low"},
        engagement_baseline="medium",
        chat_frequency=0.08,
        camera_on_rate=0.55,
        speak_tendency=0.05,
        reaction_rate=0.05,
        poll_response_rate=0.55,
        attention_span_minutes=20,
        drift_rate=0.03,
        recovery_rate=0.10,
        confusion_threshold=0.45,  # High confusion threshold
        breakout_response=0.20,
        poll_response=0.15,
        cold_call_response=-0.25,  # Very anxious
        pace_change_response=0.10,
        confusion_chat_phrases=[
            "I'm totally lost",
            "Can someone explain this differently?",
            "What does {term} mean?",
            "I don't understand the assignment",
            "Is this going to be on the exam?"
        ],
        chat_templates={
            "engaged": ["Oh, I think I get it now", "That example helped"],
            "drifting": ["?", "um"],
            "confused": ["I have no idea what's happening", "Can we go back to basics?", "I need help"]
        }
    ),

    StudentProfile(
        name="The Ideal (Jordan Lee)",
        student_id="S15",
        demographic={"age": 26, "major": "Learning Analytics", "learning_style": "balanced", "tech_comfort": "high"},
        engagement_baseline="high",
        chat_frequency=0.18,
        camera_on_rate=0.90,
        speak_tendency=0.22,
        reaction_rate=0.15,
        poll_response_rate=0.95,
        attention_span_minutes=45,
        drift_rate=0.01,
        recovery_rate=0.25,
        confusion_threshold=0.2,
        breakout_response=0.25,
        poll_response=0.15,
        cold_call_response=0.10,
        pace_change_response=0.10,
        confusion_chat_phrases=["Could you elaborate on the connection between {concept_a} and {concept_b}?"],
        chat_templates={
            "engaged": [
                "This connects to {concept} from the reading",
                "I see two interpretations: {a} and {b}",
                "Building on {peer}'s point, what about {extension}?",
                "The implications for practice are {insight}"
            ],
            "drifting": ["Good point", "I'd like to think more about that"],
            "confused": ["I want to make sure I'm following the logic — is the argument that {interpretation}?"]
        }
    ),
]


def get_profiles() -> List[StudentProfile]:
    """Return all student profiles."""
    return STUDENT_PROFILES


def get_profile_by_id(student_id: str) -> Optional[StudentProfile]:
    """Look up a profile by student ID."""
    for p in STUDENT_PROFILES:
        if p.student_id == student_id:
            return p
    return None


def get_profiles_by_engagement(level: str) -> List[StudentProfile]:
    """Filter profiles by engagement baseline level."""
    return [p for p in STUDENT_PROFILES if p.engagement_baseline == level]
