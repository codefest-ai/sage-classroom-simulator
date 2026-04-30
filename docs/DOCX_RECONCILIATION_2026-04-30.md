# Almost-Final Docx Reconciliation — Apr 30, 2026

**Source:** `~/Downloads/IST 505 Final Project Phase 4 (almost final).docx` (received from Evren Apr 30 evening).
**Comparison:** Against the integrated packet at `docs/MEETING_PACKET_2026-05-01.md`, paste-ready prose at `docs/EVREN_PHASE4_PAPER_DRAFT_PROSE_2026-04-26.md`, and the Apr 26 group meeting decisions.

---

## The headline

About 60% done. The Ahmed-owned scaffolding is solid. The teammate paste-ins arrived in their **raw** form (not the corrected versions in the meeting packet), so the camera contradiction and the "AI-generated" wording are now inside the docx and need to come out before submission. Several Evren-owned sections are still missing entirely.

---

## Critical fixes — must land before Friday

### 1. Camera contradiction inside the Stakeholders section
**Where:** Stakeholder Groups and Ethical Recruitment Strategy → Students paragraph.
**Current text:** *"...while the system may use intrusive signals such as camera-based data, all video recordings will be deleted immediately after processing."*
**Problem:** Directly contradicts the artifact. Camera was removed from `SIGNAL_WEIGHTS` (`simulator/scoring.py`, commit `c2a36f7`), is rendered for presence context only, and the dashboard now carries an explicit non-scoring caveat banner above the camera grid. A grader who looks at the artifact will catch this in seconds.
**Fix:** Replace that single sentence with: *"Camera state is excluded from the participation composite by design and rendered for presence context only; no video content is processed, scored, or stored by the artifact, and no inference about engagement or attention is drawn from camera-on or camera-off status. This decision was made on ethical grounds in response to the multidimensional nature of engagement and to avoid penalizing students for reasons unrelated to learning (bandwidth limits, privacy, environment, or accessibility)."*
**Owner:** Olga to approve at the meeting; Evren or Olga pastes the swap.

### 2. "AI-generated" / "AI-augmented" wording inside Section 7
**Where:** Section 7 — three places: RQ2 ("AI-augmented instructional dashboard"), RQ3 ("AI-generated instructional recommendations"), and the closing summary ("AI-augmented educational systems").
**Problem:** The Apr 26 meeting agreed to retire this language. The artifact is rule-based, not ML — every other section in the docx (User-Centric metrics, Methodology) doesn't use this framing, so Section 7 will read as inconsistent. Chatterjee's Phase 3 critique was already about overclaiming AI; this re-introduces it.
**Fix:**
- "AI-augmented instructional dashboard" → "rule-based instructional decision-support dashboard"
- "AI-generated instructional recommendations" → "rule-based advisory recommendations"
- "AI-augmented educational systems" → "advisory learning-analytics systems"
**Owner:** Hamad to approve at the meeting; Evren or Hamad pastes the substitutions.

### 3. Same wording inside Quantitative Data Analysis Approach
**Where:** First sentence of "Quantitative Data Analysis Approach" — *"...whether the AI-augmented instructional dashboard improves instructors' experience..."*
**Fix:** Same substitution as #2.
**Owner:** Samantha to approve.

### 4. Same wording inside the Descriptive subsection
**Where:** "Descriptive:" paragraph — *"...trust in the AI-generated recommendations..."*
**Fix:** Same substitution.
**Owner:** Whoever wrote this paragraph (likely Ahmed); needs review.

---

## Missing sections — must add before Friday

### 5. Analytical (Simulation) — header is empty
**Where:** "Types of Evaluation → Analytical (Simulation)" — heading present, zero content.
**Source:** P1 prose at `docs/EVREN_PHASE4_PAPER_DRAFT_PROSE_2026-04-26.md` (~410 words, includes the FEDS positioning Chatterjee will look for).
**Owner:** Evren — paste-ready.

### 6. Performance Metrics subsection
**Where:** Section 3 (Measurement and metrics) currently has only "User-Centric Evaluation Metrics" as a subsection. Performance Metrics is missing entirely.
**Source:** P2 prose (~360 words).
**Owner:** Evren — paste-ready. Without this subsection, the paper has no answer to *"what does technical performance look like for an advisory rule-based system?"*

