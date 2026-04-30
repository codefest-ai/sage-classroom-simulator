# Phase 4 Group Meeting Packet — Thursday May 1, 2026

**Purpose:** Single document for tomorrow evening's group meeting. Contains the proposed integrated draft sections, the corrections needed to teammates' contributions before paste, the defense talking points, and the approval checklist. The submission deadline is **Friday May 3**.

---

## Agenda (suggested, 60 min)

1. **5 min — Status snapshot.** What is in the draft .docx now vs. what is still empty.
2. **10 min — Stakeholders section.** Approve Olga's prose with the camera correction below.
3. **10 min — Section 7.** Approve Hamad's prose with the wording pass below.
4. **15 min — Evren-owned sections.** Walk Performance Metrics, Behavioral Impact, Analytical/SAGE, Artifact Description, recommendation-engine rationale, DSR validity limits.
5. **10 min — Open decisions.** T-test vs. ANOVA. Outcome Metrics ownership. Section 7 research-question wording (Ahmed).
6. **10 min — Final cadence.** Who pastes what into the .docx by when. Submission gate.

---

## Status snapshot — current .docx vs. ready prose

| Section | Status in .docx | Source for paste | Owner |
|---|---|---|---|
| Evaluation Objective | Done | — | — |
| Types of Evaluation — Experimental | Done | — | — |
| **Types of Evaluation — Analytical (Simulation)** | Empty header | P1 below | Evren |
| **Behavioral-impact paragraph (precedes analytical)** | Missing | P3 below | Evren + Samantha |
| **Stakeholder Groups + Ethical Recruitment** | Empty header | Olga's prose, edited (§A) | Olga (paste), Evren (edit) |
| **Performance Metrics** | Missing subsection | P2 below | Evren |
| User-Centric Metrics | Done | — | Ahmed |
| **Outcome Metrics** | Missing subsection | scaffold (§C) | Samantha |
| Methodological Approach | Done | — | Ahmed |
| IRB Justification | Done | — | Ahmed |
| Data Collection (quant + qual) | Done with appendices | — | Ahmed |
| **Quantitative Analysis Approach** | Empty header | P10 below | Samantha + Ahmed |
| Qualitative Analysis Approach | Done | — | Ahmed |
| **Section 7: Linking Evaluation Data → RQs** | Empty header | Hamad's prose, edited (§B) | Hamad (paste), Evren (edit) |
| **Artifact Description** | Missing standalone section | P4 below | Evren |
| **Recommendation Engine Design Rationale** | Missing | P6 below | Evren |
| **DSR Hevner mapping (optional)** | Missing | P7 below | Evren |
| **Threats to Validity / Scope Limits** | Missing | P9 below | Evren |

Already-drafted Evren sections live at `docs/EVREN_PHASE4_PAPER_DRAFT_PROSE_2026-04-26.md`. They are paste-ready.

---

## §A — Stakeholder section (Olga's prose, with camera correction)

**Why edited:** Olga's draft contains a line stating the system "may use intrusive signals such as camera-based data, all video recordings will be deleted immediately after processing." This contradicts the artifact's actual posture — camera was removed from the participation composite (`SIGNAL_WEIGHTS` in `simulator/scoring.py`, commit `c2a36f7`) and is rendered as presence context only. The dashboard now carries an explicit non-scoring caveat banner above the camera grid. If the paper claims intrusive video processing, the artifact contradicts the paper. The corrected version preserves Olga's structure and her ethical-considerations framing.

