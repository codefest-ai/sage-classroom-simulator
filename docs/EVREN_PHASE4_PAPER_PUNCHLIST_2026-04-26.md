# Evren — Phase 4 Paper Punchlist (Apr 26 → May 3)

**Drop in chat by:** Thursday Apr 30
**Submit by:** Friday May 3
**Receiving artifact:** `~/Downloads/IST 505 Final Project Phase 4 (Draft).docx`

---

## Prose deliverables (what Ahmed needs from Evren by Thursday)

### P1. Analytical (Simulation) Evaluation section
**Goes in:** "Types of Evaluation → Analytical (Simulation)" — currently empty header in draft.
**Ready when:** ~250–400 words describing SAGE as the formative evaluation environment, what gets simulated, what's measured, why this is the right Phase 4 evaluation surface for an IDSS that targets real Zoom deployment.

**Source material to compress:**
- `docs/PHASE4_DEMO_TALKING_POINTS_2026-04-23.md` (30-second opening + signal weights table)
- `docs/PACKET_RECONCILIATION_2026-04-26.md` (full current-state map)
- `simulator/scoring.py` (5-signal composite, weights, pattern detectors)
- `simulator/university_presets.py` (institutional context sensitivity)
- `simulator/student_personas.py` (15-archetype profile generation)

**Starter scaffold:**
> The analytical (simulation) evaluation uses SAGE — a Simulation and Formative Evaluation Environment built specifically to exercise the IDSS under controlled, reproducible synchronous-classroom conditions. SAGE generates 15 student profiles per session from configurable institutional presets (CGU baseline, Georgia Tech large-online-program, Howard small-department), each profile carrying behavioral parameters that drive observable participation signals: speaking time, chat activity, poll responses, reactions, and silence gaps. The IDSS consumes these signals through a deterministic five-signal weighted composite (speaking equity 30%, chat 25%, polls 25%, reactions 15%, silence gap 5%; camera removed from scoring per the ethical-design principle below) and surfaces rule-based pattern recommendations to the instructor.
>
> SAGE is appropriate for Phase 4 formative evaluation because (a) it produces controlled scenarios that all evaluator-instructors experience identically, isolating artifact effects from external classroom variability; (b) it exercises the full IDSS measurement-recommendation-response loop without requiring live student participants; and (c) it generates an exportable per-tick record of observable participation, pattern detection events, and instructor responses that the user-centric evaluation (Section 3) can be cross-referenced against. Live Zoom integration is implemented end-to-end (webhook-based, signature-verified, fixture-tested, and validated against a real Zoom meeting on the hosted deployment). Sustained multi-instructor longitudinal validation is identified as future work beyond the scope of this course project.

### P2. Performance Metrics section
**Goes in:** New subsection under "Section 3: Measurement and metrics" (alongside User-Centric and Outcome). Currently missing from draft.
**Ready when:** 4 metrics defined with operationalization for an advisory rule-based system (not a classifier).

**Resolves the open question Evren raised at meeting** — these metrics live on the *artifact-correctness* side; engagement-score *utility* sits in user-centric.

**Starter scaffold:**

> **Performance Metrics.** Because the IDSS is a rule-based advisory system rather than a learned classifier, the conventional performance vocabulary (accuracy / precision / recall / latency) is operationalized against the system's own deterministic specification rather than against ground-truth student state.
>
> *Pattern-detection precision* is defined as the proportion of pattern-trigger events whose underlying signal evidence meets or exceeds the published threshold for that pattern (e.g., the `silent_majority` pattern requires >50% of active students with zero contributing signals across speaking, chat, polls, and reactions; precision = triggers-with-valid-evidence ÷ total-triggers). Because pattern logic is deterministic, precision is expected at 1.0 in correct operation; deviations indicate code regression and are caught by the instrumentation pipeline.
>
> *Recommendation throttling effectiveness* is defined as the rate at which duplicate within-cooldown pattern triggers are suppressed (3-minute per-pattern cooldown enforced in `server.py`). Target ≥99% suppression of within-cooldown duplicates, ensuring the recommendation log is not spammed.
>
> *Latency* is defined as the elapsed time between a simulation tick and the resulting recommendation surfacing on the dashboard, measured per tick. Target <200 ms at the local-loop scale used in SAGE.
>
> *Five-way response taxonomy adoption rate* is defined as the proportion of surfaced recommendations that receive an instructor response (any of: ignore / acknowledge / accept / modify / reject) versus those left unresponded. This is a system-side outcome metric — the system functioning as intended produces high adoption regardless of which response is chosen, since each of the five is a valid disposition.
>
> All four are continuously logged via the SAGE evaluation-run export (described in §X) and can be cross-tabulated against the user-centric measures.

### P3. Behavioral-impact paragraph (joint with Samantha)
**Goes in:** Immediately preceding the Analytical (Simulation) section, per Samantha's meeting note (44:37 transcript).
**Ready when:** ~150 words describing what behavioral impact the artifact aims to produce, and how that impact will be measured.

