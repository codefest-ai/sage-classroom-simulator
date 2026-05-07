# Zoom Live-Demo Runbook

**Purpose:** Step-by-step path for connecting a real Zoom meeting to the IDSS dashboard, so the live ingestion path can be exercised against an actual meeting (rather than only the local fixture).

**Status as of 2026-04-26:** Webhook endpoint exists (`/api/zoom/webhook`), HMAC-SHA256 signature verification implemented in `simulator/zoom_adapter.py:525`, Zoom Marketplace App registered, fixture-tested end-to-end locally. **Blocker for live execution:** `ZOOM_WEBHOOK_SECRET` not yet set on the Render deployment. Once that lands, follow this runbook to validate end-to-end.

This runbook is the rehearsal path. Run through it before promising a live demo to the group.

---

## Pre-flight

### Prerequisites
- Zoom Marketplace App registered (already done; "Webhook Only" type).
- Zoom Secret Token from the Marketplace App console.
- Render deployment URL (or any public HTTPS endpoint that points at `server.py`).
- A Zoom account that can host the demo meeting.
- Server has the secret token configured: `ZOOM_WEBHOOK_SECRET=<token>` in env.

### Local API probe (optional, no public webhook required)

If you have a Zoom OAuth access token or JWT (server-to-server app or legacy
JWT app), the integration can be exercised from a laptop without setting up
the public webhook path. This is useful for confirming that token / app
permissions are correct before configuring the production webhook.

```bash
ENABLE_ZOOM_API_PROBE=1 ZOOM_API_TOKEN="<bearer>" python3 server.py &
curl -s http://localhost:8080/api/zoom/probe | jq .          # GET /users/me
curl -s "http://localhost:8080/api/zoom/probe/meetings?type=scheduled" | jq .
curl -s "http://localhost:8080/api/zoom/probe/participants?id=<meeting_id>" | jq .
```

A token can also be passed per-request: `?token=<bearer>` (do not commit any
real tokens). Read-only endpoints only — see `simulator/zoom_api_client.py`.
Do not set `ENABLE_ZOOM_API_PROBE=1` on public demo hosts; the probe path is for
local development only.

### Local fixture sanity check (do this first)
```bash
cd /Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505
ZOOM_WEBHOOK_SECRET="local-test-secret" python3 server.py &
SERVER_PID=$!

# In another terminal:
python3 scripts/send_zoom_fixture.py http://localhost:8080 --mode rich
# Expected: fixture exits 0, server logs "[zoom webhook] event=..." for each fixture event.
# Open http://localhost:8080 → click 📡 Live → observe ingestion trace populates.

kill $SERVER_PID
```
If fixture path doesn't work locally, **stop here** — fix that before attempting a live meeting.

---

## Step 1 — Configure the Zoom Marketplace App

