# Packet → Current State Reconciliation
**Date:** 2026-04-26
**Reference packet:** `share/2026-03-28-group-packet/01-IST505-Group-Packet.pdf` (shared with group on 2026-03-28)
**Purpose:** One-page diff between the agreed group framing and what the prototype actually does today, so feedback that cites the packet can be answered cleanly.

---

## What still holds from the packet

| Packet claim | Status |
|---|---|
| Project framing: IDSS + SAGE evaluation environment | ✅ Held |
| Novelty #1 — institutional context sensitivity | ✅ Held; now **surfaced on every rec card** |
| Novelty #2 — composition-behavior separation (bias-aware design) | ✅ Held; structurally enforced in `university_presets.py` |
| Novelty #3 — instructor agency / 5-way response taxonomy | ✅ Held; UI enforces in manual mode |
| Don't claim full validation | ✅ Held; framing is formative evaluation |
| Don't oversell live Zoom | ✅ Held; "Live mode is ingestion-only" label on cards |
| Don't lead with "AI recommendations" | ✅ Held; recs are rule-based, LLM enriches sim dialogue only |

---

## What changed since the packet

### 1. Vocabulary: "engagement" → "observable participation"
- **Packet language:** "surface engagement patterns," "engagement behavior is driven by archetypes."
- **Current language:** "observable participation proxy," "five-signal composite."
- **Why:** "Engagement" implied access to internal cognitive/emotional states. We can only observe behavior. The reframe holds the system honest about what it can and can't see.
- **If feedback uses "engagement":** read it as "observable participation" — same loop, more honest label.

### 2. Camera removed from scoring (commit `c2a36f7`)
- **Packet:** Camera was implicitly part of engagement signals.
- **Current:** Five-signal composite is speaking equity 30% / chat 25% / polls 25% / reactions 15% / silence gap 5%. Camera weight = 0.
- **Why:** Zoom webhooks don't reliably emit camera state, and camera-on/off is a poor engagement proxy regardless of signal availability.
- **Today's follow-on (2026-04-26):** Stripped camera modifiers from `INSTITUTIONAL_MODIFIERS` for consistency. Institutional differentiation now lives entirely in drift, attention span, speak tendency, breakout response, and chat frequency — all signals that flow through the five-signal composite.

### 3. Signal evidence visible on every recommendation (commit `623c393`)
- **Packet:** Recommendations were described but not justified on the card.
- **Current:** Each rec card shows "Triggered by [pattern] — [observable measurement]." Example: "Triggered by energy_decay — Mean observable participation dropped 17% since session start (threshold: 10%)."
- **Why:** Phase 3 feedback asked for evidence; this closes that loop.

### 4. Presence-only signal honesty (commit `dbee04e`)
- **Packet:** Joining a meeting could be read as participation.
- **Current:** Joining ≠ activity. Students with zero observable signals (no chat / reactions / polls / hand) render as `no_signal` and are excluded from class engagement averages.
- **Why:** Counting presence as engagement is the failure mode the packet warned about.

### 5. Live-mode ingestion-only label (commit `fb30643`)
- **Packet:** Don't oversell live Zoom.
- **Current:** Live mode shows the ingestion trace and observable signals but disables the 5-way instructor decision UI. A label on each card reads "Live mode is ingestion-only; instructor decisions are exercised in SAGE."
- **Why:** Programmatic interventions in real Zoom aren't supported (no API for "run a poll now"). SAGE is where decision behavior is exercised.

### 6. Institutional context line on rec cards (today, 2026-04-26)
- **Packet:** Claim #1 was the lead novelty but wasn't visually demoable.
- **Current:** Each rec card now carries "Context: [University] — [short institutional description]. Same scenario may surface different patterns under a different preset."
- **Why:** Made claim #1 demoable in the regular 30-second walkthrough without forcing the viewer to read summary stats.

### 7. Post-meeting additions (today, 2026-04-26 — see `docs/MEETING_NOTES_2026-04-26.md`)

After the Apr 26 group meeting transcript was extracted (full ~4,600-line RTF, not the partial paste), eight code changes (C1–C8) and three Zoom polish items (Z1–Z3) landed to close gaps between paper-claims and what the running system surfaces.