**Coordination needed:** Samantha said "Evren, I can work with you... put together ideas and you consider how it might impact or be utilized by the artifact." Initiate the joint draft Tuesday/Wednesday so both surfaces (prose + artifact-side measurement scaffolding) align.

**Starter scaffold:**

> **Behavioral-impact framing.** The artifact's intended behavioral impact on the instructor is twofold: (1) shift instructor attention from raw signal monitoring to higher-order interpretation, reducing the cognitive load of fragmented dashboard-watching; and (2) prompt timely instructional micro-decisions (re-engaging silent students, modulating chat-heavy moments, redirecting cluster-confusion) that would otherwise occur late or not at all. Behavioral impact is measured through three complementary surfaces: (a) instructor self-report via the user-centric instruments below (NASA-TLX cognitive load, perceived usefulness, trust); (b) observable response patterns logged within the system (the five-way response taxonomy distribution, response timing relative to recommendation surface time); and (c) participation-trajectory deltas around logged interventions, captured per-tick during SAGE runs and exportable for analysis.

### P4. Artifact description / dashboard walkthrough / sim architecture
**Goes in:** Likely a standalone section near the front of the paper or as an extended methods section. Confirm with Ahmed where it lands.
**Ready when:** ~300 words + 4–6 screenshots covering: dashboard layout (observable-participation index, student grid, patterns panel, recommendations panel with caveat), 5-way response surface, live-mode toggle and ingestion trace, university-preset selector showing institutional differentiation.

**Source material:** `dashboard/index.html` rendered output. `scripts/capture_dashboard.py` (forthcoming, see C8) will produce reproducible screenshots.

---

## Code deliverables (back the paper claims demonstrably)

Tracked in `docs/MEETING_NOTES_2026-04-26.md` cross-reference table; expanded here:

| ID | Change | Backs paper claim | Status |
|---|---|---|---|
| **C5** | Camera-presence non-scoring caveat next to UI grid | P2 §camera; Item 7 ethical reframe | Pending |
| **C2** | Engagement-scope statement on dashboard (which dimensions in/out) | P1 / P2 scope claim; Item 6 | Pending |
| **C6** | Lit-grounding tooltip per pattern | P2; Item 5 ("how recommendations created") | Pending |
| **C1** | Performance-metric telemetry pipeline | P2 (load-bearing — without this, P2 is unbacked) | Pending |
| **C7** | Live performance-metrics dashboard panel | P2 demo-side; depends on C1 | Pending |
| **C4** | SAGE evaluation-run export (JSON/CSV) | P1 + P3 (citable artifact) | Pending |
| **C3** | Behavioral-impact delta surface around interventions | P3 (numeric backing) | Pending |
| **C8** | `scripts/capture_dashboard.py` reproducible screenshots | P4 figures | Pending |
| **Z3** | `docs/ZOOM_LIVE_DEMO_RUNBOOK.md` | future-work paragraph (post-course project) | Pending |
| **Z1** | Live-mode UI polish | Demo-day; not required for paper | Pending |
| **Z2** | Local Zoom OAuth/dev token flow | Demo-day; not required for paper | Pending |

**Sequencing recommendation:** C5 → C2 → C6 → C1 → C7 → C4 → C3 → C8 → Z3 → Z1 → Z2.

---

## Ready-when checklist (Thursday Apr 30 EOD targets)

- [ ] **P1** drafted (Analytical/SAGE section, ~300 words) — pasted into draft .docx
- [ ] **P2** drafted (Performance Metrics, 4 metrics defined) — pasted into draft .docx
- [ ] **P3** drafted with Samantha (Behavioral-impact paragraph) — pasted into draft .docx
- [ ] **P4** drafted (Artifact description) + screenshots — pasted into draft .docx
- [ ] **C1–C5** committed and verify-green
- [ ] **C6–C8** committed and verify-green
- [ ] **Z3** runbook committed
- [ ] Drop completed paper sections in group chat for Ahmed integration

**Deferred / negotiable based on time:**
- Z1, Z2 (Zoom polish) — not required for Phase 4 paper.
- Render Zoom secret deployment — blocked on Evren's hands.
- Codex review pass on C1–C8 — held until Codex credit returns. If not back by Friday, ship with self-adversarial review only and flag in commit messages.

## Open coordination items

- **Samantha:** initiate joint draft of P3 (behavioral-impact paragraph) Tue/Wed.
- **Ahmed:** waiting on Mon Apr 28 office-hours conversation about stakeholder→evaluation scope; report back to group.
- **Olga:** literature → design gaps on her own track for final paper, no Phase 4 dependency.
- **Group:** review Ahmed's user-centric metrics draft (already in paper); confirm P2 Performance Metrics framing once Evren drafts.
