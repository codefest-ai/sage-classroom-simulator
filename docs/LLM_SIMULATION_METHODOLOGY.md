# LLM-Agent Simulation Methodology — SAGE v2
## Where SAGE Sits in the Simulation Landscape
**Date:** March 19, 2026
**Context:** IST 505 DSR artifact + potential capstone/position paper contribution

---

## Simulation Type Comparison

| Type | How agents decide | Emergence | Reproducible | Example |
|------|------------------|-----------|-------------|---------|
| **System Dynamics** | Differential equations | Aggregate only | Yes | Stella, Vensim |
| **Discrete Event** | Queue rules | Process-level | Yes | SimPy, Arena |
| **Monte Carlo** | Random sampling from distributions | Statistical | Seed-based | Risk analysis |
| **Traditional ABM** | Programmed rule trees | From interaction rules | Seed-based | NetLogo, Mesa |
| **BDI Agents** | Beliefs-Desires-Intentions logic | From rational planning | Yes | JADE, Jason |
| **Generative Agents (LLM)** | Language model reasons from context | From shared meaning | **No** | Park et al. 2023, **SAGE** |

---

## Key Distinction: Programmed vs. Generative Behavior

**Traditional ABM:** You program "if confusion > 0.6, say confused template." Emergence = interaction rules you wrote.

**LLM-Agent (SAGE):** You describe "you're a hands-on builder who hates theory, it's been 15 minutes of lecture." Emergence = the model *reasoning about being that person*.

Social contagion in ABM = a contagion matrix with weights.
Social contagion in SAGE = student reads "3 classmates just said they're lost" and the LLM naturally generates a contagion response. Contagion wasn't modeled — it emerged from shared context.

---

## What Makes This Academically Significant

### 1. Evaluation Validity
The IDSS dashboard is being evaluated by agents that *interpret* the classroom, not agents that follow probability tables. The professor agent reads the exact same dashboard JSON a human instructor would see and makes decisions. This is a stronger evaluation argument than any rule-based simulation.

### 2. Methodological Contribution
LLM-as-agent in educational simulation is novel. Park et al. (2023) did it for social behavior. Using it for **classroom engagement simulation as a DSR evaluation method** is a new application.

### 3. GEN-IT: Generative-Iterative Design
The simulation embodies "recursive, generative co-design with AI." The simulation generates emergent dynamics → the dashboard interprets them → the professor/researcher iterates on interventions → the cycle repeats. The simulation IS the method artifact.

---

## The Determinism Problem (and Solution)

### Current State (v2)
- Engagement scores: **deterministic** (formula: `baseline * decay_curve + noise`)
- Chat messages: **generative** (LLM-powered)
- Professor decisions: **rule-based** (probability distributions per style)
- Result: LLM is "lipstick on a calculator" — behavior is predetermined, only dialogue is emergent

### Target State (v2.5 — LLM engagement model)
- Engagement: **generative** — LLM decides engagement state from context
- Chat: **generative** — LLM decides what to say
- Professor: **generative** — LLM professor reads actual dashboard
- Result: TRUE agent-based model where every agent reasons about its own state

### Implementation
One LLM call per student per tick, combined:
> "You're Sara, hands-on builder, minute 22. Professor has been lecturing SA theory for 12 minutes. Room energy is low. Two classmates just said they're lost. How engaged are you (0-100) and what do you say?"

Returns: `{"engagement": 28, "chat": "Can we just look at an actual dashboard instead of more slides?"}`

Cost on Groq (free tier): 15 students × 45 minutes = 675 calls. Within free limits (30 req/min, 14,400/day).

---

## The Reproducibility Question

**Weakness:** Same seed ≠ same LLM output. Traditional ABM guarantees identical runs with identical seeds.

**Response:** Real students don't produce identical behavior either. Non-reproducibility is a feature — it models the inherent stochasticity of human interaction.

**Methodological fix:** Run multiple sessions (N ≥ 5 per condition) and report distributions. The Demo Suite's comparison mode already does this. Report mean engagement trajectories with confidence intervals, not single-run traces.

---

## Content Timeline (Missing Piece)

Currently students react to room dynamics but not to **what's being taught**. A real simulation needs a content timeline:

```json
[
  {"minute": 1, "type": "lecture", "topic": "SA Level 1 — Perception", "complexity": "medium"},
  {"minute": 11, "type": "discussion", "prompt": "Where does SA fail in your experience?"},
  {"minute": 16, "type": "lecture", "topic": "SA Level 2 — Comprehension", "complexity": "high"},
  {"minute": 25, "type": "breakout", "task": "Apply SA framework to dashboard design"},
  {"minute": 31, "type": "presentation", "format": "student groups report out"},
  {"minute": 41, "type": "wrapup", "topic": "Key takeaways + next week preview"}
]
```

Each content type modifies engagement differently per archetype:
- **Lecture** → faster drift for hands-on/pragmatist, fine for reflective
- **Discussion** → boost for collaborative/social, anxiety for withdrawn
- **Breakout** → big boost for collaborative, neutral for lurkers
- **Complex concept** → confusion spike for struggling learners

This makes decay **content-dependent**, not just time-dependent.

---

## Landmark Reference

**Park, J.S., O'Brien, J.C., Cai, C.J., et al. (2023).** "Generative Agents: Interactive Simulacra of Human Behavior." *UIST '23.* Stanford University.

25 LLM agents in a Sims-like sandbox spontaneously organized a Valentine's Day party nobody programmed. First demonstration of emergent social behavior from LLM agents sharing context.

**SAGE extends this to educational settings** — classroom engagement, instructor decision support, and DSR evaluation methodology.

---

## Where to Go From Here

### Immediate (IST 505 submission)
1. Build content timeline into engine
2. Replace formula engagement with LLM-decided engagement (v2.5)
3. Run comparison: rule-based vs. LLM students across scenarios
4. Export data for DSR evaluation section

### Medium-term (Capstone / Position paper)
- Frame as methodological contribution: "LLM-Agent Simulation as DSR Evaluation Method"
- Compare with traditional ABM approaches (NetLogo classroom sims exist)
- The non-reproducibility argument is publishable on its own
- GEN-IT framework as recursive generative co-design

### Long-term (Throughline connection)
- SAGE's person-archetype-to-LLM-agent pattern is structurally identical to Throughline's tethered agent architecture
- Student profile → system prompt is the same as Living PCP → agent fore-structure
- The IDSS dashboard → professor decision loop mirrors the Astrolabe → stakeholder translation loop
- **Do NOT make this connection in IST 505 submission.** Save for capstone where you control the framing.

---

*Saved March 19, 2026 — from Claude Code session, SAGE v2 build + methodology discussion.*
