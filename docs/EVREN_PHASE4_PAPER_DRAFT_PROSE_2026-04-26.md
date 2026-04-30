# Evren — Phase 4 Paper Draft Prose
**Date:** 2026-04-26
**Purpose:** Paste-ready paragraphs for the Evren-owned sections in the Phase 4 paper draft. Voice matches existing draft (passive-future, third-person, instrument-grounded). Each section can be pasted directly under the corresponding empty header in `IST 505 Final Project Phase 4 (Draft).docx`; minor edits expected after group review.

---

## P3 — Behavioral-impact paragraph
**Goes immediately before:** the Analytical (Simulation) section under "Types of Evaluation."
**Why this section first:** Samantha noted in the Apr 26 group meeting that behavioral impact must be defined before the evaluation modality so that what is being evaluated is anchored before how it is evaluated.

> The artifact's intended behavioral impact on the instructor is twofold. First, the system aims to reduce the cognitive load of fragmented signal monitoring during synchronous online teaching by surfacing a single weighted observable-participation index in place of multiple disconnected raw indicators (chat scrolls, participant grids, poll dashboards, raised-hand notifications). Second, the system aims to prompt timely instructional micro-decisions, such as re-engaging quiet students, modulating overactive chat moments, or addressing apparent confusion clusters, that may otherwise be deferred or missed during simultaneous content delivery.
>
> Behavioral impact is operationalized through three complementary measurement surfaces. The first is instructor self-report, captured through the user-centric instruments described in Section 3 (NASA-TLX for cognitive load, the adapted TAM perceived-usefulness scale, the trust-in-AI-recommendation items, and the System Usability Scale). The second is observable instructor response behavior recorded within the system itself: the distribution of decisions across the five-way response taxonomy (ignore, acknowledge, accept, modify, reject) and the elapsed time between recommendation surface and instructor response. The third is participation-trajectory measurement around logged interventions: the artifact records the class-level observable-participation index immediately before and at a fixed window after each instructor decision, allowing the analytical section to report behavioral deltas attributable to specific interventions rather than to session drift alone. Together, these three surfaces ensure that behavioral impact claims are backed by both subjective instructor experience and objective in-system behavior, rather than by either alone.

---

## P1 — Analytical (Simulation) Evaluation section
**Goes in:** "Types of Evaluation → Analytical (Simulation)" — currently empty header.

