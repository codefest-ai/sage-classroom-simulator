"""
University Demographic Presets — Real enrollment data for 3 institutions.

Each preset generates 15 student profiles with demographic distributions
drawn from actual program-level enrollment data. Same 15 behavioral
archetypes (lurker, fader, dominator, etc.) but names, majors, backgrounds,
and baseline distributions reflect each school's real student body.

IMPORTANT DESIGN DECISION: Demographics affect visual/reportable identity only.
Behavioral differences come from INSTITUTIONAL CONTEXT, not individual demographics:
- Working professional % → camera/drift adjustments (multitasking, time-constrained)
- Cohort size → participation pressure (small seminar vs large lecture)
- Platform norms → camera-off culture (OMSCS), sync vs async expectations
These are institutional-structural factors, not racial or ethnic ones.

Data Sources (cited inline):
- CGU CISAT: Peterson's 2023-24, IPEDS 2024-25 (Unit ID 112251)
- Georgia Tech CoC: GT IRP Fall 2025, OMSCS Annual Report 2024
- Howard CS: Peterson's 2023-24, IPEDS 2024-25 (Unit ID 131520)
"""

from typing import Dict, List, Tuple

# ============================================================
# DEMOGRAPHIC DISTRIBUTIONS (from real enrollment data)
# ============================================================

