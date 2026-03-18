# IST 505 Design Research Methods — Midterm Study Guide
## Oral Exam (Mar 19-24) + Written Exam (Mar 23, 4-5:15 PM)

---

## 1. Design Science vs Behavioral Science

**Oral:** IS research has two paradigms. Behavioral science seeks to understand — it tests theories that explain or predict phenomena around IT. Design science seeks to create — it builds and evaluates artifacts to solve problems. Behavioral science asks "what is true?" Design science asks "what is effective?" They're complementary: behavioral theories inform design, designed artifacts generate phenomena worth theorizing about.

**Written:** The two paradigms in IS research are behavioral science and design science (Hevner et al., 2004). Behavioral science develops and justifies theories explaining IS phenomena. Design science extends human/organizational capabilities by creating innovative artifacts. Behavioral science produces descriptive/predictive theories; design science produces prescriptive knowledge as constructs, models, methods, and instantiations. The two are complementary and iterative.

---

## 2. Hevner's 7 DSR Guidelines (Hevner et al., 2004)

| # | Guideline | SAGE Application |
|---|---|---|
| G1 | **Design as Artifact** — must produce a viable construct, model, method, or instantiation | IDSS dashboard + agent simulation |
| G2 | **Problem Relevance** — solve important business problems | Instructors lack decision support for heterogeneous classrooms |
| G3 | **Design Evaluation** — rigorously demonstrate utility, quality, efficacy | Formative (during build) + summative (user testing) |
| G4 | **Research Contributions** — novel artifact, foundations, or methodology | SA-theoretic IDSS via agent simulation = Improvement quadrant |
| G5 | **Research Rigor** — grounded in knowledge base, rigorous methods | Endsley SA model, UDL, learning analytics literature |
| G6 | **Design as Search** — iterative generate-test-refine | Agent parameter tuning, dashboard layout iteration |
| G7 | **Communication** — present to both technical and management audiences | Course presentation, paper |

---

## 3. DSR Frameworks

### Peffers et al. (2007) — DSRM Process Model
Six steps: (1) Problem identification & motivation, (2) Define objectives, (3) Design & development, (4) Demonstration, (5) Evaluation, (6) Communication. Four entry points. Explicitly iterative. **SAGE is at Step 3-4.**

### Gregor & Hevner (2013) — Knowledge Contribution Framework
2x2 matrix: application domain maturity × solution maturity.

| | Low Solution Maturity | High Solution Maturity |
|---|---|---|
| **Low Domain Maturity** | **Invention** (new solution, new problem) | **Exaptation** (known solution → new domain) |
| **High Domain Maturity** | **Improvement** (better solution, known problem) | **Routine Design** (not research) |

**SAGE = Improvement** (instructor decision support is known problem, SA-theoretic agent-based dashboard is novel solution). Also arguable as **Exaptation** (SA mature in aviation → applied to education).

---

## 4. Artifact Types (March & Smith, 1995)

| Type | Definition | SAGE Example |
|---|---|---|
| **Constructs** | Vocabulary/symbols | SA levels for instructor awareness |
| **Models** | Abstractions/representations | Agent-based classroom simulation model |
| **Methods** | Algorithms/processes | SA requirements → dashboard design process |
| **Instantiations** | Working systems | The SAGE prototype |

---

## 5. Evaluation — FEDS Framework (Venable et al., 2016)

Two dimensions: **naturalistic vs artificial** × **ex ante vs ex post**

| Strategy | When | SAGE Phase |
|---|---|---|
| **Quick & Simple** (artificial + ex ante) | Early design review | Design spec against SA checklist |
| **Human Risk & Effectiveness** (naturalistic + ex ante) | Pre-build stakeholder check | Expert review with instructors |
| **Technical Risk & Efficacy** (artificial + ex post) | Prototype testing | Controlled scenario testing |
| **Purely Naturalistic** (naturalistic + ex post) | Field deployment | Future: real instructors, real courses |

**Formative** = during development (improve artifact). **Summative** = after development (judge worth).

---

## 6. Situational Awareness — Endsley (1995)

| Level | Name | Definition | Dashboard Gap |
|---|---|---|---|
| **1** | Perception | Detecting relevant information | Most dashboards stop here (bar charts, numbers) |
| **2** | Comprehension | Understanding what it means | SAGE: pattern detection, behavioral clustering |
| **3** | Projection | Forecasting future states | SAGE: agent simulation enables projection |

**Key insight:** Most learning analytics dashboards are Level 1 tools. SAGE targets Levels 2 and 3.

---

## 7. Key Papers

| Paper | Key Finding | SAGE Connection |
|---|---|---|
| **Li et al. (2025)** | Instructors use analytics heterogeneously — not one-size-fits-all | IDSS must be adaptive to instructor profiles |
| **Wise & Jung (2019)** | Intervention↔outcomes is non-linear; too much suppresses student interaction | IDSS should support nuanced when/how/how-much decisions |
| **Kauffman (2019)** | Learner heterogeneity interacts with instruction; subgroups differ | Agents must model diverse profiles; dashboard must surface subgroup patterns |
| **Dell et al. (2015)** | UDL: multiple means of engagement/representation/expression | Engagement ≠ single metric; diverse participation forms matter |
| **Endsley (1995)** | SA 3 levels; most systems fail at L2/L3 | SAGE designed for all 3 levels |

---

## 8. Rigor vs Relevance

**Oral:** Rigor = grounded in knowledge base, methodologically precise. Relevance = problem matters to practitioners. Too much rigor = solving problems nobody has. Too much relevance = no theoretical grounding. Good DSR contributes to both: solves a real problem AND advances the knowledge base.

---

## 9. Likely Exam Questions

### Oral
1. "Describe your project as a DSR contribution" → Gregor & Hevner quadrant + artifact types + problem relevance
2. "How does your project address Hevner's guidelines?" → Walk through all 7
3. "What is your evaluation plan?" → FEDS strategy + formative/summative
4. "How does SA theory inform your design?" → 3 levels, most dashboards = L1, SAGE targets L2+L3
5. "What does the literature say about instructor analytics use?" → Li (heterogeneity), Wise & Jung (non-linear), Kauffman (subgroups)

### Written (2-3 questions)
1. "Define the four artifact types" → March & Smith with examples
2. "Explain rigor vs relevance" → Hevner, two cycles, tension is productive
3. "Describe the DSRM process and where your project is" → Peffers 6 steps, SAGE at Step 3-4

---

## Key Citations
- Hevner et al. (2004) — MIS Quarterly — 7 guidelines
- Peffers et al. (2007) — JMIS — DSRM process
- Gregor & Hevner (2013) — MIS Quarterly — Knowledge contribution
- March & Smith (1995) — Decision Support Systems — Artifact types
- Venable et al. (2016) — EJIS — FEDS evaluation
- Endsley (1995) — Human Factors — SA model
- Simon (1996) — Sciences of the Artificial — Satisficing search
