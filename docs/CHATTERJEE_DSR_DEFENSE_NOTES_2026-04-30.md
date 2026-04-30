# Dr. Chatterjee Defense Notes — IST505 Phase 4

Purpose: quick grading-language defense for the Phase 4 submission. Use this when deciding what to paste, what to say in group review, and how to answer direct methodology questions.

## The shortest defensible claim

The artifact is an Instructional Decision Support System for synchronous online teaching. SAGE is the formative simulation environment used to evaluate whether the IDSS can convert observable classroom signals into transparent, rule-based advisory prompts and structured instructor-response data.

Do not claim that the system measures engagement, learning, attention, or instructor effectiveness in real classrooms. Claim that it supports formative evaluation of an advisory workflow.

## What Dr. Chatterjee is likely checking

| Likely question | Best answer |
|---|---|
| What is the artifact? | IDSS dashboard + recommendation engine + response taxonomy + SAGE evaluation environment. |
| What DSR artifact types are represented? | Construct: five-way instructor response taxonomy. Model: situation-awareness signal-to-pattern-to-action pipeline. Method: simulation-based formative evaluation. Instantiation: working dashboard, simulator, metrics, export. |
| Why is this not just another dashboard? | It combines institutional context sensitivity, demographic/behavior separation, instructor agency as measurable response behavior, and simulation-based formative evaluation. |
| How are recommendations created? | Rule-based pattern mapping from observable participation signals. LLMs may enrich simulated student dialogue only; they do not decide recommendations. |
| Why rule-based instead of ML? | Phase 4 evaluates transparency and instructor interpretation, not predictive optimization. Rule-based logic makes every recommendation traceable to evidence and literature. |
| What does "engagement" mean here? | The artifact avoids that claim. It measures observable participation plus a thin attention proxy; emotional, cognitive, social engagement, and learning are out of scope. |
| Why remove camera? | Camera state is privacy-, access-, culture-, disability-, and bandwidth-sensitive. It is rendered as non-scoring context only and excluded from both composite scoring and institutional differentiation. |
| What is the evaluation strategy? | FEDS: artificial + ex ante/formative for Phase 4, plus a hosted-deployment live-meeting validation receipt that begins to populate the naturalistic ex post quadrant. Sustained multi-instructor longitudinal validation is identified as future work beyond the scope of this course project. |
| What is measured? | User-centric metrics (SUS, TAM usefulness, NASA-TLX, trust, satisfaction), artifact telemetry (precision, throttle effectiveness, latency, response taxonomy, deltas), and qualitative interview themes. |
| What are the limits? | Simulation primary; no IRB human-subject data yet; no live-classroom efficacy claim across multiple instructors and full course terms; no Canvas integration. Live Zoom hosted-deployment validation is included as a deployment receipt. |

## Hevner seven-guideline defense

| Guideline | One-sentence defense |
|---|---|
| Design as Artifact | The project produces a working IDSS instantiation plus the SAGE evaluation environment. |
| Problem Relevance | Online instructors must interpret fragmented Zoom-era classroom signals under time pressure. |
| Design Evaluation | Phase 4 defines formative mixed-methods evaluation and instrumented simulation traces. |
| Research Contributions | The contribution is context-sensitive, bias-aware, agency-preserving advisory support, not generic AI recommendations. |
| Research Rigor | Features map to Endsley, Sweller, learning analytics advising mode, human-AI interaction guidelines, and FEDS. |
| Design as Search | The build shows iterative refinement from professor feedback: engagement reframed, camera removed, metrics/export added. |
| Communication | The paper supplies screenshots, survey instruments, artifact walkthrough, metrics definitions, and scope limits. |

## FEDS positioning

Phase 4 is best described as artificial + ex ante/formative.

Why: the artifact is evaluated in a controlled simulation environment before full live classroom deployment. This is appropriate because the project is still establishing technical coherence, interpretability, measurement surfaces, and evaluation instrumentation.

Do not call Phase 4 naturalistic or summative. Live Zoom validation against a real meeting on the hosted deployment is a deployment receipt that begins to touch the naturalistic ex post quadrant, but a single hosted-meeting receipt is not a sustained naturalistic classroom study.

## Knowledge contribution position

Gregor and Hevner framing: primarily Improvement, with an Exaptation element.

Improvement: instructor dashboards and learning analytics already exist, but this artifact improves the design space through institutional context sensitivity, demographic/behavior separation, response taxonomy, and instrumented formative simulation.

Exaptation: situation-awareness theory from dynamic decision environments is adapted to synchronous online teaching.

## Recommendation engine defense

The recommendation engine is intentionally simple enough to inspect. That is a methodological strength at Phase 4, not a weakness. The evaluation asks whether instructors understand, trust, use, modify, or reject advisory prompts when the evidence is visible. A black-box recommender would make that harder to evaluate and would weaken the professor's Phase 3 request for clearer links between literature, design features, and evaluation.

The five implemented pattern types are:

| Pattern | What it catches | Literature/design rationale |
|---|---|---|
| energy_decay | Class-wide participation decline | Situation awareness projection; cognitive-load / pacing concern |
| equity_imbalance | Participation concentrated in few voices | Advising-mode analytics; equitable instructional response |
| confusion_cluster | Multiple simultaneous confusion signals | Cognitive load and sensemaking |
| silent_majority | Majority with no contributing observable signals | Situation awareness comprehension, with explicit caution against assuming disengagement |
| fade_cascade | Rapid sequential decline | Early advisory prompt before pattern compounds |

## One-minute oral answer

"Our Phase 4 evaluation is formative and simulation-primary, with a live-deployment receipt from a real Zoom meeting against the hosted webhook. The artifact is the IDSS dashboard; SAGE is the controlled evaluation environment. We are not claiming to measure true engagement or improve real classroom outcomes. We are evaluating whether the artifact can take observable participation signals, detect transparent rule-based patterns, surface evidence-backed advisory prompts, and record how instructors respond through a five-way taxonomy. That gives us DSR evidence at this stage: technical feasibility, interpretability, structured response data, and a deployment receipt; sustained multi-instructor longitudinal validation is identified as future work beyond the scope of this course project."

## Zoom webhook email posture

Zoom disabled the lhr.life webhook because the tunnel URL was not persistently responsive. That does not falsify the artifact. It means the public live webhook path needs a stable deployment URL before it can be cited as live validation.

For the paper, use this wording:

> The Zoom live path is implemented end-to-end: HMAC-SHA256 signature verification, fixture-tested ingestion, registered Zoom Marketplace App, and validation against a real Zoom meeting on the hosted deployment. The resulting per-tick JSON export is the live-validation receipt cited alongside the analytical evaluation. Sustained multi-instructor longitudinal validation is identified as future work beyond the scope of this course project.

Render deployment or a reserved ngrok domain is the durable fix. Reusing an ephemeral tunnel is rehearsal-only.

