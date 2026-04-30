# Phase 3 Draft
## Working Title: Context-Adaptive Instructional Decision Support for Synchronous Online Teaching

**Working note:** This draft is designed to turn the current repo materials into a submission-shaped document for IST 505 Phase 3. It is intentionally conservative about claims that still need literature citations or stronger validation evidence.

## 1. Problem Statement

In synchronous online learning environments, instructors must continuously interpret multiple streams of partial and fast-changing information, including chat activity, participation patterns, silence, confusion signals, and changes in class energy. Existing dashboards and analytics tools can surface behavioral indicators, but instructors still face a cognitive burden in deciding what those indicators mean and whether intervention is warranted. This creates a situation-awareness problem: instructors may perceive signals without fully comprehending their significance or projecting how engagement is likely to evolve. The proposed artifact addresses this problem by supporting instructor sensemaking and intervention selection in real time, while preserving instructor agency rather than replacing it.

## 2. DSR Artifact Description

The Phase 3 artifact is a working instructional decision-support prototype for synchronous online teaching. In this draft, the artifact is described functionally rather than through a final product name because the naming decision is still provisional.

In the current implementation, the artifact is demonstrated and formatively evaluated through **SAGE** (Simulated Agent-Generated Evaluation), a classroom simulation and evaluation environment that generates classroom states, routes them through the dashboard, and records instructor responses before live deployment.

These artifacts collectively cover multiple DSR artifact types:

| DSR artifact type | Project element |
|---|---|
| Construct | Instructor Response Taxonomy |
| Model | Situation-awareness pipeline from signal perception to comprehension and projection |
| Method | Simulation-based formative evaluation using scenario-driven classroom runs |
| Instantiation | Dashboard prototype, simulation engine, university presets, and professor-response loop |

## 3. What Is Unique Or Novel

The novelty of the project should not be framed as merely adding AI-generated recommendations to an instructor dashboard. A more defensible claim is that the project combines three contributions that are rarely treated together.

First, the artifact is **institutionally adaptive**: the same dashboard and scenario can produce different recommendation patterns depending on institutional context. Second, the design explicitly separates **demographic composition from behavioral modeling**, allowing classroom composition to reflect real enrollment patterns without claiming that race, ethnicity, gender, or nationality directly determine engagement behavior. Third, the project introduces an **Instructor Response Taxonomy** that treats the instructor as an active decision-maker who may ignore, acknowledge, accept, modify, or reject a recommendation. This reframes instructor-AI interaction as a measurable construct rather than a black box.

An additional methodological contribution is that SAGE provides a **simulation-based evaluation environment** for the instructional artifact. This supports formative testing of recommendations, intervention effects, and instructor responses before moving to live classroom settings.

This methodological direction can be situated alongside prior generative-agent work such as Park et al. (2023), which is often summarized through the well-known example of agents in a simulated town spontaneously organizing a Valentine's Day party. In contrast, the present project applies shared-context agent simulation to classroom engagement and instructional decision support.

Taken together, the contribution is a context-adaptive instructional decision-support prototype whose novelty lies in how it combines institutional context sensitivity, bias-aware classroom modeling, and a measurable instructor response taxonomy within one artifact and one formative evaluation workflow. SAGE strengthens that contribution by providing a simulation-based environment for testing the artifact across repeatable scenarios before live classroom deployment.

## 4. Design Requirements And Principles

The current build implies the following design principles:

| ID | Principle | Rationale | Artifact expression |
|---|---|---|---|
| DP1 | Institutional context sensitivity | Online classrooms differ structurally across institutions and program formats | University presets with institutional modifiers |
| DP2 | Composition-behavior separation | Demographic realism should not require demographic stereotyping | Demographics describe classroom composition, not direct behavior rules |
| DP3 | Instructor agency preservation | Decision support should advise rather than dictate | Instructor Response Taxonomy and recommendation interface |
| DP4 | Cognitive load reduction | Instructors need aggregated interpretation, not only raw behavioral streams | Dashboard summaries, alerts, and grouped patterns |
| DP5 | Situation awareness escalation | Perception alone is insufficient for intervention | Signals feed into pattern detection and forward-looking recommendations |
| DP6 | Bias-aware evaluation | DSR should surface and reduce bias risks during artifact design | Explicit rejection of demographic-to-behavior mappings |
| DP7 | Risk-reduced formative testing | Early evaluation should be possible without immediate classroom deployment | SAGE as simulation sandbox for scenario testing |