UNIVERSITY_DATA = {
    "cgu": {
        "full_name": "Claremont Graduate University",
        "program": "Center for Information Systems & Technology (CISAT)",
        "location": "Claremont, CA",
        "program_size": 153,
        "data_year": "2023-2024",
        "sources": [
            "Peterson's Graduate Schools — CGU CISAT (petersons.com)",
            "NCES IPEDS Unit ID 112251, AY 2024-25",
            "College Tuition Compare / IPEDS AY 2024-25",
        ],
        # Gender: 63% male, 36% female, 1% unreported (Peterson's)
        "gender_weights": {"male": 0.63, "female": 0.36, "nonbinary": 0.01},
        # Race/ethnicity (CISAT program-level, Peterson's):
        # International 43%, White 19%, Hispanic 12.42%, Asian 12.42%,
        # Black 7.19%, Unknown 3.27%, NHPI 0.65%, Two+ 0.65%
        "ethnicity_weights": {
            "international": 0.43,
            "white": 0.19,
            "hispanic": 0.1242,
            "asian": 0.1242,
            "black": 0.0719,
            "two_or_more": 0.0065,
            "other": 0.0332,
        },
        # International breakdown (estimated from CGU IS program patterns):
        # Heavy China/India/Korea, some Middle East, some Latin America
        "international_origins": [
            ("China", 0.30), ("India", 0.25), ("South Korea", 0.15),
            ("Iran", 0.08), ("Mexico", 0.07), ("Taiwan", 0.05),
            ("Nigeria", 0.05), ("Turkey", 0.05),
        ],
        "age_range": (23, 40),  # Graduate program, mix of recent grads + professionals
        "working_professional_pct": 0.35,  # Estimated — CGU has part-time options
        "majors": [
            "Information Systems", "Data Science", "Information Technology",
            "Health Informatics", "Learning Technologies", "Cybersecurity",
            "Human-Centered Design",
        ],
    },

    "gatech": {
        "full_name": "Georgia Institute of Technology",
        "program": "College of Computing — MS Programs (incl. OMSCS)",
        "location": "Atlanta, GA",
        "program_size": 16910,  # Fall 2024
        "data_year": "Fall 2024 (CoC) / Fall 2025 (IRP)",
        "sources": [
            "Georgia Tech IRP Student Demographics, Census Fall 2025",
            "Georgia Tech College of Computing Facts & Rankings, Spring 2025",
            "OMSCS 2024 Annual Report (omscs.gatech.edu)",
            "NCES IPEDS Unit ID 139755, AY 2024-25",
        ],
        # Gender: ~75% male, ~25% female (CoC grad estimate from GT-wide 72.5% + CS skew)
        "gender_weights": {"male": 0.75, "female": 0.24, "nonbinary": 0.01},
        # Race/ethnicity (GT graduate-level, IRP Fall 2025):
        # International 33.2%, White 26.5%, Asian 24.2%, Hispanic 6.6%,
        # Black 4.4%, Two+ 2.8%, Other/Unknown 2.3%
        "ethnicity_weights": {
            "international": 0.332,
            "white": 0.265,
            "asian": 0.242,
            "hispanic": 0.066,
            "black": 0.044,
            "two_or_more": 0.028,
            "other": 0.023,
        },
        "international_origins": [
            ("India", 0.35), ("China", 0.25), ("South Korea", 0.10),
            ("Taiwan", 0.05), ("Bangladesh", 0.05), ("Iran", 0.05),
            ("Canada", 0.05), ("Brazil", 0.05), ("Germany", 0.05),
        ],
        "age_range": (24, 45),  # OMSCS avg age 30, 87% working full-time
        "working_professional_pct": 0.87,  # OMSCS survey data
        "majors": [
            "Computer Science", "Machine Learning", "Interactive Intelligence",
            "Computational Perception & Robotics", "Computing Systems",
            "Information Security", "Human-Computer Interaction",
        ],
    },

    "howard": {
        "full_name": "Howard University",
        "program": "Department of Systems & Computer Science",
        "location": "Washington, DC",
        "program_size": 21,  # Peterson's
        "data_year": "2023-2024",
        "sources": [
            "Peterson's Graduate Schools — Howard Dept. Systems & CS",
            "NCES IPEDS Unit ID 131520, AY 2024-25",
            "College Factual — Howard University Diversity",
            "Howard IRA Common Data Set",
        ],
        # Gender: 52% male, 47% female (Peterson's — notably balanced for CS)
        "gender_weights": {"male": 0.52, "female": 0.47, "nonbinary": 0.01},
        # Race/ethnicity (CS department, Peterson's):
        # International 52%, Black 47.62%, other not individually reported
        # Note: remarkably, international students are MAJORITY even at an HBCU CS dept
        "ethnicity_weights": {
            "international": 0.52,
            "black": 0.4762,
            "other": 0.0038,  # Residual — tiny program, other categories ~0
        },
        "international_origins": [
            ("Nigeria", 0.25), ("Ethiopia", 0.15), ("Ghana", 0.12),
            ("India", 0.12), ("Cameroon", 0.10), ("Jamaica", 0.08),
            ("Kenya", 0.08), ("Bangladesh", 0.05), ("Brazil", 0.05),
        ],
        "age_range": (22, 35),  # Mix of recent graduates + accelerated MS
        "working_professional_pct": 0.25,  # Estimated — smaller, more traditional
        "majors": [
            "Computer Science", "Systems Engineering", "Data Science",
            "Cybersecurity", "Information Systems",
        ],
    },
}


# ============================================================
# NAME POOLS (culturally plausible for each demographic)
# ============================================================