| ID | Change | Backs | Files |
|---|---|---|---|
| **C1** | `/api/metrics` endpoint + telemetry pipeline (precision, throttle effectiveness, latency mean/p50/p95, taxonomy adoption, behavioral-impact deltas), under state-lock | Item 9 / Performance Metrics section | `server.py` |
| **C2** | Engagement-scope statement under Class Participation Overview (behavioral + attention slice in; emotional/cognitive/social out) | Item 6 (engagement is multidimensional — specify scope) | `dashboard/index.html` |
| **C3** | Behavioral-impact delta surface (pre/post participation around each logged response, computed server-side, displayed with means by 5-way category) | Item 4 / behavioral-impact paragraph | `server.py`, `dashboard/index.html` |
| **C4** | SAGE evaluation-run export (`/api/export?format=json|csv`) — citable artifact with metadata, timeline, recs, responses, metrics | Item 13 / Analytical (Simulation) section | `server.py`, `dashboard/index.html` |
| **C5** | Camera-presence non-scoring caveat banner above classroom grid | Item 7 / camera ethical reframe | `dashboard/index.html` |
| **C6** | Lit-grounding line on every rec card (Endsley/Sweller/Van Leeuwen/Wise & Jung/Amershi keyed by pattern type); markdown export carries it | Item 5 (define recommendations — how created) | `dashboard/index.html` |
| **C7** | Live System Performance Metrics panel (collapsible details, summary line, taxonomy bar, per-pattern breakdown, behavioral-impact list) | Item 9 demo-side; surfaces C1 telemetry | `dashboard/index.html` |
| **C8** | `scripts/capture_dashboard.py` Playwright-based reproducible screenshot capture with `.meta.json` sidecars (git SHA, scenario, seed, university) | Item 13 / paper figure reproducibility | `scripts/capture_dashboard.py` |
| **Z1** | Meeting topic + host email captured from `meeting.started`, surfaced on Live Signal Trace card | Live demo readability | `simulator/zoom_adapter.py`, `dashboard/index.html` |
| **Z2** | `simulator/zoom_api_client.py` + three probe endpoints (`/api/zoom/probe`, `/probe/meetings`, `/probe/participants`) — Zoom integration testable from a laptop with just a Bearer token | Local-development smoke-test path; supports the runbook | `simulator/zoom_api_client.py`, `server.py` |
| **Z3** | `docs/ZOOM_LIVE_DEMO_RUNBOOK.md` — 6-step rehearsed path for live Zoom validation, with pre-flight, troubleshooting, and Phase-4-paper-framing guidance | Honest framing for "Zoom path is technically sound, deployment-step blocked on Render secret" | `docs/ZOOM_LIVE_DEMO_RUNBOOK.md` |

**Verification posture:** All eleven additions covered by `bash scripts/verify_phase4_demo.sh` (still green). End-to-end smoke tests via `curl` confirm `/api/metrics`, `/api/export`, `/api/zoom/probe`, response taxonomy aggregation, and behavioral-impact delta computation all work with real simulation data. **Browser-side UI verification is partial** — DOM elements confirmed in served HTML; full visual rendering not validated in a real browser since this session has no browser access. `scripts/capture_dashboard.py` will produce that verification once Playwright is installed and a server is running.

**Commit posture:** All changes uncommitted. CLAUDE.md prefers Codex review pre-commit; Codex credit currently out. Decision held for Evren.

**Paper draft prose for the Evren-owned sections** (P1 Analytical/SAGE, P2 Performance Metrics, P3 Behavioral-impact, P4 Artifact Description) lives at `docs/EVREN_PHASE4_PAPER_DRAFT_PROSE_2026-04-26.md` — paste-ready for the Word draft.

---

## Posture on Zoom Marketplace App

- **Built:** Yes, app is registered and webhook endpoint exists.
- **Wired:** Webhook signature verification logic is in `server.py`. Zoom Marketplace App is published.
- **Deployed secret:** `ZOOM_WEBHOOK_SECRET` is *not* set on Render at the time of this doc. Hosted endpoint will accept webhook payloads without HMAC verification until that's wired.
- **Honest framing for the group:** Zoom path is technically sound and locally tested; final secret wiring on the hosted side is the last config step before a live meeting drives it. This is a deploy step, not a code step.

---

## Division of labor (still as packet specified)

| Owner | Slice |
|---|---|
| Evren | Artifact description, screenshots, dashboard walkthrough, simulation architecture, proof-of-concept |
| Writing team | Problem statement, lit gap synthesis, competing-systems positioning, design principles, kernel-theory-to-feature mapping |
| Whole group | One agreed novelty statement, one evaluation story, one consistent claim set |

If the group's feedback shifts the writing slice (e.g., asks Evren to take more prose or asks the writing team to take more artifact framing), this is the surface to update.

---

## Open questions worth flagging if not raised by the group

1. **Persistence:** Session state is in-memory. Render free tier wipes on redeploy. No data carries across sessions. Acceptable for formative eval; would matter for any longitudinal study.
2. **Auth:** Dashboard is public. Anyone with the URL can run sims and log responses. Acceptable for the demo; would matter for any external user testing.
3. **SAGE agent profile validation:** 15 archetypes are not validated against real classroom behavior. This is formative-eval scope, not summative.
4. **Pattern thresholds preset-aware?** Currently no — `silent_majority` triggers when more than 50% of active students hold zero contributing signals (no speaking, chat, polls, or reactions), regardless of institutional preset. Whether GA Tech's silent-majority threshold should differ from Howard's is a defensible follow-on question identified as future work beyond the scope of this course project; would need real classroom data to ground.
