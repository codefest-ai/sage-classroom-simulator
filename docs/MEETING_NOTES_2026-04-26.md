# Group Meeting Notes — Apr 26, 2026

**Phase:** 4 (Evaluation Method)
**Attendees:** Evren Arat, Samantha Aguirre, Ahmed Alhussain, Olga Serebryannaya
**Source:** Teams transcript (`~/Developer/evren-pcp/Chat transcripts/IST Meeting for Phase 4.rtfd/TXT.rtf`, ~4,600 lines)
**Phase 4 paper deadline:** Friday May 3 (cover sheet says May 1; group locked in Friday). Drop-completed-parts in chat by Thursday Apr 30 for integration.

---

## Action items (verbatim from Samantha's notes, Phase 4 vs final paper scoped)

| # | Item | Owner | Phase 4? | Status |
|---|---|---|---|---|
| 1 | Synthesize literature into clear design gaps | Olga | Final paper only | Olga to clarify wording of existing gap |
| 2 | Formalize design principles into explicit statements | (already in P3) | Final paper | Sovereignty-first / data security / fairness already articulated |
| 3 | Tightly connect kernel theories to design features | Writing team | Final paper | Overlaps with #4 |
| 4 | Clarify how you will evaluate the artifact (behavioral-impact paragraph precedes analytical section) | Samantha + Evren | **Phase 4** | New prose needed |
| 5 | Define recommendations — how created (lit-backed, not ML) | Samantha (prose) + Evren (artifact framing) | **Phase 4** | Lit references + survey-perceived-factors needed |
| 6 | Engagement is multidimensional — specify scope | Ahmed (prose) + Evren (artifact) | **Phase 4** | Scope statement to UI + paper |
| 7 | Refrain from camera as major signal — proactive ethical reframe | Evren (code, done) | **Phase 4** | Code locked in (`c2a36f7` + today's modifier strip) |
| 8 | Stakeholder groups + ethical recruitment | Samantha; Ahmed asks prof Mon Apr 28 | **Phase 4** | Empty section in draft |
| 9 | Evaluation metrics — performance / user-centric / outcome | Evren / Ahmed (drafted) / Samantha | **Phase 4** | Performance + Outcome sections missing |
| 10 | Methodological approach — mixed methods | Ahmed | **Phase 4** | Done in draft |
| 11 | Data collection instruments | Ahmed | **Phase 4** | Done (SUS, TAM, NASA-TLX, Trust, Satisfaction in appendices) |
| 12 | Quantitative analysis approach (T-test vs ANOVA) | Samantha + Ahmed | **Phase 4** | Empty section; deferred |
| 13 | Artifact description / screenshots / dashboard walkthrough / sim architecture | Evren | **Phase 4** | Underway |

## Framing decisions

**Engagement → Observable Participation.** Confirmed reframe. Caveat enforced on UI: *"Proxy signal, not engagement truth. Silence may mean focus; chat volume may mean skimming. The instructor interprets and decides."* Ahmed: "we have to specify what does the engagement mean" — the paper and the UI need to enumerate which engagement dimensions are in scope (behavioral + slice of attention) and which are out (emotional, cognitive, social).

**Camera as major signal — proactive reframe.** Don't downplay the professor's ethical concern. Frame removal as principled: *"Because of our concern about [bandwidth dependency, cultural expectations around camera-on], we built it in such a way that camera is excluded from scoring."* Camera now non-scoring across both `SIGNAL_WEIGHTS` and `INSTITUTIONAL_MODIFIERS`.

**IDSS vs SAGE.** Already established in talking points. Artifact under study = IDSS (Instructional Decision Support System, real deployment target). SAGE = Simulation & Formative Evaluation Environment (Phase 4 evaluation tool).

## Design principles agreed (Phase 3 carryover, no Phase 4 change)

1. **Sovereignty first** — instructor has agency to make classroom choices; recommendations are advisory; 5-way response taxonomy enforces consent (Evren, ~3:47).
2. **Data security & privacy** — no collection of sensitive demographics (race, etc.).
3. **Fairness / non-bias** — institutional context sensitivity differentiates by context, not by individual demographics.
4. **Observable behavior honesty** — joining ≠ activity; presence ≠ participation; `no_signal` students excluded from class averages.
5. **Instructor interpretation loop** — system flags patterns, evidence visible on every card, professor decides.

## Phase 4 vs final paper — what's in scope

**Phase 4 (this submission):**
- Mixed-methods evaluation (quantitative survey: SUS, TAM, NASA-TLX, Trust, Satisfaction; qualitative: semi-structured interview).
- Three metric categories (performance / user-centric / outcome).
- Stakeholders mentioned briefly; primary evaluator = professor.
- IRB not pursued (formative, in-semester scope).
- Canvas integration **out of scope** (future work beyond this course project).
- Sustained multi-instructor live Zoom validation across full course terms **out of scope** (future work beyond this course project). A hosted-deployment receipt against a single real meeting is included.

**Final paper (later):**
- Literature → design gaps full synthesis (Olga).
- Kernel theory ↔ design features explicit mapping.
- Broader stakeholder analysis (universities, HR, students-as-indirect-users).
- Full design principle articulation.

## Deadlines

| Date | Event |
|---|---|
| Mon Apr 28 (~office hours) | Ahmed asks professor about stakeholder→evaluation linkage in Phase 4 scope |
| Thu Apr 30 | Drop completed parts in chat for Evren to integrate |
| Thu Apr 30 (group meeting) | Final review |
| Fri May 3 | Phase 4 paper submission |

Evren (1:11:15 transcript): "if people finish their parts before Thursday, feel free to drop it in the chat. It'll help me just keep pushing along the project in a way that's congruent with everyone."

## Cross-reference: meeting decisions ↔ current artifact state

| Decision | Current state | Status |
|---|---|---|
| Camera removed from scoring | `simulator/scoring.py` `SIGNAL_WEIGHTS` excludes camera; `simulator/university_presets.py` `INSTITUTIONAL_MODIFIERS` stripped of camera modifiers (today) | ✅ Aligned |
| Engagement → Observable participation | `dashboard/index.html` UI uses "Observable Participation"; talking points enforce; `simulator/scoring.py` uses `observable_participation` | ✅ Aligned |
| Per-card evidence visible | `dashboard/index.html` "Triggered by [pattern] — [measurement]" line on every card (commit `623c393`) | ✅ Aligned |
| Per-card institutional context | `dashboard/index.html` "Context: [University] — [description]" on every card (today, see `docs/PACKET_RECONCILIATION_2026-04-26.md`) | ✅ Aligned |
| Presence ≠ activity (no_signal honesty) | `simulator/scoring.py` excludes zero-signal students from class averages (commit `dbee04e`) | ✅ Aligned |
| Live mode ingestion-only label | `dashboard/index.html` label on cards in live mode (commit `fb30643`) | ✅ Aligned |
| Engagement scope statement (which dimensions in/out) | Sticky caveat present, but does not enumerate behavioral/attention/emotional/cognitive/social scope explicitly | 🟡 **C2 candidate** |
| Camera-presence non-scoring caveat next to UI | Camera grid renders but no inline non-scoring text | 🟡 **C5 candidate** |
| Performance metric instrumentation (accuracy/precision/recall/latency) | Not measured; no telemetry endpoint | 🔴 **C1 candidate** |
| SAGE evaluation-run export (citable artifact for paper) | Per-tick state visible but not exportable | 🔴 **C4 candidate** |
| Behavioral-impact deltas around interventions | Dashboard shows current state, not pre/post-intervention deltas | 🔴 **C3 candidate** |
| Lit grounding visible per pattern | Not surfaced in UI; lives only in talking points | 🟡 **C6 candidate** |
| Live performance-metrics panel | No surface | 🟡 **C7 candidate** (depends on C1) |
| Reproducible screenshot capture | Manual only | 🟡 **C8 candidate** |
| Zoom live-demo runbook | None | 🟡 **Z3 candidate** |
| Live-mode UI polish | Sparse rendering, no meeting-context header | 🟡 **Z1 candidate** |
| Local Zoom token flow | None; only public webhook path | 🟡 **Z2 candidate** |

C1–C8 + Z1–Z3 are tracked in `docs/EVREN_PHASE4_PAPER_PUNCHLIST_2026-04-26.md`.

## Open questions (unresolved in meeting)

1. **Performance metric operationalization for an advisory system.** How do you measure "accuracy / precision / recall / latency" for a rule-based recommendation system that is *not* a classifier? Candidate framing: pattern-detection precision against signal-evidence threshold, throttling effectiveness (no-spam), latency per tick, 5-way response taxonomy adoption rate. Evren to propose; group reviews.
2. **Engagement score: performance metric or user-centric?** Evren raised this in meeting; not resolved. Likely answer: the *score's existence* is performance-side (does the system measure correctly); the *score's instructor utility* is user-centric (is the score useful). Worth restating in the paper.
3. **T-test vs ANOVA for Likert-scale survey data.** Samantha + Ahmed deferred. Depends on group-comparison structure (one group pre/post vs. two groups with vs without artifact).
4. **Stakeholder evaluation scope for Phase 4.** Ahmed asks professor Monday Apr 28. Compromise position: list primary evaluator (professor) clearly, mention others briefly, no Phase 4 data-collection from non-primary stakeholders.
5. **HR stakeholder relevance.** Olga argued for inclusion (training-effectiveness use case); Ahmed skeptical for Phase 4. Mention in final paper; out of Phase 4 unless professor clarifies.
6. **Survey distribution / recruitment logistics.** Not discussed; assumed handled as part of Phase 4 walkthrough rather than a separate study.

## Routing

Per packet division-of-labor (still holds): Evren owns artifact, screenshots, dashboard walkthrough, simulation architecture, proof-of-concept. Writing team owns problem statement, lit-gap synthesis, kernel-theory mapping, design principles articulation, evaluation prose. Today's meeting did not change this division.