NAME_POOLS = {
    "international_China": [
        ("Wei Zhang", "M"), ("Mei Lin", "F"), ("Jian Chen", "M"),
        ("Xiaoming Wu", "M"), ("Yue Wang", "F"), ("Hao Li", "M"),
    ],
    "international_India": [
        ("Arjun Patel", "M"), ("Priya Sharma", "F"), ("Vikram Reddy", "M"),
        ("Ananya Krishnan", "F"), ("Rohit Gupta", "M"), ("Deepa Nair", "F"),
    ],
    "international_South Korea": [
        ("Joon Park", "M"), ("Yuna Kim", "F"), ("Sungho Lee", "M"),
        ("Minji Choi", "F"),
    ],
    "international_Iran": [
        ("Amir Hosseini", "M"), ("Sara Tehrani", "F"), ("Reza Karimi", "M"),
    ],
    "international_Mexico": [
        ("Carlos Mendoza", "M"), ("Alejandra Reyes", "F"),
    ],
    "international_Taiwan": [
        ("Yi-Chen Huang", "M"), ("Mei-Ling Tsai", "F"),
    ],
    "international_Nigeria": [
        ("Chukwu Okafor", "M"), ("Ngozi Eze", "F"), ("Emeka Adeyemi", "M"),
        ("Amina Ibrahim", "F"),
    ],
    "international_Turkey": [
        ("Emre Yilmaz", "M"), ("Zeynep Kaya", "F"),
    ],
    "international_Ethiopia": [
        ("Dawit Tadesse", "M"), ("Hiwot Bekele", "F"),
    ],
    "international_Ghana": [
        ("Kwame Mensah", "M"), ("Ama Asante", "F"),
    ],
    "international_Cameroon": [
        ("Jean-Pierre Mbah", "M"), ("Esther Nkeng", "F"),
    ],
    "international_Jamaica": [
        ("Andre Campbell", "M"), ("Shanice Brown", "F"),
    ],
    "international_Kenya": [
        ("Brian Wanjiku", "M"), ("Grace Mwangi", "F"),
    ],
    "international_Bangladesh": [
        ("Rafiq Ahmed", "M"), ("Tasnim Hassan", "F"),
    ],
    "international_Brazil": [
        ("Lucas Silva", "M"), ("Mariana Costa", "F"),
    ],
    "international_Canada": [
        ("Ryan Thompson", "M"), ("Sarah Mitchell", "F"),
    ],
    "international_Germany": [
        ("Lukas Müller", "M"), ("Anna Schmidt", "F"),
    ],
    "white": [
        ("Tyler Morrison", "M"), ("Emily Parker", "F"), ("James Patterson", "M"),
        ("Hannah Novak", "F"), ("Chris O'Brien", "M"), ("Megan Doyle", "F"),
        ("Ryan Kowalski", "M"), ("Claire Hendricks", "F"),
    ],
    "hispanic": [
        ("Sofia Reyes", "F"), ("Carlos Gutierrez", "M"), ("Luna Martinez", "F"),
        ("Diego Fuentes", "M"), ("Isabella Morales", "F"), ("Marco Salazar", "M"),
    ],
    "asian": [
        ("Yuki Tanaka", "F"), ("Kevin Nguyen", "M"), ("Aisha Khalil", "F"),
        ("Alex Kim", "M"), ("Grace Lim", "F"), ("David Tran", "M"),
    ],
    "black": [
        ("Jordan Lee", "M"), ("Amara Okafor", "F"), ("Derek Williams", "M"),
        ("Jasmine Brooks", "F"), ("Marcus Thompson", "M"), ("Nyla Jackson", "F"),
        ("Terrence Washington", "M"), ("Kaia Robinson", "F"),
        ("Darnell Hayes", "M"), ("Tasha Mitchell", "F"),
        ("Xavier Brown", "M"), ("Imani Davis", "F"),
    ],
    "two_or_more": [
        ("Sam Rivera", "M"), ("Maya Chen-Williams", "F"), ("Kai Nakamura-Jones", "M"),
    ],
}


# ============================================================
# ARCHETYPE DEFINITIONS (behavioral — independent of demographics)
# ============================================================

# Same 15 archetypes from v1, parameterized as dicts.
# The university preset assigns names/demographics; archetypes define behavior.

