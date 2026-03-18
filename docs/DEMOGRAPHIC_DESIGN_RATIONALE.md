# Demographic Design Rationale — SAGE v2 University Presets
## Design Decision Trace for DSR Evaluation Section

**Date:** March 17, 2026
**Context:** SAGE v2 build session, IST 505 group project

---

## The Problem

SAGE v1 used 15 hand-picked student profiles with names suggesting broad demographic diversity (Priya Sharma, Marcus Chen, Amara Okafor, Tyler Morrison, etc.). This was a diversity catalog, not a realistic classroom. Real graduate seminars have demographic *clustering* based on the institution's enrollment pipeline.

## What We Built First

University demographic presets using real enrollment data from IPEDS, Peterson's, and institutional research offices:

| University | Data Year | Source |
|---|---|---|
| CGU CISAT | 2023-24 | Peterson's, IPEDS Unit ID 112251 |
| Georgia Tech CoC | Fall 2024-25 | GT IRP Fall 2025, OMSCS Annual Report 2024 |
| Howard CS | 2023-24 | Peterson's, IPEDS Unit ID 131520 |

Each preset generates 15 profiles with demographic distributions drawn from that school's real enrollment: gender split, race/ethnicity breakdown, international student percentage, age range, working professional rate, and program-specific majors.

## The Dilemma We Encountered

### If you ignore demographics:
- The simulation doesn't reflect reality
- The IDSS is evaluated against a fake classroom
- Findings don't generalize — "works for 15 made-up people" isn't evidence

### If you map demographics to behavior:
- You encode racial assumptions into an educational tool
- "International students drift faster" or "Black students participate more in breakouts" = racial stereotyping dressed as data
- The education literature does NOT support demographic → learning behavior mappings at the individual level
- This is exactly the kind of system bias that DSR should surface, not reproduce

### The resolution: separate composition from behavior

**Demographics drive *composition*** — who is in the room. This comes from real enrollment data and affects what the classroom *looks like*.

**Institutional context drives *behavior*** — how the room functions. This comes from structural/institutional factors:

| Structural Factor | What It Affects | Why It's Not Racial |
|---|---|---|
| Working professional % (GT 87% vs Howard 25%) | Camera-on rates, drift rates, attention span | Job/schedule constraint, not identity |
| Cohort size (Howard 21 vs CGU 153 vs GT 16,900) | Participation pressure, social accountability | Structural visibility, not cultural trait |
| Platform norms (OMSCS = camera-off culture) | Camera defaults, chat-vs-speak preference | Platform convention, not demographics |

### Institutional context modifiers implemented:

```
Georgia Tech: camera_on -0.15 (everyone), drift +0.005 (multitasking norm),
              attention -3min, speak -0.05, chat +0.03 (compensatory)
              Working pro: camera -0.30 additional, drift +0.012, attention -8min

Howard:       camera_on +0.10 (small cohort accountability), drift -0.003,
              attention +2min, speak +0.03, breakout +0.05

CGU:          Baseline (no institutional adjustments beyond working pro effects)
```

## Empirical Result

Same scenario (full_scenario), same seed (42), same 15 archetypes — different IDSS outputs:

| Metric | CGU | Georgia Tech | Howard |
|---|---|---|---|
| Working professionals | 6/15 | 12/15 | 2/15 |
| Avg camera rate | 0.54 | 0.29 | 0.70 |
| Avg drift rate | 0.025 | 0.037 | 0.020 |
| Avg engagement | 0.400 | 0.339 | 0.433 |
| Total recommendations | 28 | 36 | 25 |
| Energy decay detections | 20 | 28 | 18 |
| Recommendation types | breakout, pace_change | breakout, pace_change, poll | breakout, pace_change |

Georgia Tech's IDSS fires 36 recommendations (most) with more `poll` suggestions — appropriate for a working-professional cohort that drifts faster and can't commit to 5-minute breakouts between meetings. Howard's fires fewest (25) because small-cohort accountability keeps engagement higher.

## The DSR Claim

The IDSS artifact adapts its recommendations to institutional context. The same dashboard, given the same lesson scenario, produces different intervention patterns for different institutional settings — not because of who the students are, but because of the structural conditions they're learning in.

This is a legitimate finding about the artifact's context sensitivity, not a claim about demographics and learning.

## What We Explicitly Do NOT Do

1. Map ethnicity → learning style
2. Map race → engagement baseline
3. Map gender → participation tendency
4. Map national origin → any behavioral parameter
5. Claim that demographic composition *causes* engagement patterns

Demographics are reportable (visible in the transcript, avatars, and metadata) but do not enter the engagement model. The engagement model sees archetypes + institutional modifiers only.

---

*This document traces a design decision made during the build. The dilemma itself — and how it was resolved — is part of the DSR formative evaluation evidence.*