### 7. Outcome Metrics subsection
**Where:** Same parent section. Missing entirely.
**Source:** §C scaffold in `docs/MEETING_PACKET_2026-05-01.md` covers what the artifact can measure (decision latency, uptake distribution, behavioral-impact delta, instructor confidence, plus longitudinal student outcomes flagged as future work).
**Owner:** Samantha — needs final wording from her, but the scaffold is paste-ready in a pinch.

### 8. Behavioral-impact paragraph (precedes Analytical)
**Where:** Should sit immediately before the Analytical (Simulation) subsection.
**Source:** P3 prose (~270 words).
**Owner:** Evren — paste-ready. Samantha noted at Apr 26 that behavioral impact must be defined before evaluation modality.

### 9. Artifact Description (standalone section near front)
**Where:** Currently the docx has no artifact description at all. Reader hits "Evaluation Objective" with no prior anchor of what the IDSS actually is.
**Source:** P4 prose (~480 words) covers dashboard surfaces, evidence-on-card framing, exports, and figure list.
**Owner:** Evren — paste-ready. Confirm placement with Ahmed (probably between problem statement and evaluation method).

---

## Strongly recommended for Chatterjee defense — should add

### 10. Recommendation Engine Design Rationale
**Source:** P6 prose (~330 words).
**Why:** Direct answer to Chatterjee's Phase 3 *"think deeply about your recommendation engine"* feedback. Explains rule-based-not-ML choice, pattern selection, taxonomy rationale, cooldown logic.
**Owner:** Evren — paste-ready.

### 11. Threats to Validity / Scope Limits
**Source:** P9 prose (~310 words).
**Why:** A DSR grader expects this. Without it, every limitation reads as an oversight.
**Owner:** Evren — paste-ready.

### 12. (Optional) DSR Hevner mapping table + Knowledge Contribution
**Source:** P7 + P8 prose.
**Why:** Shows DSR-grader vocabulary. Optional appendix material if space is tight.
**Owner:** Evren — decide at meeting based on current page count.

---

## Structural notes worth raising at the meeting

- **"Methodological Approach" sits inside "Measurement and metrics".** That's a structure quirk — Methodological Approach is usually its own section. Worth a 30-second discussion.
- **Section numbering inconsistency.** Stakeholders is "Heading 1" but unnumbered. Section 7 has "7" prefix but no other section is numbered. Either number all major sections or none.
- **Title is "Phase 4 - Evaluation Method".** Short and accurate. No change needed.
- **References — needs a Venable et al. (2016) entry** if the FEDS framing lands (P1 invokes it). Also Hevner et al. (2004) if the Hevner mapping lands (P7), and Endsley (1995), Sweller (1988), Van Leeuwen et al. (2019) for the kernel theories cited in P1/P4/P6.

---

## What is fine and does not need touching

- Evaluation Objective ✅
- Experimental subsection ✅ (uses "AI-augmented dashboard" once but only describing the experimental treatment label, which is consistent with the rest of the paper if the wording fixes above land — alternatively, swap for "rule-based advisory dashboard" for consistency)
- Methodological Approach ✅
- IRB Justification ✅
- Quantitative Data Collection (SUS, TAM, NASA-TLX, Trust, Satisfaction) ✅
- Appendices A–F ✅
- Qualitative Data Analysis Approach ✅
- Comparative Logic paragraph ✅
- References list ✅ (just needs the new entries above)

---

## Suggested Friday paste order

For Evren on Thursday after the meeting, in order:

1. Apply the four wording fixes (#1–#4) — 5 minutes.
2. Paste P3 (Behavioral-impact), then P1 (Analytical/SAGE) into the Types-of-Evaluation block — 5 min.
3. Paste P2 (Performance Metrics) above User-Centric Metrics — 2 min.
4. Paste §C scaffold or Samantha's final Outcome Metrics — 2 min.
5. Paste P4 (Artifact Description) near the front, placement TBD with Ahmed — 5 min.
6. Paste P6 (Recommendation Engine Rationale) — 2 min.
7. Paste P9 (Threats to Validity / Scope Limits) before References — 2 min.
8. Add new References entries — 5 min.
9. Final read-through, fix cross-references — 15 min.

Total time after meeting: ~45 minutes if no scope changes come out of the discussion.

---

## What to walk into the meeting with

A printed or screen-shared copy of this reconciliation, plus the meeting packet at `docs/MEETING_PACKET_2026-05-01.md`. Open with: "Here are four wording fixes and seven paste-ins. The wording fixes need three teammates to sign off; the paste-ins are mine. Let's get the sign-offs and adjourn."