### Kernel Theory To Feature Mapping

One of the main revision needs for Phase 3 is to show more explicitly how kernel theories inform concrete design features. The current project supports the following mapping:

| Kernel theory or literature base | Design implication | Current feature or artifact element |
|---|---|---|
| Endsley situation awareness | Move beyond raw signal display toward interpretation and projection | Signal collection, pattern detection, and intervention recommendations |
| Sweller cognitive load theory | Reduce extraneous cognitive burden on instructors | Dashboard aggregation, alerts, and summarized recommendation interface |
| Advising-mode literature in learning analytics | Recommendations should support action, not just mirror data | Intervention suggestions rather than raw metrics alone |
| Situated instructional decision-making literature | Different instructors and contexts require adaptive support | Multiple professor styles and institutional-context presets |
| Bias-aware and equity-oriented design | Avoid encoding demographic assumptions into learner behavior | Composition-behavior separation and rejection of demographic behavior rules |
| Design science evaluation literature | Use iterative formative evaluation before naturalistic deployment | Scenario-driven simulation and staged evaluation roadmap |

## 5. Form And Functions

The current proof-of-concept includes a dashboard prototype and a simulation engine that work together as a single demonstration environment.

Key functional elements include:

- A dashboard that displays classroom engagement patterns, alerts, and recommendations
- A simulation engine that generates minute-by-minute classroom states under repeatable scenarios
- University presets that shift classroom conditions across institutional contexts
- A professor-response loop that records how recommendations are accepted, modified, or rejected
- Multiple evaluation scenarios, including energy decay, equity imbalance, confusion clusters, and mixed full-session scenarios

The interface can be described in terms of a situation-awareness pipeline:

| Layer | Function | Example implementation |
|---|---|---|
| Perception | Collect classroom signals | Chat, speaking, reactions, silence, camera state, participation |
| Comprehension | Detect meaningful patterns | Confusion cluster, energy decay, speaking imbalance |
| Projection | Recommend possible interventions | Poll, breakout, pace change, clarification |

For the final Phase 3 submission, this section should include screenshots or diagrams of:

- Main dashboard layout
- Recommendation panel
- Instructor response area
- University preset comparison view
- Simulation-to-dashboard flow

## 6. Proof Of Concept Demonstration

The current proof of concept is implemented as a working prototype composed of:

- A Python-based simulator for synthetic classroom sessions
- A browser-based dashboard interface
- Scenario controls and university presets
- Rule-based and LLM-assisted simulation modes
- An optional Zoom/webhook ingestion path for future live testing

The prototype already supports:

- Scenario-driven runs with seeded reproducibility in rule-based mode
- LLM-powered student chat in server mode
- A professor-decision loop that can react to dashboard recommendations
- Exportable session traces and comparison scenarios

For the Phase 3 writeup, the proof-of-concept argument should emphasize that the project is already capable of demonstrating the artifact’s intended workflow end to end:

1. A classroom state is generated or ingested
2. The dashboard interprets the state and identifies patterns
3. The system presents interventions to the instructor
4. The instructor response is recorded
5. The next classroom state reflects that intervention context

## 7. Evaluation Approach And Artifact Impact

The evaluation story should distinguish clearly between current formative evidence and future summative evidence.

### Current formative evidence

- Design decision traces, especially the demographic design rationale
- Scenario-based simulation runs across multiple classroom conditions
- Comparison across institutional presets
- Observation of recommendation patterns and instructor-response behavior in the prototype

### Current impact claims we can support

- The artifact can detect and surface classroom patterns in a coherent dashboard interface
- The artifact can vary its outputs across institutional contexts
- The artifact can represent instructor response as a meaningful part of the evaluation loop
- The project demonstrates technical feasibility for simulation-based formative evaluation

### Future impact claims that need further study