> **Stakeholder Groups and Ethical Recruitment**
>
> This study involves three primary stakeholder groups with different roles and levels of interaction with the artifact.
>
> **Professors / Faculty (Primary Stakeholders — End Users and Domain Experts).** Instructors are the primary users of the system and interact with the dashboard during live teaching sessions. Their proximity is direct: they use the artifact in real time to monitor observable participation signals and respond to advisory recommendations. Participants will be recruited inside CGU CISAT and invited to take part voluntarily. Informed consent will be obtained, and participants may withdraw at any time. Data will be anonymized, and the system is positioned as a decision-support tool, not a performance-evaluation instrument.
>
> **Universities / Instructional Designers / IT Departments (Secondary Stakeholders — Decision Makers).** These stakeholders are indirect users who influence adoption and integration of the system. Their proximity is institutional, shaping implementation rather than direct use. They are not included in Phase 4 because of resource limits; in subsequent phases, they would be recruited through professional networks for interviews or feedback sessions. No institutional data will be collected without explicit permission, and any responses will be aggregated.
>
> **Students (Indirect Stakeholders — Participants).** Students are affected by the system but do not interact with it directly. Their proximity is indirect: they participate in the learning environment where the artifact is used. Phase 4 evaluation relies on simulated agent-students within the SAGE evaluation environment and, in any subsequent live deployment, on anonymized observable participation signals from the synchronous classroom (speaking time, chat activity, poll responses, reactions, and silence gaps). **Camera state is excluded from the participation composite by design and rendered for presence context only;** no video content is processed, scored, or stored by the artifact, and no inference about engagement or attention is drawn from camera-on or camera-off status. This decision was made on ethical grounds in response to the multidimensional nature of engagement and to avoid penalizing students for reasons unrelated to learning (bandwidth limits, privacy, environment, or accessibility).
>
> **Ethical Considerations.** Across all groups, the study follows principles of voluntary participation, transparency, data minimization, and user autonomy. Observable participation signals are framed in the interface and the paper as proxy indicators rather than ground-truth engagement, attention, or learning. The system is designed to support instructor decision-making without enforcing rigid interpretations of student state, consistent with guidelines such as Amershi et al. (2019) for human-AI interaction.

**Ask Olga at the meeting:** "Are you OK with the camera correction? It changes one paragraph; the rest preserves your structure." If yes, she pastes this version into the .docx.

---

## §B — Section 7 (Hamad's prose, with wording pass)

**Why edited:** Hamad's draft uses two phrases the group has explicitly moved away from since the Apr 26 meeting: "AI-augmented instructional dashboard" and "AI-generated instructional recommendations." The artifact is rule-based, not ML; the recommendation pathway is deterministic and traceable. The edit substitutes "rule-based instructional decision-support dashboard" and "rule-based advisory recommendations" while preserving the RQ structure, instrument mapping, and analysis logic. One factual fix: the IDSS does not measure "engagement" — it surfaces observable participation. Hamad's mapping to TAM, NASA-TLX, paired t-tests, and thematic analysis is preserved unchanged.

> **7. Linking Evaluation Data to the Research Questions**
>
> The evaluation is designed to directly address the three research questions by systematically linking collected data, measurement instruments, and analysis methods to each research objective. A mixed-methods approach is employed to combine quantitative measures with qualitative insights, ensuring both measurable evidence and deeper understanding of instructor experiences.
>
> **RQ1 — Design Question:** *How can a design artifact be developed to transform real-time online classroom data into interpretable instructional decision-support signals for instructors?* This research question is addressed through a combination of perceived-usefulness measures and qualitative interview data. Perceived usefulness, measured using a Technology Acceptance Model (TAM)-based scale, provides indirect evidence by capturing whether instructors believe the system improves their ability to interpret classroom dynamics and make instructional decisions. Because interpretability is not directly measured by TAM, qualitative interview questions explicitly examine how instructors interpret the system's observable-participation signals and recommendation evidence, and whether the summarized indicators are easier to work with than raw classroom data. Together, these measures provide complementary evidence that the artifact supports interpretation and sensemaking of real-time classroom information.
>
> **RQ2 — Evaluation Question:** *To what extent does a rule-based instructional decision-support dashboard reduce instructor cognitive load and support adaptive teaching behaviors during synchronous online classes?* This question is addressed through the experimental design comparing two conditions: without the dashboard (baseline) and with the dashboard (treatment). Cognitive load is measured using NASA-TLX in both conditions, and differences are analyzed using paired-sample t-tests (or a non-parametric alternative if distributional assumptions are violated). A statistically significant reduction in cognitive load in the dashboard condition would indicate that the artifact reduces instructor mental workload during synchronous online teaching. Perceived-usefulness measures provide additional quantitative evidence of perceived instructional value, while qualitative interview responses offer deeper insight into how instructors adapt their teaching behavior when supported by the system. Together, these results assess whether the artifact enhances instructor performance under real-time constraints.
>
> **RQ3 — Knowledge Contribution Question:** *What design principles can be derived from instructors' use and perceptions of rule-based advisory recommendations in synchronous online teaching environments?* This question is primarily addressed through qualitative data collected from post-session interviews, supported by quantitative measures of trust in the recommendations. Thematic analysis is used to identify recurring patterns related to trust, explainability, recommendation usage, and user control. Interview questions explicitly examine whether instructors trust the recommendations, how they accept, modify, reject, or ignore them through the five-way response taxonomy, and how the on-card evidence and literature grounding influence their decisions. These insights enable identification of key themes such as selective reliance, importance of transparency, and the need for instructor agency, which directly inform the refinement of design principles. Quantitative trust scores further support these findings by indicating overall confidence in the system.
>
> **Cross-cutting evaluation tie-back.** In addition to the survey instruments and interview data, the artifact records its own behavioral evidence during each evaluation run. The five-way response taxonomy distribution, per-response behavioral-impact deltas, and pattern-detection telemetry described in Section 3 are exportable as a single SAGE evaluation-run artifact and are aligned with each participant's survey or interview record. This cross-tabulation enables the study to ask not only whether instructors reported the dashboard as useful, but also what the artifact was actually surfacing during their session and how they responded.
>
> Overall, by explicitly linking evaluation data to each research question, the study ensures that the evaluation not only assesses artifact performance but also demonstrates how the artifact supports interpretation, supports instructional decision-making, and contributes to the development of design knowledge in advisory learning-analytics systems.