ARCHETYPES = [
    # --- HIGH ENGAGEMENT CLUSTER ---
    {
        "archetype": "Engaged Leader",
        "engagement_baseline": "high",
        "chat_frequency": 0.25, "speak_tendency": 0.30, "camera_on_rate": 0.95,
        "reaction_rate": 0.20, "poll_response_rate": 0.95,
        "attention_span_minutes": 40, "drift_rate": 0.01, "recovery_rate": 0.20,
        "confusion_threshold": 0.2,
        "breakout_response": 0.25, "poll_response": 0.15,
        "cold_call_response": 0.10, "pace_change_response": 0.10,
        "learning_style": "visual-verbal", "tech_comfort": "high",
    },
    {
        "archetype": "Critical Thinker",
        "engagement_baseline": "high",
        "chat_frequency": 0.20, "speak_tendency": 0.35, "camera_on_rate": 0.90,
        "reaction_rate": 0.10, "poll_response_rate": 0.90,
        "attention_span_minutes": 35, "drift_rate": 0.015, "recovery_rate": 0.15,
        "confusion_threshold": 0.25,
        "breakout_response": 0.30, "poll_response": 0.20,
        "cold_call_response": 0.15, "pace_change_response": 0.05,
        "learning_style": "analytical", "tech_comfort": "high",
    },
    {
        "archetype": "Collaborative Learner",
        "engagement_baseline": "high",
        "chat_frequency": 0.18, "speak_tendency": 0.25, "camera_on_rate": 0.85,
        "reaction_rate": 0.30, "poll_response_rate": 0.90,
        "attention_span_minutes": 30, "drift_rate": 0.02, "recovery_rate": 0.25,
        "confusion_threshold": 0.3,
        "breakout_response": 0.40, "poll_response": 0.15,
        "cold_call_response": 0.05, "pace_change_response": 0.15,
        "learning_style": "collaborative", "tech_comfort": "medium",
    },
    # --- MEDIUM ENGAGEMENT CLUSTER ---
    {
        "archetype": "Hands-On Builder",
        "engagement_baseline": "medium",
        "chat_frequency": 0.12, "speak_tendency": 0.10, "camera_on_rate": 0.40,
        "reaction_rate": 0.15, "poll_response_rate": 0.80,
        "attention_span_minutes": 20, "drift_rate": 0.03, "recovery_rate": 0.30,
        "confusion_threshold": 0.25,
        "breakout_response": 0.35, "poll_response": 0.25,
        "cold_call_response": -0.10, "pace_change_response": 0.20,
        "learning_style": "hands-on", "tech_comfort": "very_high",
    },
    {
        "archetype": "Reflective Processor",
        "engagement_baseline": "medium",
        "chat_frequency": 0.08, "speak_tendency": 0.15, "camera_on_rate": 0.70,
        "reaction_rate": 0.05, "poll_response_rate": 0.85,
        "attention_span_minutes": 30, "drift_rate": 0.02, "recovery_rate": 0.10,
        "confusion_threshold": 0.35,
        "breakout_response": 0.20, "poll_response": 0.10,
        "cold_call_response": 0.05, "pace_change_response": 0.10,
        "learning_style": "reflective", "tech_comfort": "medium",
    },
    {
        "archetype": "Pragmatist",
        "engagement_baseline": "medium",
        "chat_frequency": 0.10, "speak_tendency": 0.20, "camera_on_rate": 0.60,
        "reaction_rate": 0.08, "poll_response_rate": 0.75,
        "attention_span_minutes": 25, "drift_rate": 0.025, "recovery_rate": 0.15,
        "confusion_threshold": 0.3,
        "breakout_response": 0.15, "poll_response": 0.20,
        "cold_call_response": 0.10, "pace_change_response": 0.05,
        "learning_style": "pragmatic", "tech_comfort": "medium",
    },
    {
        "archetype": "Visual Learner",
        "engagement_baseline": "medium",
        "chat_frequency": 0.15, "speak_tendency": 0.08, "camera_on_rate": 0.50,
        "reaction_rate": 0.25, "poll_response_rate": 0.90,
        "attention_span_minutes": 28, "drift_rate": 0.02, "recovery_rate": 0.20,
        "confusion_threshold": 0.3,
        "breakout_response": 0.25, "poll_response": 0.20,
        "cold_call_response": -0.15, "pace_change_response": 0.10,
        "learning_style": "visual", "tech_comfort": "high",
    },
    {
        "archetype": "Social Connector",
        "engagement_baseline": "medium",
        "chat_frequency": 0.14, "speak_tendency": 0.20, "camera_on_rate": 0.75,
        "reaction_rate": 0.12, "poll_response_rate": 0.80,
        "attention_span_minutes": 32, "drift_rate": 0.018, "recovery_rate": 0.20,
        "confusion_threshold": 0.3,
        "breakout_response": 0.35, "poll_response": 0.10,
        "cold_call_response": 0.05, "pace_change_response": 0.10,
        "learning_style": "verbal-social", "tech_comfort": "medium",
    },
    # --- LOW ENGAGEMENT CLUSTER ---
    {
        "archetype": "Withdrawn",
        "engagement_baseline": "low",
        "chat_frequency": 0.03, "speak_tendency": 0.02, "camera_on_rate": 0.20,
        "reaction_rate": 0.02, "poll_response_rate": 0.40,
        "attention_span_minutes": 15, "drift_rate": 0.04, "recovery_rate": 0.05,
        "confusion_threshold": 0.25,
        "breakout_response": 0.10, "poll_response": 0.15,
        "cold_call_response": -0.20, "pace_change_response": 0.05,
        "learning_style": "independent", "tech_comfort": "low",
    },
    {
        "archetype": "Creative Observer",
        "engagement_baseline": "low",
        "chat_frequency": 0.05, "speak_tendency": 0.05, "camera_on_rate": 0.30,
        "reaction_rate": 0.20, "poll_response_rate": 0.60,
        "attention_span_minutes": 18, "drift_rate": 0.035, "recovery_rate": 0.25,
        "confusion_threshold": 0.3,
        "breakout_response": 0.30, "poll_response": 0.20,
        "cold_call_response": -0.05, "pace_change_response": 0.15,
        "learning_style": "creative", "tech_comfort": "high",
    },
    # --- ARCHETYPE PROFILES (evaluation) ---
    {
        "archetype": "The Lurker",
        "engagement_baseline": "low",
        "chat_frequency": 0.01, "speak_tendency": 0.01, "camera_on_rate": 0.10,
        "reaction_rate": 0.03, "poll_response_rate": 0.50,
        "attention_span_minutes": 45, "drift_rate": 0.005, "recovery_rate": 0.05,
        "confusion_threshold": 0.15,
        "breakout_response": 0.20, "poll_response": 0.10,
        "cold_call_response": 0.15, "pace_change_response": 0.02,
        "learning_style": "observational", "tech_comfort": "high",
    },
    {
        "archetype": "The Fader",
        "engagement_baseline": "high",
        "chat_frequency": 0.20, "speak_tendency": 0.15, "camera_on_rate": 0.80,
        "reaction_rate": 0.15, "poll_response_rate": 0.85,
        "attention_span_minutes": 15, "drift_rate": 0.05, "recovery_rate": 0.30,
        "confusion_threshold": 0.3,
        "breakout_response": 0.35, "poll_response": 0.25,
        "cold_call_response": 0.10, "pace_change_response": 0.20,
        "learning_style": "mixed", "tech_comfort": "medium",
    },
    {
        "archetype": "The Dominator",
        "engagement_baseline": "high",
        "chat_frequency": 0.35, "speak_tendency": 0.45, "camera_on_rate": 0.95,
        "reaction_rate": 0.10, "poll_response_rate": 0.95,
        "attention_span_minutes": 50, "drift_rate": 0.005, "recovery_rate": 0.30,
        "confusion_threshold": 0.2,
        "breakout_response": 0.15, "poll_response": 0.10,
        "cold_call_response": 0.20, "pace_change_response": 0.05,
        "learning_style": "verbal-dominant", "tech_comfort": "high",
    },
    {
        "archetype": "The Confused",
        "engagement_baseline": "medium",
        "chat_frequency": 0.08, "speak_tendency": 0.05, "camera_on_rate": 0.55,
        "reaction_rate": 0.05, "poll_response_rate": 0.55,
        "attention_span_minutes": 20, "drift_rate": 0.03, "recovery_rate": 0.10,
        "confusion_threshold": 0.45,
        "breakout_response": 0.20, "poll_response": 0.15,
        "cold_call_response": -0.25, "pace_change_response": 0.10,
        "learning_style": "struggling", "tech_comfort": "low",
    },
    {
        "archetype": "The Ideal",
        "engagement_baseline": "high",
        "chat_frequency": 0.18, "speak_tendency": 0.22, "camera_on_rate": 0.90,
        "reaction_rate": 0.15, "poll_response_rate": 0.95,
        "attention_span_minutes": 45, "drift_rate": 0.01, "recovery_rate": 0.25,
        "confusion_threshold": 0.2,
        "breakout_response": 0.25, "poll_response": 0.15,
        "cold_call_response": 0.10, "pace_change_response": 0.10,
        "learning_style": "balanced", "tech_comfort": "high",
    },
]