> The analytical evaluation is conducted within SAGE, a Simulation and Formative-Evaluation Environment built specifically to exercise the Instructional Decision Support System (IDSS) under controlled and reproducible synchronous-classroom conditions. SAGE generates fifteen agent students per session, each instantiated from a parameterized behavioral profile (drift rate, attention span, speak tendency, chat frequency, breakout response) drawn from one of three institutional presets (CGU baseline graduate seminar; Georgia Tech large online program with working professionals; Howard small-department seminar with high social accountability). Institutional differentiation is structurally enforced at the preset layer rather than at the individual demographic layer, isolating cohort-level context from individual student attributes and avoiding bias inference from demographic data. Each profile drives observable participation signals (speaking time, chat activity, poll responses, hand raises, reaction events, silence gaps) tick-by-tick across a forty-five-minute simulated class.
>
> The IDSS consumes these signals through a deterministic five-signal weighted composite (speaking equity 30%, chat activity 25%, poll participation 25%, reaction frequency 15%, silence gap 5%; camera state is excluded from scoring on ethical grounds and rendered for presence context only) and detects five rule-based pattern classes (energy_decay, equity_imbalance, confusion_cluster, silent_majority, fade_cascade), each grounded in established kernel theory (Endsley situation awareness levels 2-3; Sweller cognitive load; Van Leeuwen advising-mode learning analytics). When a pattern threshold is met, the system emits a prioritized advisory recommendation card visible to the instructor, displaying the triggering pattern, the underlying observable evidence, the institutional context the session is configured for, the literature grounding for the pattern, and a candidate intervention.
>
> Within the Framework for Evaluation in Design Science (FEDS) proposed by Venable et al. (2016), SAGE positions this Phase 4 evaluation as **ex ante** (preceding deployment in a fully naturalistic setting), **formative** (oriented toward design improvement and feasibility demonstration rather than summative effect-size claims), and **artificial** (executed in a controlled simulation environment rather than under naturalistic classroom conditions). This positioning is appropriate for the artifact's current maturity: the IDSS is an instantiation under iterative refinement, and the goal of Phase 4 is to establish that the rule-based pattern-detection-to-recommendation-to-response loop functions coherently and produces evaluable signals that survey instruments and qualitative inquiry can be calibrated against in subsequent phases.
>
> SAGE is appropriate for this formative-artificial-ex-ante position because it satisfies three properties simultaneously. It produces controlled scenarios that all evaluator-instructors experience identically, isolating artifact effects from external classroom variability such as course content, student behavior, or class size. It exercises the full IDSS measurement-recommendation-response loop without requiring live student participants, satisfying the in-semester scope and the IRB-deferred posture described in Section 3. And it generates an exportable per-tick record (timeline, signals, pattern detections with evidence, instructor responses with metadata, and computed performance metrics) that the user-centric and outcome evaluations can be cross-referenced against in the analysis section. The live Zoom integration path is implemented end-to-end: webhook signature verification, fixture-tested ingestion, a registered Zoom Marketplace App, and validation against a hosted deployment endpoint with a real Zoom meeting; the resulting per-tick run is exported as the live-validation receipt cited alongside the analytical evaluation. Sustained naturalistic-classroom validation across multiple instructors and full course terms (which would more fully populate the **naturalistic ex post** quadrant of FEDS) is identified as future work beyond the scope of this course project.

---

## P2 — Performance Metrics section
**Goes as a new subsection under:** "Section 3: Measurement and metrics" — alongside the existing User-Centric Evaluation Metrics subsection. Add Performance Metrics before User-Centric, and reserve a third subsection for Outcome Metrics (Samantha-owned).

> **Performance Metrics**
>
> Because the IDSS is a rule-based advisory system rather than a learned classifier, the conventional performance vocabulary (accuracy, precision, recall, latency) is operationalized against the system's own deterministic specification rather than against external ground-truth student state. Four metrics are defined and continuously logged through the SAGE evaluation-run telemetry pipeline.
>
> *Pattern-detection precision* is defined as the proportion of pattern-trigger events whose underlying signal evidence is structurally complete and meets the published threshold for that pattern (for example, the silent_majority pattern requires that more than 50% of active students hold zero contributing observable signals across speaking, chat, polls, and reactions in the current minute). Because the pattern detection logic is deterministic and rule-based, this metric is expected to remain at 1.00 in correct operation; values below 1.00 indicate either an upstream code regression or a malformed evidence payload, both of which are caught and reported by the telemetry pipeline.
>
> *Recommendation throttling effectiveness* is defined as the proportion of duplicate within-cooldown pattern triggers that the system suppresses (a three-minute per-pattern cooldown is enforced server-side). The target value is at least 0.99, ensuring that the recommendation log is not flooded by repeated detections of the same standing condition and that each surfaced recommendation represents either a new event or a re-emerged condition after meaningful elapsed time.
>
> *System latency* is defined as the elapsed wall-clock time between the start of a simulation tick and the moment the resulting recommendation surfaces on the dashboard, measured per tick and reported as mean and 95th-percentile values. Target latency at the local-loop scale used in SAGE is below 200 ms; in practice, observed latency is dominated by single-digit-millisecond Python work and is well within the target during all evaluation runs.
>
> *Five-way response taxonomy adoption rate* is defined as the proportion of surfaced recommendations that receive an instructor response in any of the five categories (ignore, acknowledge, accept, modify, reject) versus those that remain unanswered. This is treated as a system-side outcome metric in the sense that the system is functioning as designed when adoption is high regardless of which category is selected; each of the five responses represents a valid disposition and a logged decision, in keeping with the sovereignty-first design principle that the instructor retains agency over every recommendation.
>
> All four metrics are exposed through the system's `/api/metrics` endpoint and bundled into the SAGE evaluation-run JSON export, so that user-centric instrument scores collected through the survey instruments described below can be cross-tabulated against the artifact's behavioral state at the time the response was given.

