# Phase 4 Demo Talking Points — Apr 23, 2026

Reference card so the group uses consistent verbal framing that matches the committed code.

## 30-second opening

> The artifact under study is an **Instructional Decision Support System (IDSS)** for
> synchronous online teaching. **SAGE** is the simulation and formative-evaluation
> environment used to exercise and evaluate the IDSS. **Zoom live monitoring** is the
> intended real-time deployment path; the current Zoom implementation is prototype-level.
>
> The system does not claim to measure engagement, attention, or learning. It surfaces
> **observable-participation proxy signals** — speaking time, chat activity, poll responses,
> reactions — and offers rule-based advisory prompts. The instructor interprets and
> decides.

## Answering the professor's Phase-3 feedback

### "How are recommendations created — AI or literature?"

Rule-based pattern mapping, not an ML classifier. Weighted composite in
`simulator/scoring.py:22-28`:

| Signal | Weight |
|---|---|
| Speaking equity | 30% |
| Chat activity | 25% |
| Poll participation | 25% |
| Reaction frequency | 15% |
| Silence gap | 5% |

Literature-grounded: Endsley (1995) SA Levels 1–3, Sweller (1988) cognitive load,
Amershi et al. (2019) human–AI interaction guidelines, Van Leeuwen et al. (2019)
advising mode. LLMs enrich simulated student chat dialogue in SAGE but do **not**
generate or alter recommendations.

### "Engagement is multi-dimensional — a silent student may be engaged, a chat-spammer may be disengaged"

Agreed. That's why:

1. **We don't call it engagement.** The UI says "Observable Participation" and the
   sticky caveat on the recommendations panel reads: *"Proxy signal, not engagement
   truth. Silence may mean focus; chat volume may mean skimming. The instructor
   interprets and decides."*
2. **Every recommendation card shows its triggering signal** on screen (e.g.,
   "Triggered by equity imbalance — Speaking Gini = 0.62"). The instructor sees the
   mechanism, not just the verdict.
3. **5-way instructor taxonomy** — ignore, acknowledge, accept, modify, reject —
   with a rationale field. Nothing fires without human consent.

### "Camera is an ethical weakness"

Camera was **removed** from `SIGNAL_WEIGHTS` in Phase 4 (commit `c2a36f7`). The five
remaining signals sum to 1.0 without it. Camera is rendered for presence context
only, never scored. Dashboard has a distinct `camera-unknown` state so "no camera
signal observed" is visually different from "camera off" — we never infer camera
status from participation score.

### "Think deeply about your recommendation engine"

The Phase-4 refinement path explicitly avoids expanding the rec engine (which would
compound the critique). Instead:

- Recommendations are framed as advisory, not directive ("one option, not an
  automatic prescription", "before assuming disengagement", "use instructor
  judgment").
- Per-pattern throttling (3-min cooldown) in `server.py:296` prevents the same
  advisory from spamming the log every tick.
- Evidence is visible on every card, so a professor watching the demo can agree
  or disagree with the basis, not just the conclusion.

### "Where and how are these prompts shown?"

In the primary recommendations panel of the dashboard — a standing panel with the
sticky caveat, a helper line explaining the mode (simulated vs live), and a
scrolling list of rec cards. Each card has: priority, minute, message, triggering
signal, candidate intervention, 5-way response buttons, optional modify-intervention
+ rationale form, and a response status when an action is logged.

### "Is it integrated with Canvas?"

Not in this phase. The live deployment path is Zoom-webhook based; Canvas
integration is an explicit Phase-5 / future-work item. This is documented in the
artifact scope block in the dashboard.

## Five-step demo walkthrough

1. **Open the dashboard.** Select scenario `full_scenario`, professor style `none`
   (manual instructor), click **▶ Run**.
2. **Let the sim advance ~10 simulated minutes.** Observable-participation index,
   student grid, patterns panel populate. Point to the sticky caveat on the
   recommendations panel.
3. **Wait for recommendations.** When one appears, point to the *Triggered by…*
   line and narrate: "the system saw X observable signal; the instructor decides
   what to do with that."
4. **Use the 5-way taxonomy.** Click `Modify`, choose a different intervention from
   the dropdown, add a rationale. Repeat with `Accept`, `Reject`, `Ignore` on
   later recs. Log fills with metadata.
5. **Show the live Zoom path.** Click **📡 Live**. Show the sticky signal status
   ("no active meeting") is a clean 200 OK, not a 404. Run the fixture from a
   second terminal (`python3 scripts/send_zoom_fixture.py http://localhost:8000
   --mode rich`) and watch the debug trace populate with real ingested events.

## What NOT to say

- ❌ "The system measures engagement."
- ❌ "AI-generated recommendations."
- ❌ "Camera status signals engagement."
- ❌ "The system knows the student is confused / bored / attentive."
- ❌ "Machine learning classifier."
- ❌ "Replaces the instructor."

## What to say instead

- ✅ "Surfaces observable participation proxy signals."
- ✅ "Rule-based advisory recommendations."
- ✅ "Camera is non-scoring context."
- ✅ "The system flagged N students matching the confusion-cluster signal
   pattern; interpretation is the instructor's."
- ✅ "Weighted composite index over five observable signals."
- ✅ "Supports the instructor's decision; the instructor decides."

## Verification before the meeting

```bash
cd /Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505
bash scripts/verify_phase4_demo.sh
python3 server.py                        # leave running
# in another terminal:
python3 scripts/send_zoom_fixture.py http://localhost:8000 --mode rich
```

If all three exit clean (verify `phase4-demo-verify-ok`, server boots,
fixture exits 0), the demo path is green.

## Known scope-limits to acknowledge if asked

- Current Zoom live implementation is prototype-level (works with webhooks +
  secret signature verification, fixture-tested end-to-end, but not yet
  validated against a fully in-the-wild Zoom meeting on the hosted Render
  deployment).
- Evaluation is formative: SAGE demonstrates technical feasibility and workflow
  coherence. The survey supplies early usability/perception input — not a
  full validation study.
- No Canvas/LMS integration yet.
- Modifying interventions in the browser-only manual path logs the response
  but does not inject classroom-state effects; the server-attached path does.
