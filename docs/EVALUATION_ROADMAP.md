# SAGE Evaluation Roadmap
## Phased validation from simulation to real-world deployment

### Phase 1: Agent-Based Simulation (Digital)
- **1a** — Rule-based simulation (seed/probability). No LLM. ✅ DONE
- **1b** — LLM-powered student agents (local MLX). Generative chat, emergent dynamics. IN PROGRESS
- **1c** — LLM agents that actually USE the IDSS artifact. Professor agent reads dashboard, makes decisions through it. Closes the DSR evaluation loop.

### Phase 2: In-Person Simulation (Group Members)
- **2a** — Low-tech Wizard of Oz. Scenario cards, role assignment (professor/student). No technology required. Feedback from live humans going through the process.
- **2b** — High-tech Wizard of Oz. Same roles but using the SAGE tool modified for in-person session use. Pre-determined dashboard feedback.
- **2c** — High-tech in-person with actual tool. Group members use the real IDSS prototype during a simulated class.

### Phase 3: Real-World Trials
- **3a** — In-person with real students and professors using the tool in an actual class
- **3b** — Online with real students and professors using real platform integration

### What Each Phase Proves

| Phase | What it validates |
|---|---|
| 1a | Technical feasibility — does the simulation engine work? Does pattern detection fire correctly? |
| 1b | Realism — does LLM chat produce naturalistic dynamics the NLP still catches? |
| 1c | Closed-loop DSR — does the IDSS actually support better decisions? |
| 2a | Process validity — does the workflow make sense to humans before technology enters? |
| 2b | Interface validity — can humans interact with the tool as designed? |
| 2c | Artifact validity — does the tool improve the process vs without it? |
| 3a | Ecological validity — does it work in a real classroom? |
| 3b | Deployment validity — does it work at scale in real online environments? |

### Current Status
- Phase 1a: ✅ Complete
- Phase 1b: 🔧 In progress (LLM client + student agent built, needs integration testing)
- Phase 1c: 🔧 In progress (professor agent built, dashboard-mediated decisions wired)
- Phase 2a: 📋 Planned (Olga's suggestion — group members as participants, IRB-free)
- Everything else: Future work

### DSR Claim Structure
Phase 1 = Technical Risk & Efficacy evaluation (FEDS: artificial, ex post)
Phase 2 = Human Risk & Effectiveness evaluation (FEDS: naturalistic, ex ante)
Phase 3 = Purely Naturalistic evaluation (FEDS: naturalistic, ex post)