---

## P4 — Artifact Description section
**Goes as a standalone section near the front of the paper**, likely between the problem statement and the evaluation method. Confirm placement with Ahmed during Thursday integration. Includes a small figure list at the end; figures are produced by `scripts/capture_dashboard.py`.

> **Artifact Description**
>
> The Instructional Decision Support System is a browser-based dashboard that consumes synchronous-classroom signals in real time and surfaces rule-based advisory recommendations to the instructor. The interface is organized around five primary surfaces. The Class Participation Overview panel displays the weighted observable-participation composite as a single index, a count of active speakers, a speaking-equity Gini coefficient, and a pattern-detection counter, accompanied by an explicit scope statement that names which engagement dimensions are observable from Zoom signals (behavioral participation and an attention proxy) and which are deliberately out of scope (emotional, cognitive, and social engagement). The Student Status panel displays per-student participation state and confusion indicators with a visible "no observable signal" treatment that distinguishes silent presence from active disengagement. The Participation Timeline and Heatmap surfaces render the per-minute trajectory of the composite and the per-student-by-minute participation matrix. The Instructional Recommendations panel is the primary instructor decision surface: each recommendation card displays the triggering pattern, the observable signal evidence (such as a measured Speaking Gini value or a participation-decline percentage), the institutional preset the session is configured under, the literature grounding for that pattern (Endsley, Sweller, Van Leeuwen, Wise & Jung, Amershi as appropriate), and a candidate intervention, with a five-way response taxonomy (ignore, acknowledge, accept, modify, reject) and an optional rationale field.
>
> A System Performance Metrics panel beneath the recommendation panel exposes the four artifact-internal performance metrics defined in Section 3 (pattern-detection precision, throttling effectiveness, latency mean and 95th-percentile, five-way taxonomy adoption rate) and a behavioral-impact panel that displays per-response participation deltas around each logged instructor decision. A separate Live Signal Trace surface, visible when the dashboard is connected to a live Zoom meeting via the webhook ingestion path, shows the meeting context (topic, host, meeting identifier), the current signal status (waiting, presence-only, or rich), the supported live signal types, and a recent raw-event trace, so that an evaluator can see not only the final recommendations but also which inputs were available to produce them. A Classroom view renders the camera tile grid for context, with an explicit non-scoring caveat banner directly above the grid stating that camera state is rendered for presence context only and is excluded from both the participation composite and the institutional differentiation layer.
>
> The dashboard exports a single-shot SAGE evaluation run as a JSON artifact (or per-tick CSV) containing the full session metadata, timeline, ingested events, recommendations with evidence, instructor responses with metadata, and the performance-metrics snapshot. This export functions as the primary citable evaluation artifact for the analytical evaluation described above, and is also used for cross-referencing against user-centric survey responses in the analysis section.
>
> *Figures referenced in this section: (a) initial dashboard load, (b) dashboard during a simulation run with the participation overview populated, (c) a single recommendation card showing pattern, evidence, institutional context, and literature grounding, (d) the classroom view with camera-presence caveat, (e) the system performance metrics panel expanded, (f) a mid-run dashboard at minute fifteen of the full scenario. Figures are produced reproducibly via `scripts/capture_dashboard.py` and carry sidecar metadata recording the scenario, university preset, seed, and source-tree git SHA.*

---