def _pick_demographic(uni_key: str, slot_index: int, seed: int = 42) -> Dict:
    """
    Deterministically assign a demographic profile for a given slot.

    Uses the university's real enrollment weights to distribute demographics
    across the 15 slots. Deterministic given (uni_key, seed) so scenarios
    are reproducible.
    """
    import random as _rng
    _rng.seed(seed + slot_index * 1000 + hash(uni_key) % 10000)

    uni = UNIVERSITY_DATA[uni_key]
    eth_weights = uni["ethnicity_weights"]

    # Weighted random ethnicity
    categories = list(eth_weights.keys())
    weights = list(eth_weights.values())
    ethnicity = _rng.choices(categories, weights=weights, k=1)[0]

    # Gender
    gw = uni["gender_weights"]
    gender_cats = list(gw.keys())
    gender_wts = list(gw.values())
    gender = _rng.choices(gender_cats, weights=gender_wts, k=1)[0]

    # Age
    age_lo, age_hi = uni["age_range"]
    is_professional = _rng.random() < uni["working_professional_pct"]
    if is_professional:
        age = _rng.randint(max(age_lo, 28), age_hi)
    else:
        age = _rng.randint(age_lo, min(age_hi, 32))

    # Major
    major = _rng.choice(uni["majors"])

    # Name
    origin = None
    if ethnicity == "international":
        # Pick origin country
        origins = uni["international_origins"]
        o_names = [o[0] for o in origins]
        o_weights = [o[1] for o in origins]
        origin = _rng.choices(o_names, weights=o_weights, k=1)[0]
        pool_key = f"international_{origin}"
    else:
        pool_key = ethnicity

    pool = NAME_POOLS.get(pool_key, NAME_POOLS.get("white", []))
    # Filter by gender
    gender_initial = "M" if gender == "male" else "F"
    gender_pool = [n for n in pool if n[1] == gender_initial]
    if not gender_pool:
        gender_pool = pool  # Fallback

    name, _ = _rng.choice(gender_pool)

    return {
        "name": name,
        "age": age,
        "gender": gender,
        "major": major,
        "ethnicity": ethnicity,
        "origin_country": origin,
        "is_working_professional": is_professional,
        "university": uni["full_name"],
        "program": uni["program"],
    }


