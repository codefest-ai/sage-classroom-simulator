# IST 505 One-Page Meeting Brief
## Working Artifact Status, Safe Claims, and Next Writing Moves

**Purpose:** Give the group a clean, truthful summary of what is already built, what we can safely claim in Phase 3, and which supporting docs exist but may not have been circulated yet.

### 1. Working Framing

**Working artifact:** Instructional decision-support prototype for synchronous online teaching

**Functional label:** IDSS (Instructional Decision Support System)

**Demo / sandbox label:** SAGE (Simulated Agent-Generated Evaluation)

**Best current framing:** The class artifact is the instructional decision-support prototype itself. SAGE is the simulation and evaluation environment used to evaluate and refine that prototype before real-world deployment.

### 2. What We Can Safely Say Right Now

- We have a working prototype that simulates synchronous online classrooms and displays instructor-facing patterns, alerts, and recommendations.
- We have university presets that produce different classroom conditions based on institutional context.
- We have an Instructor Response Taxonomy that treats the instructor as a decision-maker rather than a passive recipient of recommendations.
- We have an LLM-powered simulation mode in server mode, plus a rule-based mode for faster controlled runs.
- We have a prototype closed loop: classroom state -> dashboard recommendation -> professor response -> intervention -> changed classroom state.

### 3. Strongest Contribution Claims

Our strongest novelty claim is **not** "we added AI recommendations."

Our stronger claims are:

- **Institutional context sensitivity:** the same dashboard/scenario can produce different recommendation patterns across different university contexts.
- **Composition-behavior separation:** demographics affect classroom composition, but they do not directly drive behavioral scoring.
- **Instructor agency as a construct:** the Response Taxonomy measures how instructors use, modify, or reject AI support.
- **Simulation-based formative evaluation:** SAGE provides a way to test and refine the instructional decision-support prototype before real classroom deployment.

### 4. Claims That Need Careful Wording

- Do **not** say the system is fully validated.
- Do **not** say live Zoom integration is production-ready; it is an optional Zoom/webhook path for future live testing.
- Do **not** say no other system offers AI recommendations unless we cite specific competing systems.
- Do **not** imply demographics cause engagement behavior; our own design rationale explicitly rejects that move.

### 5. Best Short Pitch for the Meeting

> We are building a context-adaptive instructional decision-support prototype for synchronous online learning and evaluating it through SAGE, a classroom simulation environment. The novelty is not simply AI recommendations, but institutional context sensitivity, explicit separation of demographics from behavior modeling, and a response taxonomy that measures how instructors actually use AI support. The current build supports formative evaluation and proof of concept, not full validation yet.

### 6. Key Existing Docs The Group Should Know About

These already exist in the repo and can support the Phase 3 writeup:

- [README.md](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/README.md)
- [PHASE3_ARTIFACT_SPEC_2026-04-02.md](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/docs/PHASE3_ARTIFACT_SPEC_2026-04-02.md)
- [DEMOGRAPHIC_DESIGN_RATIONALE.md](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/docs/DEMOGRAPHIC_DESIGN_RATIONALE.md)
- [DSR_DIFFERENTIATION_SPEC.md](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/docs/DSR_DIFFERENTIATION_SPEC.md)
- [EVALUATION_ROADMAP.md](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/docs/EVALUATION_ROADMAP.md)
- [LLM_SIMULATION_METHODOLOGY.md](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/docs/LLM_SIMULATION_METHODOLOGY.md)
- [TEAMS_UPDATE_LLM.md](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/docs/TEAMS_UPDATE_LLM.md)

### 7. Immediate Group Writing Priorities

- Tighten the problem statement around situation awareness, cognitive load, and instructor decision support.
- Reposition novelty away from "AI recommendations" and toward context sensitivity, bias-aware modeling, and instructor agency.
- Turn the theory base into explicit design principles.
- Clarify that current evidence is formative / proof-of-concept evaluation.
- Decide which of the existing internal docs should be cited, summarized, or converted into Phase 3 prose.

### 8. Suggested Division of Labor

- **Evren:** demo, screenshots, technical description, proof-of-concept narrative, artifact spec
- **Writing team:** literature gaps, competing systems, design principles, evaluation framing
- **All:** agree on one honest novelty statement and one evaluation story