## P5 (stub) — Section 7: Linking Evaluation Data → Research Questions
**Goes in:** "Section 7: Linking Evaluation Data to the Research Questions" — currently empty header.
**Owner:** Group / Ahmed (per meeting notes); this stub covers only the artifact-side data half so Ahmed has something to expand from. **Do not paste this stub directly without Ahmed's review** — the user-centric and outcome halves and the actual research-question wording are his slice.

> **Research questions and evaluation data sources.** This section maps each evaluation data source to the research questions it primarily answers, in keeping with the Design Science Research evaluation framework (Venable et al., 2016). The research questions are framed against the evaluation objective stated in Section 1 and address whether the artifact (1) improves instructors' interpretation of real-time classroom signals, (2) reduces cognitive load associated with monitoring fragmented engagement indicators, and (3) supports timely instructional decisions during synchronous online teaching.
>
> The table below maps each data source to its primary and secondary contribution to each research question. Cross-reference is intended: most research questions are answered by combining multiple data sources rather than any one in isolation.

| Data source | RQ1 (interpretation) | RQ2 (cognitive load) | RQ3 (timely decisions) |
|---|---|---|---|
| **System Usability Scale (SUS)** | secondary | secondary | secondary |
| **Adapted TAM perceived-usefulness scale** | primary | secondary | primary |
| **NASA-TLX cognitive load instrument** | secondary | **primary** | secondary |
| **Trust-in-AI-recommendation items (Section 3)** | primary | secondary | primary |
| **Overall satisfaction items** | secondary | secondary | secondary |
| **Five-way response taxonomy distribution (in-system)** | secondary | secondary | **primary** |
| **Per-response behavioral-impact deltas (in-system)** | secondary | secondary | **primary** |
| **Pattern-detection precision and throttling effectiveness (Section 3 performance metrics)** | n/a (system-side) | n/a | n/a (system-side) |
| **System latency (Section 3 performance metrics)** | secondary | **primary** | **primary** |
| **Semi-structured post-session interview** | **primary** | **primary** | **primary** |
| **SAGE evaluation-run export (artifact-side, JSON/CSV)** | secondary | secondary | secondary (provides ground for behavioral-delta computation; supports cross-tabulation with self-report) |