**Ask Hamad at the meeting:** "Two wording substitutions and one cross-cutting paragraph. Structure and instrument mapping preserved. OK to paste this version?" If yes, he pastes this into the .docx.

---

## §C — Outcome Metrics scaffold (Samantha-owned)

**Why scaffold, not final prose:** Outcome Metrics is Samantha's slice. This scaffold covers what the artifact can already measure so Samantha can finalize wording and add the longitudinal-outcome framing. Items in brackets are decisions for Samantha.

> **Outcome Metrics.** Outcome metrics capture the artifact's downstream effect on the synchronous-classroom decision cycle. Phase 4 defines four outcome metrics that can be measured immediately and one that is reserved for later naturalistic study.
>
> *Decision latency.* The elapsed time from a recommendation surfacing on the dashboard to an instructor's recorded response across the five-way taxonomy. Reported as median and interquartile range across all surfaced recommendations within a session.
>
> *Recommendation uptake distribution.* The proportion of surfaced recommendations responded to in each of the five categories (ignore, acknowledge, accept, modify, reject). Each category is treated as a valid disposition; the metric describes how instructors actually used the system rather than scoring uptake against any single "correct" response.
>
> *Behavioral-impact delta around interventions.* The change in the class-level observable-participation index between a fixed window before and after each `accept` or `modify` response, exported per session and aggregated across sessions. This metric quantifies whether logged instructor responses are followed by participation-trajectory shifts and is reported descriptively in Phase 4 with explicit acknowledgment that simulated-environment causality is not equivalent to live-classroom causality.
>
> *Instructor confidence in recommendations.* Trust-in-AI-recommendation Likert items from the post-session survey (Section 3), reported per scenario and per institutional preset.
>
> *[Out of scope for this evaluation — student learning outcomes.]* Sustained student-side outcomes (achievement, retention, or persistence) require IRB-approved live-classroom deployment over a full course term, which falls outside the in-semester scope of this course project and is identified as future work.

**Ask Samantha at the meeting:** "Does this scaffold match your outcome-metrics framing? You own the final wording and the longitudinal piece."

---

## Evren-owned paste-ready prose

These are referenced from `docs/EVREN_PHASE4_PAPER_DRAFT_PROSE_2026-04-26.md`. **For the meeting, walk through the headers and word counts; do not re-read the full prose during the meeting unless the group requests it.**