# ============================================================
# INSTITUTIONAL CONTEXT MODIFIERS
# These affect simulation behavior based on structural/institutional
# factors — NOT individual demographics. This is the key design decision.
# ============================================================

INSTITUTIONAL_MODIFIERS = {
    "cgu": {
        # Small SoCal private grad school. Mix of full-time + part-time.
        # Moderate seminar culture. Baseline/control condition.
        "camera_on_modifier": 0.0,         # No adjustment (baseline)
        "drift_rate_modifier": 0.0,         # No adjustment
        "attention_span_modifier": 0,       # No adjustment
        "speak_tendency_modifier": 0.0,     # No adjustment
        "breakout_response_modifier": 0.0,  # No adjustment
        "chat_frequency_modifier": 0.0,     # No adjustment
        "working_pro_camera_penalty": -0.25,  # Working pros have camera off more
        "working_pro_drift_bonus": 0.008,     # Multitasking = faster drift
        "working_pro_attention_penalty": -5,  # Shorter focus blocks
        "description": "Baseline: small graduate seminar, mixed cohort",
    },
    "gatech": {
        # 87% working professionals (OMSCS). Camera-off is NORMAL culture.
        # Async-native. Time-constrained. High tech comfort.
        # These modifiers apply to ALL students because it's the institutional norm.
        "camera_on_modifier": -0.15,        # Camera-off culture across the board
        "drift_rate_modifier": 0.005,       # Everyone drifts slightly faster (multitasking norm)
        "attention_span_modifier": -3,      # Shorter focused attention (parallel work)
        "speak_tendency_modifier": -0.05,   # Less verbal, more chat-oriented
        "breakout_response_modifier": -0.05, # Breakouts less effective in online-async culture
        "chat_frequency_modifier": 0.03,    # Compensatory: more chat when camera/mic off
        "working_pro_camera_penalty": -0.30, # Working pros even more camera-off
        "working_pro_drift_bonus": 0.012,    # Multitasking between work and class
        "working_pro_attention_penalty": -8,  # Work interruptions shorten focus
        "description": "Large online program: camera-off culture, working professionals, async norms",
    },
    "howard": {
        # Small department (21 students). Higher participation pressure.
        # Everyone is visible. Stronger social accountability.
        "camera_on_modifier": 0.10,         # Small cohort = higher camera norm
        "drift_rate_modifier": -0.003,      # Less drift (social accountability)
        "attention_span_modifier": 2,       # Slightly longer focus (seminar intimacy)
        "speak_tendency_modifier": 0.03,    # More verbal participation (small group pressure)
        "breakout_response_modifier": 0.05, # Breakouts effective (already collaborative culture)
        "chat_frequency_modifier": 0.0,     # No adjustment
        "working_pro_camera_penalty": -0.20,
        "working_pro_drift_bonus": 0.008,
        "working_pro_attention_penalty": -5,
        "description": "Small department: high visibility, social accountability, intimate seminar",
    },
}


