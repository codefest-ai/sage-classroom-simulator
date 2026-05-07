# Chatterjee Phase 4 Feedback Response

**Date:** 2026-05-07  
**Purpose:** Reconcile Dr. Chatterjee's Phase 4 grading comments with the actual SAGE / IDSS artifact and define the corrected final-presentation evaluation story.

---

## Bottom line

The feedback is directionally right. The project was close, but the submitted evaluation plan still leaned too hard on instructor perception and did not make enough use of the artifact's own objective logs. The fix is not to inflate the study. The fix is to make the evaluation design match what the artifact can actually produce:

- controlled SAGE scenarios;
- explicit sample-size target;
- objective instructor response logs;
- benchmarked decision-quality rubric;
- counterbalanced condition order;
- pipeline validation separate from user perception;
- clear definition of SAGE.

The live Zoom path now supports the same core loop: real Zoom signals -> rule-based recommendation -> instructor five-way response -> persisted evaluation receipt. It still does not actuate Zoom actions programmatically. The instructor executes the chosen action directly in Zoom.

---

## What "really works" should mean

For the final presentation, avoid the vague claim "the system improves engagement." The defensible claim is:

> The artifact transforms observable classroom signals into transparent advisory recommendations, preserves instructor agency through a five-way response taxonomy, and produces an exportable evidence trail that supports formative DSR evaluation.

This can be shown in two complementary ways:

1. **SAGE analytical evaluation:** controlled, repeatable scenarios with known signal patterns and exported telemetry.
2. **Live Zoom validation receipt:** a real meeting proves hosted ingestion and live instructor response logging against the deployment path.

The live demo is not the full empirical study. It is deployment-oriented validation. The evaluation study remains mixed-methods and formative.

---

## Feedback-to-fix mapping

### 1. Participant count missing

**Feedback:** The plan never states how many participants will be recruited.

**Correction:** State a concrete formative sample:

> The Phase 4 human evaluation will recruit a convenience sample of 10-15 instructor/evaluator participants, sufficient for formative usability and mixed-methods DSR evaluation but not for strong inferential claims. Quantitative statistics will be treated as descriptive or exploratory unless sample size and assumptions support paired tests.

If the group keeps paired t-tests and Cronbach's alpha, it must say those are exploratory with small-N caveats. Better: emphasize medians, effect sizes, confidence intervals where appropriate, and qualitative triangulation.

### 2. Behavioral change was only perceived

**Feedback:** Custom Likert items measure perceived behavioral change, not actual behavior.

**Correction:** Use the artifact logs:

- number of recommendations surfaced;
- number and distribution of instructor responses: ignore, acknowledge, accept, modify, reject;
- response latency from recommendation surface to decision;
- intervention type selected when accept/modify;
- rationale text;
- pre/post observable-participation deltas around accepted/modified interventions in SAGE.

This is now stronger because live Zoom decisions are also recorded in `professor_actions` and as `professor_action` events in Zoom history.

### 3. Decision quality lacks an objective benchmark

**Feedback:** Participants cannot objectively judge whether their own decisions were appropriate/timely.

**Correction:** Add a benchmark rubric. Do not ask only "was your decision good?"

For each scenario, define an expert-coded acceptable response set:

| Pattern | Acceptable responses | Poor response examples |
|---|---|---|
| `confusion_cluster` | acknowledge, accept clarification, modify to brief check-for-understanding | ignore repeated confusion without rationale |
| `equity_imbalance` | acknowledge, accept/modify to think-pair-share or structured turn-taking | cold-call low-signal students without rationale |
| `silent_majority` | acknowledge, poll, reflective pause, chat prompt | assume disengagement as fact |
| `energy_decay` | pace change, poll, brief activity shift | continue unchanged without rationale in severe case |

Decision quality can then be scored by independent raters or a pre-defined rubric:

- alignment with signal evidence;
- pedagogical appropriateness;
- timeliness;
- preservation of student dignity/accessibility;
- rationale quality.

This makes decision quality an external coding problem, not a self-rating problem.

### 4. Sequential within-subject design risks demand effects

**Feedback:** If everyone sees baseline first and dashboard second, they can guess the hypothesis.

**Correction:** Counterbalance order:

- Group A: baseline scenario -> dashboard scenario.
- Group B: dashboard scenario -> baseline scenario.

Use comparable but not identical scenarios so participants cannot merely repeat their prior decisions. Frame the study as comparing decision-support workflows, not "proving dashboard is better."

If the sample is very small, report this as a validity limitation rather than pretending it disappears.

### 5. RQ1 answered by perception alone