| Section | Word count | Source ID |
|---|---|---|
| Behavioral-impact paragraph (precedes Analytical) | ~270 | P3 |
| Analytical (Simulation) — SAGE + FEDS positioning | ~410 | P1 |
| Performance Metrics subsection | ~360 | P2 |
| Artifact Description (standalone section) | ~480 | P4 |
| Recommendation Engine Design Rationale | ~330 | P6 |
| DSR Hevner mapping table (optional appendix) | table + 60 | P7 |
| DSR Knowledge Contribution positioning (optional) | ~150 | P8 |
| Threats to Validity and Scope Limits | ~310 | P9 |
| Quantitative Analysis Approach scaffold (Samantha + Ahmed) | ~260 | P10 |
| Section 7 stub (artifact-side rows of the data-source table) | table + notes | P5 |

---

## Defense talking points (one minute each)

These are the answers to the most likely Chatterjee questions; the underlying detail is in `docs/CHATTERJEE_DSR_DEFENSE_NOTES_2026-04-30.md` and `docs/PHASE4_DEMO_TALKING_POINTS_2026-04-23.md`.

- **"Where does the recommendation engine come from?"** Rule-based pattern detection over a deterministic five-signal weighted composite, grounded in Endsley situation awareness, Sweller cognitive load, Van Leeuwen advising-mode learning analytics, and Amershi human-AI guidelines. Not ML. Each card surfaces its evidence, its institutional-preset context, and its literature grounding. (P6.)
- **"Engagement is multidimensional."** Agreed. The artifact does not claim to measure engagement. It surfaces observable participation signals and explicitly names which engagement dimensions are out of scope (emotional, cognitive, social). The UI carries this scope statement as standing text. (Olga §A and Evren P9.)
- **"Camera is an ethical weakness."** Camera is removed from the scoring composite, rendered for presence context only, with an on-screen non-scoring caveat banner. Stakeholder section now reflects this truthfully. (§A camera correction.)
- **"How do you know it works?"** Phase 4 is **ex ante / formative / artificial** within Venable et al.'s FEDS framework. The claim is technical coherence, evaluable telemetry, and decision-support feasibility — not measured improvement of student learning. Threats to validity section names this explicitly. (P1, P9.)
- **"What about Hevner's seven guidelines?"** Mapping table available as an optional appendix. (P7.)
- **"Is it integrated with Canvas?"** No. Live deployment path is Zoom-webhook-based, with signature verification and ingestion validated against a real Zoom meeting on the hosted deployment. Canvas integration is identified as future work beyond the scope of this course project. (Talking points doc.)

---

## Approval checklist for tomorrow night

- [ ] **Olga** approves the camera correction in §A and pastes that version into the Stakeholders empty header.
- [ ] **Hamad** approves the wording pass in §B and pastes that version into the Section 7 empty header.
- [ ] **Samantha** approves the §C scaffold or replaces it with her final Outcome Metrics prose; commits to a paste timestamp before Friday.
- [ ] **Samantha + Ahmed** confirm whether quantitative analysis uses paired-sample t-tests, ANOVA, or both, and finalize P10 wording.
- [ ] **Ahmed** confirms research-question wording for Section 7 and integrates Hamad's RQ1/RQ2/RQ3 paragraphs against the actual stated questions.
- [ ] **Evren** pastes P1, P2, P3, P4, P6, P9 into corresponding empty headers; confirms whether P7 (Hevner table) and P8 (knowledge contribution) belong in the appendix or get cut for length.
- [ ] **Group** acknowledges the live Zoom hosted-deployment validation receipt as part of the Phase 4 artifact evidence (live JSON export from a real meeting against the hosted webhook).

---

## Submission gate (Friday May 3)

Before submitting:

```bash
cd /Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505
bash scripts/verify_phase4_demo.sh
bash scripts/verify_runtime_metrics.sh
git status --short
```

If all three are clean, the artifact side is green. Submit the .docx.

---

## What is intentionally out of scope for tomorrow

- New pattern detectors, new institutional presets, new survey instruments. The group did not ask for these.
- Canvas integration. Future work beyond the scope of this course project.
- Render deployment of the Zoom webhook. Separate decision lane; only on the critical path if the group commits to a live proof inclusion.
- Reopening engagement vs. observable-participation framing. Settled at Apr 26.
- Reopening camera scoring. Settled at Apr 26 and reflected in code (`c2a36f7`).
