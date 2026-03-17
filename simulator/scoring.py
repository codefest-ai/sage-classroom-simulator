"""
Engagement Scoring Model — Weighted engagement index and state classification.

Maps to Endsley (1995) SA Levels:
  Level 1 (Perception)    → Raw signal collection (engine.py)
  Level 2 (Comprehension) → Engagement scoring + pattern classification (THIS FILE)
  Level 3 (Projection)    → Recommendation generation (engine.py + dashboard)

Engagement-to-action translation framework from Phase 2 Section 3.1b.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ============================================================
# SIGNAL WEIGHTS
# Derived from the engagement signal literature.
# Weights sum to 1.0 for normalized index.
# ============================================================

SIGNAL_WEIGHTS = {
    "speaking_equity": 0.25,     # Most reliable engagement indicator
    "chat_activity": 0.20,       # Active participation signal
    "poll_participation": 0.20,  # Structured response signal
    "reaction_frequency": 0.10,  # Low-effort but present signal
    "camera_status": 0.15,       # Presence signal (noisy but informative)
    "silence_gap": 0.10,         # Inverse signal — long silence = disengagement
}


# ============================================================
# ENGAGEMENT STATES
# ============================================================

ENGAGEMENT_STATES = {
    "engaged":      {"min": 0.65, "max": 1.00, "color": "#22c55e", "label": "Engaged"},
    "drifting":     {"min": 0.40, "max": 0.65, "color": "#f59e0b", "label": "Drifting"},
    "disengaged":   {"min": 0.15, "max": 0.40, "color": "#ef4444", "label": "Disengaged"},
    "confused":     {"min": 0.00, "max": 1.00, "color": "#8b5cf6", "label": "Confused"},  # Orthogonal to engagement
}


# ============================================================
# PATTERN CLASSIFICATIONS
# SA Level 2: What the engagement data MEANS
# ============================================================

PATTERNS = {
    "energy_decay": {
        "description": "Class-wide engagement declining over time",
        "detection": "Mean engagement drops >15% from session start",
        "severity_thresholds": [0.10, 0.20, 0.30],  # mild, moderate, severe
    },
    "equity_imbalance": {
        "description": "Speaking time dominated by 1-2 students",
        "detection": "Gini coefficient of speaking time > 0.6",
        "severity_thresholds": [0.5, 0.65, 0.80],
    },
    "confusion_cluster": {
        "description": "Multiple students signaling confusion simultaneously",
        "detection": "3+ students in confused state within 2-minute window",
        "severity_thresholds": [2, 4, 6],  # student count
    },
    "silent_majority": {
        "description": "Most students have not spoken or chatted",
        "detection": ">60% of students with zero speaking + zero chat",
        "severity_thresholds": [0.5, 0.65, 0.80],  # percentage
    },
    "breakout_boost": {
        "description": "Engagement increased after breakout room activity",
        "detection": "Mean engagement rises >10% post-breakout",
        "severity_thresholds": [0.05, 0.15, 0.25],  # positive pattern
    },
    "fade_cascade": {
        "description": "Sequential student disengagement (social contagion)",
        "detection": "3+ students drift to disengaged within 3-minute window",
        "severity_thresholds": [2, 4, 6],
    },
}


@dataclass
class SignalSnapshot:
    """Raw engagement signals for one student at one time step."""
    student_id: str
    minute: int
    speaking: bool = False
    speaking_duration_sec: float = 0.0
    chat_sent: bool = False
    chat_text: str = ""
    poll_responded: bool = False
    poll_answer: str = ""
    reaction_sent: bool = False
    reaction_type: str = ""
    camera_on: bool = False
    silence_duration_sec: float = 0.0


@dataclass
class EngagementScore:
    """Computed engagement score for one student."""
    student_id: str
    minute: int
    raw_scores: Dict[str, float]  # Per-signal scores
    weighted_index: float          # 0.0-1.0 composite
    state: str                     # engaged / drifting / disengaged
    is_confused: bool              # Orthogonal flag
    contributing_signals: List[str]  # Which signals drove the score


@dataclass
class ClassSnapshot:
    """Aggregate engagement for the whole class at one time step."""
    minute: int
    mean_engagement: float
    median_engagement: float
    std_engagement: float
    student_scores: List[EngagementScore]
    patterns_detected: List[Dict]
    speaking_gini: float
    active_speakers: int
    total_students: int


class EngagementScorer:
    """
    Computes engagement indices from raw signals.
    SA Level 2: transforms perception into comprehension.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or SIGNAL_WEIGHTS
        self._history: List[ClassSnapshot] = []
        self._student_speaking_totals: Dict[str, float] = {}
        self._student_chat_counts: Dict[str, int] = {}
        self._confusion_signals: List[Tuple[str, int]] = []  # (student_id, minute)

    def score_student(self, signals: SignalSnapshot, profile_engagement: float = 0.5) -> EngagementScore:
        """Score a single student's engagement from raw signals."""
        raw = {}
        contributing = []

        # Speaking equity — based on whether they spoke and duration
        if signals.speaking:
            raw["speaking_equity"] = min(1.0, signals.speaking_duration_sec / 30.0)
            contributing.append("speaking")
            self._student_speaking_totals[signals.student_id] = (
                self._student_speaking_totals.get(signals.student_id, 0) + signals.speaking_duration_sec
            )
        else:
            raw["speaking_equity"] = 0.0

        # Chat activity
        if signals.chat_sent:
            raw["chat_activity"] = 0.8 if len(signals.chat_text) > 20 else 0.4
            contributing.append("chat")
            self._student_chat_counts[signals.student_id] = (
                self._student_chat_counts.get(signals.student_id, 0) + 1
            )
        else:
            raw["chat_activity"] = 0.0

        # Poll participation
        raw["poll_participation"] = 1.0 if signals.poll_responded else 0.0
        if signals.poll_responded:
            contributing.append("poll")

        # Reaction frequency
        raw["reaction_frequency"] = 0.6 if signals.reaction_sent else 0.0
        if signals.reaction_sent:
            contributing.append("reaction")

        # Camera status
        raw["camera_status"] = 0.8 if signals.camera_on else 0.1
        if signals.camera_on:
            contributing.append("camera")

        # Silence gap (inverse — long silence = low score)
        if signals.silence_duration_sec > 0:
            raw["silence_gap"] = max(0.0, 1.0 - (signals.silence_duration_sec / 120.0))
        else:
            raw["silence_gap"] = 0.7  # No silence data = neutral

        # Weighted composite
        weighted = sum(raw.get(k, 0) * v for k, v in self.weights.items())

        # Blend with profile-based engagement (50/50 signal vs profile)
        blended = 0.5 * weighted + 0.5 * profile_engagement

        # Classify state
        if blended >= 0.65:
            state = "engaged"
        elif blended >= 0.40:
            state = "drifting"
        else:
            state = "disengaged"

        # Confusion detection (orthogonal to engagement level)
        is_confused = False
        if signals.chat_sent and signals.chat_text:
            confusion_keywords = ["lost", "confused", "don't understand", "what", "?", "help",
                                  "repeat", "explain", "huh", "wait"]
            text_lower = signals.chat_text.lower()
            if any(kw in text_lower for kw in confusion_keywords):
                is_confused = True
                self._confusion_signals.append((signals.student_id, signals.minute))

        return EngagementScore(
            student_id=signals.student_id,
            minute=signals.minute,
            raw_scores=raw,
            weighted_index=round(blended, 3),
            state=state,
            is_confused=is_confused,
            contributing_signals=contributing,
        )

    def score_class(self, student_scores: List[EngagementScore], minute: int) -> ClassSnapshot:
        """Aggregate individual scores into class-level engagement snapshot."""
        if not student_scores:
            return ClassSnapshot(
                minute=minute, mean_engagement=0, median_engagement=0,
                std_engagement=0, student_scores=[], patterns_detected=[],
                speaking_gini=0, active_speakers=0, total_students=0
            )

        indices = [s.weighted_index for s in student_scores]
        n = len(indices)

        mean_eng = sum(indices) / n
        sorted_indices = sorted(indices)
        median_eng = sorted_indices[n // 2] if n % 2 else (sorted_indices[n // 2 - 1] + sorted_indices[n // 2]) / 2
        variance = sum((x - mean_eng) ** 2 for x in indices) / n
        std_eng = variance ** 0.5

        # Speaking equity (Gini coefficient)
        speaking_gini = self._compute_gini()
        active_speakers = sum(1 for s in student_scores if "speaking" in s.contributing_signals)

        # Pattern detection
        patterns = self._detect_patterns(student_scores, minute, mean_eng, speaking_gini)

        snapshot = ClassSnapshot(
            minute=minute,
            mean_engagement=round(mean_eng, 3),
            median_engagement=round(median_eng, 3),
            std_engagement=round(std_eng, 3),
            student_scores=student_scores,
            patterns_detected=patterns,
            speaking_gini=round(speaking_gini, 3),
            active_speakers=active_speakers,
            total_students=n,
        )
        self._history.append(snapshot)
        return snapshot

    def _compute_gini(self) -> float:
        """Compute Gini coefficient of speaking time distribution."""
        values = list(self._student_speaking_totals.values())
        if not values or sum(values) == 0:
            return 0.0
        n = len(values)
        values_sorted = sorted(values)
        cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(values_sorted))
        return cumulative / (n * sum(values)) if sum(values) > 0 else 0.0

    def _detect_patterns(self, scores: List[EngagementScore], minute: int,
                         mean_eng: float, gini: float) -> List[Dict]:
        """Detect class-level engagement patterns (SA Level 2)."""
        patterns = []

        # Energy decay: compare to first 5 minutes
        if len(self._history) >= 5:
            early_mean = sum(h.mean_engagement for h in self._history[:5]) / 5
            decay = early_mean - mean_eng
            if decay > 0.10:
                severity = "mild" if decay < 0.20 else "moderate" if decay < 0.30 else "severe"
                patterns.append({
                    "type": "energy_decay",
                    "severity": severity,
                    "value": round(decay, 3),
                    "message": f"Class engagement dropped {decay:.0%} from session start",
                })

        # Equity imbalance
        if gini > 0.5:
            severity = "mild" if gini < 0.65 else "moderate" if gini < 0.80 else "severe"
            patterns.append({
                "type": "equity_imbalance",
                "severity": severity,
                "value": round(gini, 3),
                "message": f"Speaking time concentrated (Gini={gini:.2f})",
            })

        # Confusion cluster
        recent_confused = [s for s in scores if s.is_confused]
        if len(recent_confused) >= 3:
            patterns.append({
                "type": "confusion_cluster",
                "severity": "mild" if len(recent_confused) < 4 else "moderate" if len(recent_confused) < 6 else "severe",
                "value": len(recent_confused),
                "message": f"{len(recent_confused)} students signaling confusion",
                "students": [s.student_id for s in recent_confused],
            })

        # Silent majority
        silent_count = sum(1 for s in scores if not s.contributing_signals or s.contributing_signals == ["camera"])
        silent_ratio = silent_count / len(scores) if scores else 0
        if silent_ratio > 0.5:
            patterns.append({
                "type": "silent_majority",
                "severity": "mild" if silent_ratio < 0.65 else "moderate" if silent_ratio < 0.80 else "severe",
                "value": round(silent_ratio, 3),
                "message": f"{silent_ratio:.0%} of students silent",
            })

        # Fade cascade
        disengaged = [s for s in scores if s.state == "disengaged"]
        if len(disengaged) >= 3 and len(self._history) >= 2:
            prev_disengaged = sum(1 for s in self._history[-1].student_scores if s.state == "disengaged")
            if len(disengaged) > prev_disengaged + 1:
                patterns.append({
                    "type": "fade_cascade",
                    "severity": "moderate",
                    "value": len(disengaged),
                    "message": f"Rapid disengagement: {len(disengaged)} students now disengaged",
                })

        return patterns

    def get_recommendations(self, snapshot: ClassSnapshot) -> List[Dict]:
        """
        SA Level 3: Generate actionable recommendations from patterns.
        Maps patterns to instructor interventions.
        """
        recommendations = []

        for pattern in snapshot.patterns_detected:
            ptype = pattern["type"]
            severity = pattern["severity"]

            if ptype == "energy_decay":
                if severity == "severe":
                    recommendations.append({
                        "priority": "high",
                        "action": "breakout",
                        "message": f"Participation dropped {pattern['value']:.0%} since session start. Consider a 5-minute breakout activity to re-engage.",
                        "evidence": pattern,
                    })
                elif severity == "moderate":
                    recommendations.append({
                        "priority": "medium",
                        "action": "poll",
                        "message": f"Energy declining ({pattern['value']:.0%} drop). A quick poll or discussion prompt could help.",
                        "evidence": pattern,
                    })
                else:
                    recommendations.append({
                        "priority": "low",
                        "action": "pace_change",
                        "message": "Slight energy dip. Consider varying pace or asking a question.",
                        "evidence": pattern,
                    })

            elif ptype == "equity_imbalance":
                recommendations.append({
                    "priority": "high" if severity == "severe" else "medium",
                    "action": "equity_intervention",
                    "message": f"Discussion dominated by few voices (Gini={pattern['value']:.2f}). Consider cold-calling quieter students or using think-pair-share.",
                    "evidence": pattern,
                })

            elif ptype == "confusion_cluster":
                recommendations.append({
                    "priority": "high",
                    "action": "clarification",
                    "message": f"{pattern['value']} students appear confused. Consider pausing for clarification or re-explaining the current concept.",
                    "evidence": pattern,
                    "affected_students": pattern.get("students", []),
                })

            elif ptype == "silent_majority":
                recommendations.append({
                    "priority": "medium",
                    "action": "activation",
                    "message": f"{pattern['value']:.0%} of class is silent. Try a round-robin, poll, or chat prompt to activate participation.",
                    "evidence": pattern,
                })

            elif ptype == "fade_cascade":
                recommendations.append({
                    "priority": "high",
                    "action": "breakout",
                    "message": "Multiple students disengaging rapidly. A breakout or activity shift is strongly recommended.",
                    "evidence": pattern,
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

        return recommendations

    def get_history(self) -> List[ClassSnapshot]:
        """Return full scoring history for this session."""
        return self._history

    def reset(self):
        """Reset scorer for a new session."""
        self._history.clear()
        self._student_speaking_totals.clear()
        self._student_chat_counts.clear()
        self._confusion_signals.clear()