**Feedback:** RQ1 asks how raw classroom data becomes interpretable signals, but the evaluation only asks whether instructors perceive usefulness.

**Correction:** Split RQ1 evidence into two layers:

1. **Pipeline validation:** Does raw signal input produce the expected pattern and recommendation?
   - synthetic fixture tests;
   - scenario tests with known triggers;
   - pattern-detection precision;
   - false-positive and false-negative checks against scripted scenarios;
   - evidence completeness checks.

2. **Human interpretability:** Do instructors understand and trust the surfaced evidence?
   - TAM usefulness;
   - trust items;
   - interview questions;
   - think-aloud interpretation of a recommendation card.

RQ1 should not depend only on perception. The design pipeline must validate itself.

### 6. SAGE not defined

**Feedback:** The plan mentions SAGE but does not describe it.

**Correction:** Use this concise definition:

> SAGE (Simulated Agent-Generated Evaluation) is the project's controlled simulation and formative evaluation environment. It generates reproducible synchronous-classroom scenarios with 15 agent-student profiles, converts observable participation signals into dashboard inputs, surfaces rule-based advisory recommendations, records instructor responses through a five-way taxonomy, and exports the full evaluation trace for analysis.

---

## Corrected evaluation design

### Evaluation objective

Evaluate whether the IDSS:

- transforms observable classroom signals into interpretable instructional recommendations;
- reduces instructor monitoring burden during synchronous teaching scenarios;
- supports timely, pedagogically appropriate micro-decisions;
- preserves instructor agency and transparency.

### Evaluation types

- **Analytical:** SAGE simulation and pipeline validation.
- **Descriptive:** scenario walkthrough and expert review of recommendation cards.
- **Experimental / quasi-experimental:** small within-subject or counterbalanced comparison of baseline versus dashboard-supported decision-making.
- **Observational / deployment-oriented:** live Zoom validation receipt for webhook ingestion and instructor response logging.

### Participants

Target 10-15 instructor/evaluator participants for formative evaluation. If only classmates/team members are available, describe it as a convenience sample and do not make strong statistical claims.

### Quantitative measures

- NASA-TLX for workload;
- SUS for usability;
- TAM perceived usefulness / ease-of-use items;
- trust / reliance calibration items;
- task completion and decision latency;
- response taxonomy distribution;
- benchmark decision-quality rubric scores;
- pattern-detection precision / false-positive / false-negative checks;
- system latency and throttling effectiveness.

### Qualitative measures

Post-session questions should focus on interpretability and judgment:

- What did you think the recommendation was asking you to notice?
- Was the evidence on the card enough to decide whether to act?
- When did you accept, modify, reject, or ignore the system?
- Did any recommendation feel misleading or overconfident?
- What would you need before trusting this in a real class?
- Did the system preserve your agency as instructor?

### Analysis

Quantitative:

- descriptive statistics first;
- paired tests only if sample and assumptions allow;
- Wilcoxon signed-rank as fallback for small non-normal samples;
- effect sizes and confidence intervals over p-value theater;
- inter-rater agreement for decision-quality rubric if more than one rater.

Qualitative:

- thematic analysis over interview responses;
- code for interpretability, trust, agency, overclaim concern, cognitive-load relief, and actionability;
- use at least two coders if possible, or mark single-coder analysis as a limitation.

Comparative:

- baseline versus dashboard condition;
- counterbalanced order;
- scenario-level comparison by pattern type;
- artifact telemetry cross-tabulated with survey/interview response.

---

## Final presentation demo protocol

Use three short receipts, not one sprawling demo:

1. **Pipeline receipt:** run a SAGE scenario with known trigger and show recommendation evidence.
2. **Decision receipt:** click accept/modify/reject and show the response log / export.
3. **Live Zoom receipt:** start real Zoom meeting, generate chat/reaction/hand signals, show live card and record a five-way instructor response.

For the live Zoom demo, participants must be instructed to use observable signals the system actually receives:

- chat messages;
- reactions;
- raised hands;
- silence / no contribution;
- join/leave presence.

Do not rely on camera state or passive facial/attention inference. Those are intentionally out of scope.

---

## Recommended final answer to "Does it really work?"

> It works as a formative DSR artifact, not as a completed large-scale efficacy study. The system can ingest or simulate classroom signals, transform them into transparent rule-based recommendations, let the instructor decide through a five-way taxonomy, and export the whole trace for analysis. The revised evaluation design answers Chatterjee's critique by adding objective behavior logs, a decision-quality rubric, counterbalanced conditions, explicit sample size, and separate pipeline validation for RQ1. What remains future work is naturalistic multi-instructor classroom validation and programmatic actuation inside Zoom.

