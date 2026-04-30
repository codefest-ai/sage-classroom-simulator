# Phase 3 Artifact Spec
## Working Title: Context-Adaptive Instructional Decision Support for Synchronous Online Teaching

**Status:** authoritative working spec for IST 505 Phase 3

## 1. Artifact Purpose

The class artifact is a working instructional decision-support prototype for synchronous online teaching. Its purpose is to help instructors interpret fragmented classroom signals, recognize meaningful patterns, and choose possible interventions without replacing instructor judgment.

The artifact is being demonstrated and formatively evaluated through **SAGE** (Simulated Agent-Generated Evaluation), which currently serves as the simulation and evaluation environment around the artifact.

## 2. Primary Users

- University instructors teaching synchronous online courses
- Research team members evaluating how instructors interpret and respond to AI-supported recommendations

## 3. Core Inputs And Outputs

### Core inputs

- Participation and speaking patterns
- Chat activity and interaction signals
- Silence, drift, and confusion-related signals
- Institutional context presets that modify classroom conditions
- Scenario conditions and instructor response choices

### Core outputs

- Pattern detection and summarized class state
- Prioritized intervention recommendations
- Instructor response logging
- Session traces for formative evaluation

## 4. Instructor Response Taxonomy

The current artifact treats instructor response as part of the artifact story, not a side effect.

- `ignore`
- `acknowledge`
- `accept`
- `modify`
- `reject`

## 5. What Is Included Now

- Scenario-based classroom simulation
- Dashboard-based pattern detection and recommendation display
- Institutional presets / context sensitivity
- Instructor response tracking and action logging
- Multi-session server-backed demo support
- Rule-based and LLM-assisted simulation modes

## 6. Prototype-Path Only

- Zoom/webhook live-ingestion path
- Hosted deployment details
- LLM realism beyond the currently demonstrated workflow

These support the prototype and future extension path, but they are not the core artifact claim for Phase 3.

## 7. Future Work

- Real-world validation with instructors in live teaching contexts
- Stronger cognitive-load measurement in human-subject studies
- More robust live meeting integration
- Post-class separation of the broader simulation platform from the class artifact if needed

## 8. Current Claims We Can Support

- The artifact supports instructor sensemaking and intervention selection in a coherent prototype workflow.
- The current build can vary outputs across institutional contexts.
- The current build represents instructor agency as a measurable part of the evaluation loop.
- The project supports formative proof of concept, not full validation.

## 9. Naming Guidance For Phase 3

- Use the **working title** above in the formal writeup.
- Use `instructional decision-support prototype` or `IDSS` as the functional artifact label when needed.
- Use `SAGE` to describe the current simulation/evaluation environment.
- Defer the final product name until after the artifact boundary is stable.