- Whether instructors using the artifact make better decisions than those not using it
- Whether the dashboard reduces cognitive load in real teaching contexts
- Whether the recommendations improve student engagement outcomes in live classrooms
- Whether the prototype live-integration path works reliably in real deployment environments

Accordingly, the current evaluation claim is formative rather than summative. Phase 3 supports technical feasibility, coherence of the signal-to-recommendation workflow, context-sensitive variation across institutional presets, and traceable instructor-response behavior inside a controlled simulation environment. Claims about reduced cognitive load, improved instructional decisions, or better student outcomes require later human-subject or real-classroom studies and should be presented as future validation targets rather than completed findings.

## 8. Competing-Systems Positioning

The literature and related-systems section should avoid claiming that current tools are purely descriptive. A safer framing is that some current tools already provide analytics summaries and, in some cases, recommendation-like support. The differentiation argument should therefore focus on what this project combines that those systems typically do not foreground: institutional adaptation, explicit separation of demographic composition from behavior modeling, and a construct for measuring instructor response to AI support.

Commercial and research-facing systems already address parts of this space. Class Technologies adds instructor controls and engagement indicators to synchronous online teaching workflows, Engageli provides a purpose-built online classroom with participation monitoring and interaction tools, and Kulkarni and Eagle (2021) describe a real-time AI-powered educational dashboard that combines visualization with recommendation logic. The present artifact is therefore not positioned as the first system to surface engagement indicators or even recommendation-like support. Its differentiation is that it combines institutional context sensitivity, explicit separation of demographic composition from behavioral modeling, and a measurable instructor response construct within the same instructional decision-support workflow.

A useful structure for the final paper is:

1. Existing systems can surface behavioral indicators and sometimes suggest actions.
2. Those systems are not the central novelty target for this paper.
3. The present artifact is differentiated by context sensitivity, bias-aware modeling choices, and instructor agency as a measurable construct.

## Suggested Closing Paragraph

This project contributes an institutionally adaptive instructional decision-support concept and a simulation-based evaluation environment for synchronous online learning. Its main contribution is not simply the addition of AI recommendations, but the combination of context-sensitive recommendation behavior, bias-aware classroom modeling, and an instructor response construct that preserves agency while enabling evaluation. In its current form, the project offers a credible proof of concept and a strong basis for formative design science evaluation, while also identifying a clear path toward more naturalistic future validation.

## References

Amershi, S., Weld, D., Vorvoreanu, M., Fourney, A., Nushi, B., Collisson, P., ... & Horvitz, E. (2019). Guidelines for human-AI interaction. In *Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems*. https://doi.org/10.1145/3290605.3300233

Dell, C. A., Dell, T. F., & Blackwell, T. L. (2015). Applying universal design for learning in online courses: Pedagogical and practical considerations. *https://eric.ed.gov/?id=EJ1068401*

Endsley, M. R. (1995). Toward a theory of situation awareness in dynamic systems. *Human Factors, 37*(1), 32–64. https://doi.org/10.1518/001872095779049543

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. *MIS Quarterly, 28*(1), 75–105.

Kulkarni, A., & Eagle, M. (2021). Towards understanding the impact of real-time AI-powered dashboards on instructor decision-making. *Proceedings of the International Conference on Learning Analytics & Knowledge*.

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. In *Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology*. https://doi.org/10.1145/3586183.3606763

Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. *Cognitive Science, 12*(2), 257–285.

Van Leeuwen, A., Janssen, J., Rummel, N., & Brekelmans, M. (2019). Comparing teacher and student perspectives on the use of learning analytics dashboards. *British Journal of Educational Technology, 50*(6), 3038–3054.

Venable, J., Pries-Heje, J., & Baskerville, R. (2016). FEDS: A framework for evaluation in design science research. *European Journal of Information Systems, 25*(1), 77–89.

Wise, A. F., & Jung, Y. (2019). Teaching with analytics: Towards a situated model of instructional decision-making. *Journal of Learning Analytics, 6*(2), 53–69.

---

## Remaining Packaging Tasks

- Screenshots, diagrams, or UI sketches
- Group review and approval of the final novelty and evaluation wording
- Final packet refresh so the draft, artifact spec, and demo language stay aligned