def _apply_institutional_modifiers(profile: Dict, uni_key: str) -> Dict:
    """
    Apply institutional-level behavioral modifiers to a profile.

    Modifiers come from the university's structural characteristics
    (cohort size, working professional %, platform norms) — NOT from
    individual student demographics like race or ethnicity.
    """
    mods = INSTITUTIONAL_MODIFIERS.get(uni_key, INSTITUTIONAL_MODIFIERS["cgu"])

    # Base institutional adjustments (apply to everyone in this cohort)
    profile["camera_on_rate"] = max(0.05, min(0.99,
        profile["camera_on_rate"] + mods["camera_on_modifier"]))
    profile["drift_rate"] = max(0.001, min(0.08,
        profile["drift_rate"] + mods["drift_rate_modifier"]))
    profile["attention_span_minutes"] = max(10, min(55,
        profile["attention_span_minutes"] + mods["attention_span_modifier"]))
    profile["speak_tendency"] = max(0.01, min(0.50,
        profile["speak_tendency"] + mods["speak_tendency_modifier"]))
    profile["breakout_response"] = max(0.0, min(0.50,
        profile["breakout_response"] + mods["breakout_response_modifier"]))
    profile["chat_frequency"] = max(0.01, min(0.40,
        profile["chat_frequency"] + mods["chat_frequency_modifier"]))

    # Working professional adjustments (structural, not demographic)
    if profile["demographic"].get("is_working_professional"):
        profile["camera_on_rate"] = max(0.05,
            profile["camera_on_rate"] + mods["working_pro_camera_penalty"])
        profile["drift_rate"] = max(0.001,
            profile["drift_rate"] + mods["working_pro_drift_bonus"])
        profile["attention_span_minutes"] = max(10,
            profile["attention_span_minutes"] + mods["working_pro_attention_penalty"])

    return profile


