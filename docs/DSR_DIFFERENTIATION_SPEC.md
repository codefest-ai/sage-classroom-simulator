# SAGE v2 — DSR Differentiation Spec
## Where SAGE Sits and Why It Matters
**Date:** March 19, 2026
**Course:** IST 505 Design Science Research Methods, CGU Spring 2026

---

## The Claim

SAGE (Simulated Agent-Generated Engagement) is the first application of LLM-powered generative agents to **formative evaluation of a learning analytics artifact**. It combines deep agent profiling, emergent social dynamics, and closed-loop instructor decision support evaluation in a single system.

No existing tool does this.

---

## Simulation Landscape — Where SAGE Sits

### Traditional Simulation Approaches

| Approach | Method | Agents? | LLM? | Interaction? | Example |
|----------|--------|---------|------|-------------|---------|
| System Dynamics | Differential equations | No — aggregate only | No | No | Stella, Vensim |
| Discrete Event | Queue/process rules | No | No | No | SimPy, Arena |
| Monte Carlo | Random sampling from distributions | No | No | No | Risk analysis tools |
| Traditional ABM | Programmed rule trees | Yes — rule-based | No | Programmed rules | NetLogo, Mesa, MASON |
| BDI Agents | Beliefs-Desires-Intentions logic | Yes — logic-based | No | Rational planning | JADE, Jason |
| **Generative Agents** | **LLM reasons from context** | **Yes — language-based** | **Yes** | **Emergent from shared context** | **Park et al. 2023, SAGE** |

### LLM Agent Approaches (Within Generative Category)

| Approach | Depth | Scale | Interaction | State | Use Case |
|----------|-------|-------|-------------|-------|----------|
| **Synthetic Surveys** (Argyle et al. 2023) | Shallow — one demographic sentence | 1,000+ agents | None — each responds independently | Stateless — one prompt, one response | Polling simulation, crowd opinion |
| **Synthetic Users** (startups) | Shallow — persona prompt | 100s | None | Stateless | UX feedback at scale |
| **AgentTorch** (MIT) | Medium — population parameters | 1,000s | Minimal — decision heuristics | Aggregate state | Epidemiology, policy |
| **Park et al. Generative Agents** (Stanford 2023) | Deep — memory, plans, reflections | 25 | Rich — observe, talk, form relationships | Full memory stream | Social behavior simulation |
| **SAGE v2** | Deep — archetype, learning style, affinity peers, engagement state | 15 | Rich — read room context, reference peers by name, respond to content | Engagement evolves per-minute from LLM decisions | **Classroom engagement + IDSS evaluation** |

---

## Key Differentiators

### 1. Shallow-Many vs. Deep-Few

Synthetic survey approaches (Argyle et al. 2023 "Out of One, Many") prove LLMs can approximate population-level distributions. Feed GPT "you are a 35-year-old Black woman in Georgia" → one survey response → matches real polling data. Scale to thousands.

**But:** Each response is statistically plausible, not individually meaningful. No agent reads another agent's response. No social dynamics. No emergence. It's statistics wearing a language model costume.

SAGE inverts this. 15 agents with deep profiles interact over 45 minutes. Sara the Hands-On Builder says "can we just look at a dashboard instead of more slides" because she IS Sara — her archetype, her learning style, her engagement trajectory, and the 12 minutes of lecture she just sat through all inform the response. The social contagion when 3 students say "I'm confused" and a 4th responds was never programmed — it emerged from shared context.

**The tradeoff is explicit:** depth over breadth. For classroom simulation, 15 deep agents that interact produce richer evaluation data than 1,000 shallow agents that don't.

### 2. Programmed Emergence vs. Generative Emergence

Traditional ABM (NetLogo, Mesa): You program the rules. "If confusion > 0.6, output confused template." Emergence comes from interaction rules the researcher designed. The researcher's assumptions are baked into every agent decision.

SAGE: You describe the character. "You're a hands-on builder who hates theory. It's been 15 minutes of lecture." The LLM decides what to do. The researcher didn't program the decision — the model reasoned about being that person.

**Social contagion example:**
- NetLogo: `contagion_matrix[i][j] * confusion_level[j]` → programmed spread
- SAGE: Student reads "3 classmates just said they're lost" in their context window → LLM naturally generates a contagion response. No matrix. No weights. The language model IS the social dynamics engine.

### 3. Content-Dependent Engagement (Novel)

No existing classroom simulation ties engagement to **what is being taught**. SAGE's content timeline feeds actual class material into agent context:

- Hands-On Builder drifts during lecture, snaps back during code demos
- Reflective Processor does fine during lecture, freezes during cold calls
- Confused student asks for clarification when complexity spikes

Engagement is context-dependent, not curve-dependent. This makes the simulation testable against real classroom patterns.

### 4. Closed-Loop IDSS Evaluation (Novel)

The professor agent reads the **exact same dashboard JSON** a real instructor would see. This closes the DSR evaluation loop:

- Dashboard detects pattern → generates recommendation
- Professor agent reads recommendation + their own teaching plan (instructor notes)
- Professor decides: follow plan or deviate based on dashboard
- Decision feeds back to students as spoken intervention
- Students react to intervention → new engagement state → new patterns

**The DSR claim:** If the professor makes better decisions with the dashboard than without it, the artifact works. If not, iterate. This IS formative evaluation — the simulation is the method artifact.

### 5. Non-Reproducibility as Feature (Novel Methodological Argument)

Same seed ≠ same LLM output. Traditional ABM guarantees identical runs with identical seeds.

**Response:** Real students don't produce identical behavior either. Non-reproducibility is a feature — it models the inherent stochasticity of human interaction.

**Methodological fix:** Run multiple sessions (N ≥ 5 per condition), report distributions. The Demo Suite's comparison mode does this. Report mean engagement trajectories with confidence intervals, not single-run traces. This is standard experimental methodology applied to simulation.

---

## What Exists for Classroom Simulation (Prior Art)

| Tool | What It Does | Gap SAGE Fills |
|------|-------------|----------------|
| **SimSchool** (Gibson, 2007) | Pre-service teacher training with virtual students | Scripted decision trees. Students don't interact. No LLM. No emergent dynamics. |
| **NetLogo classroom models** | Rule-based ABM of classroom dynamics | No language. No dialogue. No content awareness. Emergence is programmed. |
| **ClassSim / engagement curve models** | Statistical models of attention over time | No agents at all. Just curves. Can't evaluate a dashboard because there's no decision-making. |
| **Minecraft Education / VR classrooms** | Virtual environments for real humans | Real students, not simulated. Different purpose entirely — delivery medium, not evaluation. |
| **Second Life educational spaces** | Virtual campus environments | Same — real humans in virtual space. No simulation. |
| **LA dashboards (Wise & Jung, 2019)** | Learning analytics interfaces evaluated with real classes | Real evaluation but requires real classes, real IRB, real semesters. Can't iterate quickly. SAGE enables rapid formative evaluation before deploying to real classrooms. |

**Nobody has applied Park et al.'s generative agent framework to educational simulation or learning analytics evaluation.** SAGE fills this gap.

---

## GEN-IT: Generative-Iterative Design

SAGE embodies a design methodology we call **GEN-IT (Generative-Iterative)** — recursive, generative co-design with AI:

1. **Generate:** LLM agents produce emergent classroom dynamics
2. **Interpret:** IDSS dashboard detects patterns, generates recommendations
3. **Iterate:** Professor (human or agent) responds, modifying the classroom
4. **Repeat:** New dynamics emerge from the intervention

The simulation IS the method artifact. Each cycle generates new evaluation data. The researcher observes how the IDSS performs under emergent conditions that no one designed — conditions that arise from the LLM agents reasoning about being students.

This distinguishes SAGE from evaluation methods that test artifacts against predetermined scenarios. SAGE tests against scenarios that the simulation itself generates. The evaluation and the artifact co-evolve.

---

## References

- Argyle, L. P., et al. (2023). "Out of One, Many: Using Language Models to Simulate Human Samples." *Political Analysis.*
- Endsley, M. R. (1995). "Toward a Theory of Situation Awareness in Dynamic Systems." *Human Factors.*
- Gibson, D. (2007). "SimSchool: An Online Dynamic Simulator for Enhancing Teacher Preparation." *IMSCI.*
- Hevner, A. R., et al. (2004). "Design Science in Information Systems Research." *MIS Quarterly.*
- Li, H., et al. (2025). "Instructor Heterogeneity in Learning Analytics Dashboard Use." *British Journal of Educational Technology.*
- Park, J. S., O'Brien, J. C., Cai, C. J., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." *UIST '23.*
- Venable, J., Pries-Heje, J., & Baskerville, R. (2016). "FEDS: A Framework for Evaluation in Design Science Research." *European Journal of Information Systems.*
- Wise, A. F., & Jung, Y. (2019). "Teaching with Analytics: Towards a Situated Model of Instructional Decision-Making." *Journal of Learning Analytics.*

---

## Summary Table

| Dimension | Traditional ABM | Synthetic Surveys | Park et al. 2023 | **SAGE v2** |
|-----------|----------------|-------------------|-------------------|-------------|
| Agent decisions | Programmed rules | One-shot demographic prompt | LLM with memory | LLM with engagement state + content context |
| Scale | 100s-1000s | 1000s | 25 | 15 |
| Interaction | Programmed | None | Emergent social | Emergent classroom |
| Content awareness | None | N/A | Environment objects | Lecture slides, discussion topics, instructor notes |
| Evaluation target | General dynamics | Population opinion | Social behavior | **Learning analytics dashboard (IDSS)** |
| Closed loop | No | No | No | **Yes — professor reads dashboard, decides, students react** |
| Cost per session | Free (computation) | API cost at scale | API cost | **Free (Groq)** |
| Domain | Various | Political science, UX | Social simulation | **Educational technology** |

---

*IST 505 · CGU Spring 2026 · SAGE v2 Differentiation Spec*