> *(Stub note for Ahmed: the **primary** designations on the artifact-side rows reflect what the system can directly demonstrate; the **primary** designations on the user-centric rows are placeholders pending Ahmed's review against the actual research-question wording. The performance-metric rows are tagged n/a for RQ1–RQ3 because they verify the system functions as designed rather than answering questions about instructor effectiveness; consider whether they belong in a separate Section 7.1 on system-validity claims rather than user-effectiveness claims.)*

---

## P6 — Recommendation Engine Design Rationale
**Goes in:** A short subsection after Artifact Description or under Measurement and Metrics.
**Purpose:** Directly answers Dr. Chatterjee's Phase 3 feedback to "think deeply" about the recommendation engine.

> **Recommendation Engine Design Rationale.** The recommendation engine is intentionally rule-based and advisory rather than machine-learned. This design choice follows from the evaluation stage of the artifact. In Phase 4, the goal is not to optimize a predictive model against ground-truth student state, but to evaluate whether instructors can interpret observable classroom signals, understand the basis for a suggested action, and decide how to respond. A rule-based engine makes the recommendation pathway transparent: each recommendation can be traced from an observable signal, to a detected pattern, to a literature-grounded candidate intervention.
>
> Five pattern classes are implemented because they correspond to the most common instructional decision problems surfaced by the kernel theories and the Phase 3 feedback: class-wide participation decline (`energy_decay`), concentrated participation (`equity_imbalance`), simultaneous confusion signals (`confusion_cluster`), low observable participation among a majority of students (`silent_majority`), and rapid sequential participation decline (`fade_cascade`). The system does not infer emotional, cognitive, or social engagement directly. It only identifies observable participation patterns that may warrant instructor attention.
>
> Recommendations are therefore framed as decision-support prompts rather than prescriptions. Each card displays the triggering signal evidence, the institutional preset context, the literature grounding, and a candidate instructional move. The instructor then records one of five responses: ignore, acknowledge, accept, modify, or reject. This five-way taxonomy is the key evaluation construct because it converts instructor judgment into analyzable response data without removing instructor agency. In DSR terms, the engine is not evaluated primarily as an autonomous recommender; it is evaluated as part of a human-in-the-loop artifact that supports situation awareness, reduces monitoring burden, and makes instructor response behavior measurable.

---

## P7 — DSR Rigor Mapping (Hevner et al., 2004)
**Goes in:** Near the evaluation-method discussion or as a short table in the appendix if space is tight.
**Purpose:** Makes the paper legible to a DSR grader.

| Hevner guideline | Phase 4 alignment |
|---|---|
| **G1: Design as an artifact** | The artifact is an instantiated IDSS dashboard plus SAGE simulation environment, recommendation engine, response taxonomy, and exportable evaluation trace. |
| **G2: Problem relevance** | The artifact addresses the instructor problem of interpreting fragmented synchronous-online classroom signals under time pressure. |
| **G3: Design evaluation** | Phase 4 proposes mixed-methods formative evaluation: controlled simulation, user-centric survey instruments, qualitative interviews, performance telemetry, and behavioral-response traces. |
| **G4: Research contributions** | The contribution is not "AI recommendations" alone. It is the combination of institutional context sensitivity, demographic/behavior separation, instructor response taxonomy, and simulation-based formative evaluation. |
| **G5: Research rigor** | Design features are tied to kernel theories: Endsley situation awareness, Sweller cognitive load, learning analytics advising-mode literature, human-AI interaction guidelines, and DSR evaluation literature. |
| **G6: Design as a search process** | The current artifact represents an iterative generate-test-refine cycle: prototype recommendations, inspect instructor response, verify telemetry, revise design limits, then prepare for later naturalistic validation. |
| **G7: Communication of research** | The paper communicates to both technical and managerial audiences through artifact screenshots, metrics definitions, survey instruments, evaluation plan, and scope limits. |

> This mapping positions Phase 4 as a design-evaluation milestone rather than as a final validation study. The artifact is sufficiently implemented to evaluate technical coherence and instructor-facing interpretability, while the paper explicitly identifies live-classroom efficacy claims and longitudinal student outcomes as future work beyond the scope of this course project.

---

## P8 — DSR Knowledge Contribution Positioning
**Goes in:** Optional short paragraph near novelty / contribution language.
**Purpose:** Prevents the project from sounding like routine dashboard implementation.

> Using Gregor and Hevner's (2013) knowledge contribution framing, this project is best positioned as an **improvement** contribution with an **exaptation** component. The problem domain is mature: instructors already face fragmented signal interpretation in online classrooms, and learning analytics dashboards already exist. The solution approach, however, improves on routine dashboarding by combining institutional context sensitivity, bias-aware composition/behavior separation, instructor-agency-preserving response taxonomy, and a simulation-based evaluation environment. The exaptation element comes from applying situation-awareness concepts originally developed for dynamic decision environments to synchronous online teaching. The resulting artifact is not claimed as a completed theory of instruction; it is an instantiated DSR prototype that generates design knowledge about how advisory learning-analytics systems can preserve instructor judgment while making response behavior measurable.

---

## P9 — Threats to Validity and Scope Limits
**Goes in:** End of evaluation method or before conclusion.
**Purpose:** Show methodological honesty before Dr. Chatterjee has to demand it.

> **Threats to validity.** Several threats are recognized. First, construct validity is limited because observable participation is not equivalent to engagement, attention, or learning. The artifact mitigates this threat by explicitly labeling its metric as an observable-participation proxy, excluding camera state from scoring, and showing the triggering evidence for each recommendation. Second, internal validity is limited because SAGE is a simulation environment: any measured change in participation trajectory after an instructor response is generated within the model rather than observed in a real classroom. This is appropriate for formative evaluation but cannot establish live instructional effectiveness. Third, external validity is limited because the fifteen simulated student profiles and three institutional presets do not represent all teaching contexts. The university presets are used to test context sensitivity, not to generalize behavior by institution. Fourth, statistical conclusion validity is limited because the current Phase 4 plan defines instruments and data sources but does not yet collect a sufficiently powered human-subject dataset. The paper therefore treats survey, interview, and telemetry measures as an evaluation plan and proof-of-concept structure, not as completed empirical validation.
>
> These limits are not failures of the artifact; they define the boundary between Phase 4 formative evaluation and later naturalistic validation. The appropriate Phase 4 claim is that the IDSS can produce transparent advisory recommendations from observable classroom signals, record instructor responses through a structured taxonomy, and export evaluable traces for mixed-methods analysis. Claims about improved learning, real instructor effectiveness, or live-classroom generalizability require IRB-approved follow-up research.

---

## P10 — Quantitative Analysis Approach Stub
**Goes in:** "Data Analysis -> Quantitative Data Analysis Approach" empty header.
**Owner:** Samantha + Ahmed; this is a draftable scaffold only.

> **Quantitative Data Analysis Approach.** Quantitative analysis will combine survey-scale scoring with artifact-generated telemetry. Survey instruments will first be scored according to their established procedures: SUS will be converted to the standard 0-100 score, TAM perceived usefulness will be averaged across the adapted usefulness items, NASA-TLX will be averaged using the raw TLX method, and trust and satisfaction items will be summarized as mean Likert-scale scores. Descriptive statistics (mean, standard deviation, median, and range) will be reported for each construct.
>
> If the final design uses a within-subjects comparison, such as instructors completing a scenario without the dashboard and then with the dashboard, paired-sample tests will be appropriate for comparing perceived workload, usefulness, trust, and response behavior across conditions. If the final design compares more than two conditions, such as different instructional scenarios or institutional presets, ANOVA or a non-parametric alternative may be more appropriate depending on sample size and distribution assumptions. Because the current course project is formative and sample size may be small, effect sizes and descriptive trends should be reported alongside significance tests rather than relying on p-values alone.
>
> Artifact telemetry will be analyzed descriptively and used to contextualize the survey results. Pattern-detection precision, throttling effectiveness, latency, response-taxonomy distribution, and behavioral-impact deltas will be exported from SAGE and aligned with participant survey or interview responses when available. This alignment allows the evaluation to ask not only whether participants reported the dashboard as useful, but also what the artifact was actually surfacing and how instructors responded during the session.

---

## Notes for Evren before pasting

- **Section ordering in the draft.** Put P3 (behavioral-impact) immediately before P1 (Analytical/SAGE). Put P2 (Performance Metrics) as a new subsection above the existing User-Centric Evaluation Metrics subsection. Put P4 (Artifact Description) wherever Ahmed indicates makes most sense — possibly as Section 2 (between the problem statement and the evaluation method).
- **Cross-references.** Every "Section 3" / "Section X" / "above" / "below" reference is approximate — adjust to match the final paper's section numbering during integration.
- **Citations format.** The paper currently uses APA-style with full author lists and DOIs in the References section. Inline references in the prose use Author (Year) format. Match this voice when integrating.
- **Word counts.** P1 ≈ 410 words, P2 ≈ 360, P3 ≈ 270, P4 ≈ 480, P6 ≈ 330, P8 ≈ 150, P9 ≈ 310, P10 ≈ 260. Trim if section budget is tight; the DSR positioning, recommendation-engine rationale, and validity limits are the load-bearing parts to preserve.
- **What is deliberately omitted.** Outcome metrics (Samantha-owned), stakeholder analysis (Samantha + Ahmed-Monday), and final Section 7 research-question linkage (group). P5 and P10 are scaffolds for Ahmed/Samantha review, not unilateral final prose.