def generate_preset_profiles(uni_key: str = "cgu", seed: int = 42) -> List[Dict]:
    """
    Generate 15 student profiles for a given university preset.

    Returns list of dicts compatible with StudentProfile constructor.
    Each profile combines a behavioral archetype with a demographically
    realistic identity from the specified university's enrollment data.

    Behavioral differences come from institutional context modifiers
    (cohort size, working professional %, platform norms), NOT from
    individual demographics. This is a deliberate design decision.
    """
    if uni_key not in UNIVERSITY_DATA:
        raise ValueError(f"Unknown university: {uni_key}. Options: {list(UNIVERSITY_DATA.keys())}")

    profiles = []
    used_names = set()

    for i, archetype in enumerate(ARCHETYPES):
        # Get demographic assignment
        demo = _pick_demographic(uni_key, i, seed)

        # Ensure unique names
        attempts = 0
        while demo["name"] in used_names and attempts < 20:
            demo = _pick_demographic(uni_key, i, seed + attempts + 100)
            attempts += 1
        used_names.add(demo["name"])

        profile = {
            "name": demo["name"],
            "student_id": f"S{i+1:02d}",
            "demographic": {
                "age": demo["age"],
                "major": demo["major"],
                "learning_style": archetype["learning_style"],
                "tech_comfort": archetype["tech_comfort"],
                "gender": demo["gender"],
                "ethnicity": demo["ethnicity"],
                "origin_country": demo["origin_country"],
                "is_working_professional": demo["is_working_professional"],
                "university": demo["university"],
                "program": demo["program"],
            },
            "archetype": archetype["archetype"],
            "engagement_baseline": archetype["engagement_baseline"],
            "chat_frequency": archetype["chat_frequency"],
            "camera_on_rate": archetype["camera_on_rate"],
            "speak_tendency": archetype["speak_tendency"],
            "reaction_rate": archetype["reaction_rate"],
            "poll_response_rate": archetype["poll_response_rate"],
            "attention_span_minutes": archetype["attention_span_minutes"],
            "drift_rate": archetype["drift_rate"],
            "recovery_rate": archetype["recovery_rate"],
            "confusion_threshold": archetype["confusion_threshold"],
            "breakout_response": archetype["breakout_response"],
            "poll_response": archetype["poll_response"],
            "cold_call_response": archetype["cold_call_response"],
            "pace_change_response": archetype["pace_change_response"],
        }

        # Apply institutional context modifiers
        profile = _apply_institutional_modifiers(profile, uni_key)

        profiles.append(profile)

    return profiles


def get_university_info(uni_key: str) -> Dict:
    """Return metadata about the university preset."""
    if uni_key not in UNIVERSITY_DATA:
        raise ValueError(f"Unknown university: {uni_key}. Options: {list(UNIVERSITY_DATA.keys())}")
    uni = UNIVERSITY_DATA[uni_key]
    return {
        "key": uni_key,
        "full_name": uni["full_name"],
        "program": uni["program"],
        "location": uni["location"],
        "program_size": uni["program_size"],
        "data_year": uni["data_year"],
        "sources": uni["sources"],
        "gender_distribution": uni["gender_weights"],
        "ethnicity_distribution": uni["ethnicity_weights"],
    }


def list_presets() -> List[str]:
    """Return available university preset keys."""
    return list(UNIVERSITY_DATA.keys())
