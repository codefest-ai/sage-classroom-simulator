"""
NLP Analysis — Confusion detection, sentiment, and participation patterns from chat.

Pure rule-based (no external dependencies). Designed for the simulation context
where chat messages are generated from templates with known patterns.

For production use with real student chat, this would need a proper NLP pipeline.
For the DSR evaluation, rule-based detection is more controllable and reproducible.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


# ============================================================
# CONFUSION DETECTION PATTERNS
# ============================================================

CONFUSION_PATTERNS = [
    # Direct confusion signals
    (r"\b(confused|lost|don'?t understand|don'?t get it)\b", 0.9, "explicit_confusion"),
    (r"\b(what|huh|wait)\s*\?", 0.6, "question_marker"),
    (r"\bcan (you|someone) (explain|repeat|clarify|go back)\b", 0.85, "clarification_request"),
    (r"\b(what does .+ mean|what is .+)\?", 0.7, "definition_request"),
    (r"\bi('m| am) (totally )?(lost|confused)\b", 0.95, "self_report_confusion"),
    (r"\b(help|stuck|struggling)\b", 0.75, "help_signal"),
    (r"\bcan we (go back|slow down|pause)\b", 0.8, "pace_request"),
    (r"\b(doesn'?t make sense|not following)\b", 0.85, "comprehension_failure"),

    # Indirect confusion signals
    (r"\bwhich (slide|page|section)\b", 0.5, "navigation_confusion"),
    (r"\bsorry.+(repeat|missed|zoned)\b", 0.6, "attention_lapse"),
    (r"\bis this going to be on the (exam|test|quiz)\b", 0.4, "anxiety_signal"),
]

# ============================================================
# ENGAGEMENT SENTIMENT PATTERNS
# ============================================================

POSITIVE_PATTERNS = [
    (r"\b(great|interesting|fascinating|love|excellent|agree)\b", 0.7),
    (r"\b(building on|connects to|relates to)\b", 0.8),
    (r"\bin my experience\b", 0.6),
    (r"\b(good point|well said|exactly)\b", 0.7),
    (r"\bthis (reminds me of|is similar to)\b", 0.6),
]

NEGATIVE_PATTERNS = [
    (r"\b(disagree|wrong|incorrect|no way)\b", 0.5),
    (r"\b(boring|pointless|waste of time)\b", 0.8),
    (r"\b(this (doesn'?t|won'?t) work)\b", 0.6),
]

NEUTRAL_PATTERNS = [
    (r"^(ok|sure|yes|no|thanks|noted|interesting)$", 0.9),
    (r"^[\+1👍🔥💯]+$", 0.8),
]


@dataclass
class ChatAnalysis:
    """Analysis result for a single chat message."""
    student_id: str
    minute: int
    text: str
    confusion_score: float        # 0.0-1.0
    confusion_type: Optional[str] # Category of confusion detected
    sentiment: str                # positive / negative / neutral
    sentiment_score: float        # 0.0-1.0
    is_question: bool
    is_substantive: bool          # >20 chars, not just reaction
    engagement_signal: str        # "active", "minimal", "none"
    topics_mentioned: List[str]


@dataclass
class ChatSummary:
    """Aggregated chat analysis for a time window."""
    minute_start: int
    minute_end: int
    total_messages: int
    unique_participants: int
    confusion_count: int
    confusion_ratio: float
    mean_sentiment: float
    questions_asked: int
    substantive_ratio: float
    dominant_topics: List[str]
    flagged_messages: List[ChatAnalysis]


class ChatAnalyzer:
    """Analyzes simulated chat messages for engagement signals."""

    def __init__(self):
        self._message_history: List[ChatAnalysis] = []
        self._topic_counts: Dict[str, int] = {}

    def analyze_message(self, student_id: str, minute: int, text: str) -> ChatAnalysis:
        """Analyze a single chat message."""
        if not text or not text.strip():
            return ChatAnalysis(
                student_id=student_id, minute=minute, text="",
                confusion_score=0.0, confusion_type=None,
                sentiment="neutral", sentiment_score=0.5,
                is_question=False, is_substantive=False,
                engagement_signal="none", topics_mentioned=[]
            )

        text_clean = text.strip()
        text_lower = text_clean.lower()

        # Confusion detection
        confusion_score = 0.0
        confusion_type = None
        for pattern, weight, ctype in CONFUSION_PATTERNS:
            if re.search(pattern, text_lower):
                if weight > confusion_score:
                    confusion_score = weight
                    confusion_type = ctype

        # Sentiment analysis
        pos_score = 0.0
        for pattern, weight in POSITIVE_PATTERNS:
            if re.search(pattern, text_lower):
                pos_score = max(pos_score, weight)

        neg_score = 0.0
        for pattern, weight in NEGATIVE_PATTERNS:
            if re.search(pattern, text_lower):
                neg_score = max(neg_score, weight)

        is_neutral = False
        for pattern, weight in NEUTRAL_PATTERNS:
            if re.search(pattern, text_lower):
                is_neutral = True

        if is_neutral and pos_score == 0 and neg_score == 0:
            sentiment = "neutral"
            sentiment_score = 0.5
        elif pos_score > neg_score:
            sentiment = "positive"
            sentiment_score = 0.5 + pos_score * 0.5
        elif neg_score > pos_score:
            sentiment = "negative"
            sentiment_score = 0.5 - neg_score * 0.5
        else:
            sentiment = "neutral"
            sentiment_score = 0.5

        # Question detection
        is_question = "?" in text_clean

        # Substantive check
        is_substantive = len(text_clean) > 20 and not is_neutral

        # Engagement signal
        if is_substantive or is_question:
            engagement_signal = "active"
        elif len(text_clean) > 3:
            engagement_signal = "minimal"
        else:
            engagement_signal = "none"

        # Topic extraction (simple keyword matching)
        topics = self._extract_topics(text_lower)

        analysis = ChatAnalysis(
            student_id=student_id,
            minute=minute,
            text=text_clean,
            confusion_score=confusion_score,
            confusion_type=confusion_type,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            is_question=is_question,
            is_substantive=is_substantive,
            engagement_signal=engagement_signal,
            topics_mentioned=topics,
        )

        self._message_history.append(analysis)
        return analysis

    def get_window_summary(self, minute_start: int, minute_end: int) -> ChatSummary:
        """Summarize chat activity over a time window."""
        window = [m for m in self._message_history if minute_start <= m.minute <= minute_end]

        if not window:
            return ChatSummary(
                minute_start=minute_start, minute_end=minute_end,
                total_messages=0, unique_participants=0,
                confusion_count=0, confusion_ratio=0.0,
                mean_sentiment=0.5, questions_asked=0,
                substantive_ratio=0.0, dominant_topics=[],
                flagged_messages=[]
            )

        unique = set(m.student_id for m in window)
        confused = [m for m in window if m.confusion_score > 0.5]
        questions = sum(1 for m in window if m.is_question)
        substantive = sum(1 for m in window if m.is_substantive)

        sentiments = [m.sentiment_score for m in window]
        mean_sent = sum(sentiments) / len(sentiments) if sentiments else 0.5

        # Topic frequency
        all_topics: Dict[str, int] = {}
        for m in window:
            for t in m.topics_mentioned:
                all_topics[t] = all_topics.get(t, 0) + 1
        dominant = sorted(all_topics.keys(), key=lambda k: all_topics[k], reverse=True)[:5]

        return ChatSummary(
            minute_start=minute_start,
            minute_end=minute_end,
            total_messages=len(window),
            unique_participants=len(unique),
            confusion_count=len(confused),
            confusion_ratio=len(confused) / len(window) if window else 0.0,
            mean_sentiment=round(mean_sent, 3),
            questions_asked=questions,
            substantive_ratio=round(substantive / len(window), 3) if window else 0.0,
            dominant_topics=dominant,
            flagged_messages=confused,
        )

    def _extract_topics(self, text: str) -> List[str]:
        """Simple keyword-based topic extraction."""
        topic_keywords = {
            "methodology": ["method", "methodology", "approach", "framework", "design"],
            "theory": ["theory", "theoretical", "model", "construct", "concept"],
            "data": ["data", "dataset", "analysis", "statistics", "numbers", "graph", "chart"],
            "practice": ["practice", "practical", "real-world", "application", "example", "industry"],
            "literature": ["reading", "paper", "article", "literature", "research", "study"],
            "assignment": ["assignment", "homework", "project", "deliverable", "deadline", "exam", "test"],
            "technology": ["technology", "tool", "platform", "software", "code", "implementation"],
            "collaboration": ["group", "team", "together", "partner", "breakout", "discuss"],
        }

        found = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                found.append(topic)
                self._topic_counts[topic] = self._topic_counts.get(topic, 0) + 1

        return found

    def get_confusion_timeline(self) -> List[Dict]:
        """Return timeline of confusion events for visualization."""
        confused = [m for m in self._message_history if m.confusion_score > 0.5]
        return [
            {
                "minute": m.minute,
                "student_id": m.student_id,
                "text": m.text,
                "score": m.confusion_score,
                "type": m.confusion_type,
            }
            for m in confused
        ]

    def reset(self):
        """Reset for new session."""
        self._message_history.clear()
        self._topic_counts.clear()
