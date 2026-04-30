# IST 505 Group Meeting — March 29, 2026
## Agenda: Phase 2 Revision + Phase 3 Strategy
## Phase 3 Due: April 13

---

## Professor's Phase 2 Feedback (2 comments)

### Comment 1 (on submission):
> "You claim 'existing systems are descriptive'. Some systems already include AI recommendations. Your artifact novelty is understated."

### Comment 2 (rubric):
> "Cognitive load → signal aggregation, summarization as features.
> Situational awareness → perception, interpretation as features.
> You need to (1) synthesize literature into clear design gaps, (2) formalize your insights into explicit design principles, (3) tightly connect kernel theories to design features, and (4) clarify how you will evaluate the artifact's impact."

---

## Proposed Responses

### 1. "Existing systems are descriptive" — Fix the positioning

**Problem:** We overstated the gap. Some systems already have AI recommendations (Instructure Impact, Zoom IQ, Class Companion, etc.).

**Fix:** Our novelty is NOT "we added AI recommendations." Our novelty is:
- **Institutional context sensitivity** — same dashboard adapts to different schools (we demonstrated this with CGU vs Georgia Tech vs Howard presets using real IPEDS data)
- **Composition-behavior separation** — demographics drive who's in the room, NOT how the engagement model scores them (avoids encoding racial bias)
- **Instructor Response Taxonomy** — 5-level construct (Ignore → Acknowledge → Accept & Adjust → Modify & Adjust → Reject with Reason) that measures HOW instructors use AI support, not just whether they receive it

**Suggested revised positioning:**
> "While existing AI-augmented learning analytics tools provide engagement metrics and some generate AI recommendations, they share three limitations: (1) they treat all classrooms identically regardless of institutional context, (2) they risk encoding demographic bias into behavioral predictions, and (3) they provide no construct for measuring how instructors respond to AI support. IDSS addresses all three."

### 2. Synthesize literature into clear design gaps

We need a gap table:

| Literature Finding | What Exists | What's Missing (Our Gap) |
|---|---|---|
| Endsley (1995) SA theory | Systems provide L1 perception (signals) | No L2-L3 comprehension/projection in dashboards |
| Sweller (1988) CLT | Dashboards show raw data | Signal aggregation to reduce cognitive load is rare |
| Van Leeuwen et al. (2019) | Mirroring mode (show data) | Advising mode (actionable suggestions) under time pressure |
| Li et al. (2025) | One-size-fits-all recommendations | No adaptation for instructor heterogeneity |
| Dell et al. (2015) UDL | Accessibility features | No equity-aware participation monitoring |
| Kauffman (2019) | Learner profiles exist | Not used to generate diverse simulation populations |

### 3. Formalize design principles

| ID | Principle | Kernel Theory | IDSS Feature |
|---|---|---|---|
| DP1 | Institutional context sensitivity | Li et al. (instructor heterogeneity) | University presets with real IPEDS enrollment data |
| DP2 | Composition-behavior separation | Dell et al. (UDL/diverse learners) | Demographics ≠ engagement model inputs |
| DP3 | Instructor agency preservation | Van Leeuwen (advising mode) | 5-level Response Taxonomy |
| DP4 | Cognitive load reduction | Sweller (CLT) | Dashboard aggregates signals, not raw streams |
| DP5 | SA escalation (L1→L2→L3) | Endsley (SA theory) | Perception → Comprehension → Projection pipeline |
| DP6 | Bias-aware evaluation | Ethical AI literature | SAGE separates who from how |
| DP7 | Risk-free evaluation | DSR evaluation methodology | SAGE simulates classrooms — no human subjects needed for initial testing |

### 4. Clarify evaluation approach

**Formative:** Design decision traces (e.g., Demographic Design Rationale document), expert review, iterative build
**Summative:** SAGE scenario comparison across 3 university presets, measuring:
- Recommendation count and type differences across institutional contexts
- Instructor Response Taxonomy distribution (simulated professor)
- Engagement recovery after interventions
- Equity metrics (Gini coefficient for participation)

---

## Phase 3 Requirements (Due April 13)

1. Working (improved) title
2. Problem statement paragraph
3. DSR artifact description (constructs, models, frameworks, methods, prototypes)
4. What is unique/novel
5. Design requirements or principles
6. Form and functions (diagrams, sketches, usability)
7. Proof-of-concept demonstration (platforms, tools)

**Suggested division of labor:**
- **Evren:** Sections 6-7 (app demo, screenshots, technical description, proof of concept)
- **Writing team:** Sections 1-5 (literature, problem, novelty, design principles)
- **All:** Review and integrate

---

## What Evren Can Demo Today

- SAGE simulator running (Python, 5 scenarios, reproducible with seeds)
- 15 student agent profiles with behavioral archetypes
- 3 university presets (CGU, Georgia Tech, Howard) with real IPEDS data
- Comparison table showing different IDSS outputs per institution
- Closed-loop professor agent
- Dashboard (if HTML version is ready)

---

## Suggested Improved Title

"IDSS: An Institutionally-Adaptive Instructional Decision Support System for AI-Augmented Teaching in Synchronous Online Environments"
