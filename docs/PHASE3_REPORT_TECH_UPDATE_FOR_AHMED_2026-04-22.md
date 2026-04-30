# Phase 3 Report — Technology Update for Ahmed

Drop-in replacement for the "development plan" portion of Section 7 (page 9 of the
submitted PDF). Reflects the actual Phase 4 build and answers the professor's margin
highlights about scoring mechanism, camera signal, and AI-vs-literature recommendation
generation.

---

## Revised paragraphs (replace "For development plan…" through end of Section 7)

The artifact is developed as a Python web dashboard for an Instructional Decision
Support System (IDSS). Python with the standard-library `http.server` / `ThreadingHTTPServer`
runs the backend with no external framework. The frontend is a single-page dashboard built
with vanilla HTML, CSS, and JavaScript; server-sent events stream live updates.

Recommendations are produced by a **rule-based pattern engine**, not a machine-learning
classifier or an LLM. Five observable-participation signals are aggregated with literature-
informed weights (speaking equity 30%, chat activity 25%, poll participation 25%, reaction
frequency 15%, silence gap 5%) into a single observable-participation index. Five patterns
(`energy_decay`, `equity_imbalance`, `confusion_cluster`, `silent_majority`, `fade_cascade`)
are detected via explicit thresholds, and each pattern maps to a pre-written advisory
message with its triggering evidence surfaced on the recommendation card
(e.g., "Triggered by Speaking Gini = 0.62, target < 0.50"). The instructor responds with
one of five actions — ignore, acknowledge, accept, modify, or reject — with a rationale
field. No recommendation fires without human consent.

Camera status is rendered for presence context only and is **not scored**. This follows
from the ethical concern that camera-on vs camera-off reflects bandwidth, home
environment, disability, and cultural factors more than participation. The Phase 4 weights
sum to 1.0 without camera, and the dashboard has a distinct "camera: no signal" state
so "no camera data observed" is visually different from "camera off."

The prototype is exercised inside the SAGE (Simulated Agent-Generated Evaluation)
environment, which generates synthetic classroom scenarios and agent behaviors so the
IDSS can be evaluated without recruiting a live class. An optional LLM component
(Groq / llama models) enriches simulated student chat dialogue for realism, but the LLM
does **not** alter engagement scoring or recommendation logic — those remain rule-based
and deterministic.

A prototype live-deployment path is integrated with Zoom. A webhook receiver ingests
meeting.participant_joined, participant_left, chat_message, and reaction events,
verifies each payload with HMAC-SHA256 against a shared secret, and feeds the stream
into the same scoring pipeline used by SAGE. This demonstrates that the same artifact
can be driven by either simulated signals or real Zoom session data.

Tooling summary:

| Layer | Technology |
|---|---|
| Backend | Python 3 (standard library: `http.server`, `ThreadingHTTPServer`, `json`, `hmac`) |
| Frontend | HTML, CSS, vanilla JavaScript, Server-Sent Events |
| Simulation environment | SAGE (Simulated Agent-Generated Evaluation) |
| Scoring engine | Rule-based weighted composite + pattern detection (Python) |
| Optional dialogue enrichment | Groq LLM (llama models) — simulated student chat only |
| Live deployment path | Zoom webhook ingestion with HMAC-SHA256 signature verification |
| Evaluation | Formative — SAGE scenarios + early user feedback survey (not full validation study) |

## Two small fixes elsewhere in the report

1. **Section 7, signal list (p.9):** remove "camera status" from the list of scored
   signals. The current sentence ("speaking participation, chat activity, poll responses,
   reactions, camera status, and silence gaps") should read: "speaking participation,
   chat activity, poll responses, reactions, and silence gaps." Add a follow-up sentence:
   "Camera status is rendered for presence context only and is not included in the score."

2. **Section 6, Artifact Functions (p.6):** the "recommendation engine generates adaptive
   instructional suggestions" sentence is accurate but reads ambiguously against the
   professor's "AI or literature?" comment. Suggest tightening to: "the recommendation
   engine applies rule-based pattern mapping to detected signal combinations and surfaces
   a pre-written advisory message with its triggering evidence."

## Why this addresses the professor's feedback

- **"How are recommendations created — AI or literature?"** The revised text explicitly
  names it as rule-based, lists the weights, and states the LLM is scoped to dialogue
  enrichment only.
- **"Camera is an ethical weakness."** Removed from the scored signal list; rationale given.
- **"Think deeply about your recommendation engine."** The revised text describes the
  mechanism concretely (weights, thresholds, pattern → advisory mapping, evidence shown
  on each card) rather than leaving it as a black box.
- **"Engagement is multi-dimensional."** The revised text calls the output
  "observable-participation index," not "engagement score," matching the dashboard UI.
