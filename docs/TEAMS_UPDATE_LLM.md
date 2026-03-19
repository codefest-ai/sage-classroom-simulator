## SAGE Update — LLM-Powered Student Agents

Hey team — quick update on a major upgrade to SAGE.

**What changed:** The simulated students are now powered by a large language model (Llama 3.1 via Groq). Instead of picking from template responses like "Great point!" or "+1", each student agent *reasons about who they are and what's happening in class* and generates authentic responses.

**What this looks like:**
- The Hands-On Builder says "Can we just look at an actual dashboard instead of more slides?" during a long lecture segment
- The Critical Thinker pushes back: "But how do we measure that without it becoming super subjective?"
- The Confused student asks: "Can someone explain what they mean by 'add value' exactly?"
- Students reference each other by name and build on each other's points

**Why it matters for DSR:** This moves SAGE from a rule-based calculator to a true agent-based simulation. The closest precedent is Park et al. (2023) at Stanford — "Generative Agents: Interactive Simulacra of Human Behavior" — where they put 25 LLM agents in a Sims-like sandbox and the agents spontaneously organized a Valentine's Day party that nobody programmed. Social behavior emerged from shared context, not explicit rules.

We're applying the same approach to classroom engagement. Social contagion, confusion cascades, and discussion dynamics emerge from the LLM reading the room — not from a contagion matrix we designed. This could be a methodological contribution: **LLM-agent simulation as a DSR evaluation method.**

**Also new:** Configurable class content timelines (SA theory, DSR methods, data ethics, HCI, or custom). Students react to *what's being taught*, not just room energy. You can compare "pure lecture" vs. "active learning" formats and see how the IDSS responds differently.

**Try it:** https://sage-simulator-ulsd.onrender.com
Click ▶ Run — it auto-detects the AI backend.

**Cost:** $0. Groq's free tier handles it.

Let me know what you think.