1. Go to [Zoom App Marketplace](https://marketplace.zoom.us/develop/apps) and open the IDSS app.
2. Under **Feature → Event Subscriptions**, set:
   - **Event Notification URL:** `https://<your-render-host>/api/zoom/webhook`
   - **Add events** (subscribe to all of these — see `simulator/zoom_adapter.py:535-`):
     - `meeting.started`
     - `meeting.ended`
     - `meeting.participant_joined`
     - `meeting.participant_left`
     - `meeting.chat_message_sent`
     - `meeting.participant_raised_hand`
     - `meeting.participant_lowered_hand`
     - `meeting.reaction_received`
3. Under **App Credentials**, copy the **Secret Token** (this is what becomes `ZOOM_WEBHOOK_SECRET`).
4. Click **Save**. Zoom will send a `endpoint.url_validation` event to the webhook URL — the server responds with the HMAC challenge automatically (`zoom_adapter.py:541-546`). If validation fails, check that the secret token in env matches what's in the Marketplace console.

---

## Step 2 — Set the secret on the deployed server

### Render
1. Open the Render dashboard → IDSS service → Environment.
2. Add `ZOOM_WEBHOOK_SECRET` with the value from Step 1.3.
3. Trigger a deploy (Render restarts the service with the new env).

### Local (for end-to-end without Render)
```bash
ZOOM_WEBHOOK_SECRET="<token>" python3 server.py
```
Then expose the local port via a tunnel (e.g., `ngrok http 8080`) and use the tunnel URL as the Marketplace Event Notification URL for the duration of the demo.

---

## Step 3 — Validate the webhook handshake

Without starting a meeting, hit:
```bash
curl https://<your-render-host>/api/zoom/state | jq .
```
Expected: `{"active": false, "reason": "No active Zoom meeting has been seen on this server yet.", ...}` (200 OK, not 404).

This confirms the server is reachable and the live endpoint is wired.

---

## Step 4 — Start the meeting

1. Open the dashboard at `https://<your-render-host>/`.
2. Click **📡 Live** to switch to live mode. The dashboard will start polling `/api/zoom/state`.
3. From a separate device, **start a Zoom meeting** with the host account. Server should log:
   ```
   [zoom webhook] event=meeting.started meeting_id=<id>
   ```
4. Have at least 2 participants join (ideally with chat enabled). Server should log `meeting.participant_joined` per join.
5. Send a few chat messages. Server should log `meeting.chat_message_sent`.
6. Trigger a reaction (👍, ✋). Server should log `meeting.reaction_received`.
7. The dashboard should now render:
   - "Live participation" index updating
   - Per-participant tile in the classroom view
   - Live trace populated in the live-mode debug panel
   - The **camera-presence caveat** banner above the classroom grid (camera is non-scoring per the meeting decision; this is the visual confirmation)

---

## Step 5 — Confirm recommendations fire

If the meeting includes a few minutes of asymmetric participation (e.g., one person dominates chat, others silent), the live recommender should surface a `silent_majority` or `equity_imbalance` rec card with:
- **Triggered by [pattern]** — observable evidence
- **Context: [University]** if a university preset was set on the live session
- **Grounding:** literature reference per pattern
- 5-way decision UI active on each recommendation card (decisions are recorded for the evaluation receipt; the artifact does not programmatically trigger actions in Zoom — the instructor executes the chosen action directly in the meeting)

If no recs fire after ~5 minutes of varied participation, check `/api/zoom/debug` for the raw event trace and confirm patterns are being detected by the scorer.

---

## Step 6 — End the meeting and capture the run

1. End the Zoom meeting. Server should log `meeting.ended`.
2. From the dashboard, click **📦 SAGE Run (JSON)** to download the full ingested run as a citable artifact. The export includes:
   - Per-participant join/leave history
   - Chat events
   - Reaction events
   - Computed observable-participation index per minute
   - Recommendations surfaced (with evidence)
   - Performance metrics snapshot

Save this JSON alongside the paper as the live-validation receipt.

---

## Known limitations

- **No programmatic intervention.** Zoom's API does not expose "start a poll now" or "create a breakout room mid-meeting" via webhooks. The 5-way instructor decision UI is available in live mode and records the instructor's response (category, intervention type, rationale) for the evaluation receipt, but the artifact does not actuate the action inside the Zoom meeting — the instructor executes the chosen action directly in Zoom (e.g., launching a Zoom poll using Zoom's native UI).
- **Webhook reliability.** Zoom's webhook delivery is at-least-once; duplicate events should be tolerated by `zoom_adapter.py` but bursts may briefly desync the index.
- **Camera state inference.** Zoom webhooks do not consistently emit camera on/off state. The dashboard renders camera-unknown tiles distinctly and **does not infer camera state from participation score** (per the camera-removal decision, commit `c2a36f7`).
- **No persistence.** Render free-tier session state wipes on redeploy. For a live demo, do not redeploy mid-session.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Webhook events 401 in server logs | `ZOOM_WEBHOOK_SECRET` mismatch | Re-copy from Marketplace, update env, redeploy |
| Dashboard live mode shows "no active meeting" forever | Webhook URL not reaching server | `curl <webhook-url>` from outside; check Render is awake (free tier may sleep) |
| `endpoint.url_validation` validation fails | Secret token in env differs from Marketplace token | Set the env var to the exact token shown in the Marketplace console |
| Recs never fire on a live meeting | Insufficient signal volume; scorer waiting for thresholds | Have participants chat / react more actively, or check `/api/zoom/debug` for ingest trace |
| Camera tiles all show "no signal" | Zoom webhook didn't emit camera state | Expected behavior; camera state is non-scoring regardless |

---

## Phase 4 paper framing

This runbook is the operational evidence behind the paper's "Deployment-oriented extension" claim. Acknowledge in the paper:

- Live Zoom path **exists**, is **signature-verified**, **fixture-tested end-to-end**, and **validated against a real Zoom meeting on the hosted deployment** (the resulting per-tick JSON export is the live-validation receipt).
- Live mode supports the full instructor decision loop: real-time ingestion from Zoom webhooks, rule-based recommendations surfaced from real participation patterns, and the 5-way response taxonomy with rationale recorded for the evaluation receipt. The artifact records decisions but does not actuate them in Zoom; the instructor executes the chosen action in the meeting directly.

Future work beyond the scope of this course project: programmatic intervention via Zoom REST APIs (start poll, create breakout room, send chat from host), stronger camera-state inference, persistence beyond Render free tier, and multi-tenant deployment.
