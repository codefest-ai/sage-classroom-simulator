# Zoom Live-Demo Runbook

**Purpose:** Step-by-step path for connecting a real Zoom meeting to the IDSS dashboard, so the live ingestion path can be exercised against an actual meeting (rather than only the local fixture).

**Status as of 2026-05-07:** Webhook endpoint exists (`/api/zoom/webhook`), HMAC-SHA256 signature verification implemented in `simulator/zoom_adapter.py`, OAuth multi-install layer (`/api/zoom/connection`, `/api/zoom/connect`, `/api/zoom/oauth/callback`, `/api/zoom/disconnect`, `/api/zoom/oauth/refresh`) and per-install runtime scoping live, Zoom General App registered with both OAuth and Event Subscriptions on the same app. Hosted at `https://sage-simulator-ulsd.onrender.com/`.

**The product architecture is a single Zoom General App** that does both OAuth (each teacher OAuth-installs to authorize their Zoom account) and Event Subscriptions (the same app's webhook delivers their meeting events). Multiple Zoom accounts can be connected to the same dashboard instance — webhook events are routed to the matching install by `account_id` from the event payload, and live state, history, recommendations, and decision logging are scoped per install.

> **Migration note:** the project briefly used a separate "Webhook Only" Marketplace app to deliver events while OAuth was being added. The General App now subsumes both responsibilities. Once you've validated the General App's webhook against the hosted URL and confirmed events arrive (`/api/zoom/debug` shows `known_meetings > 0` after a real meeting), disable the legacy Webhook Only app's event subscription so events don't double-deliver.

This runbook is the rehearsal path. Run through it before promising a live demo to the group.

---

## Pre-flight

### Prerequisites
- Zoom Marketplace **General App** (a.k.a. OAuth app) registered. User-managed unless you specifically need an institutional admin install. This single app handles both OAuth and Event Subscriptions.
- Zoom OAuth Client ID, Client Secret, and Redirect URL from the Marketplace App console (OAuth section).
- Zoom Webhook Secret Token from the Event Subscriptions section of the same app.
- Render deployment URL (or any public HTTPS endpoint that points at `server.py`).
- A Zoom account that can host the demo meeting.
- Server has the OAuth + webhook envs configured: `ZOOM_OAUTH_CLIENT_ID`, `ZOOM_OAUTH_CLIENT_SECRET`, `ZOOM_OAUTH_REDIRECT_URL`, `ZOOM_OAUTH_STORE_DIR`, and `ZOOM_WEBHOOK_SECRET`.

### OAuth-first teacher flow (preferred)

```text
Dashboard → 🔌 Connect Zoom Account → /api/zoom/connect
  → Zoom authorize page (teacher signs in, approves scopes)
  → /api/zoom/oauth/callback?code=...&state=...
  → server exchanges code for tokens, fetches /v2/users/me, stores install
  → redirect to /?zoom_connected=1&install_id=<sanitized-account-id>
  → dashboard chip flips to "Connected: alice@cgu.edu"
```

The server stores one JSON file per install under `ZOOM_OAUTH_STORE_DIR`, keyed by sanitized `account_id` (or `user_id` fallback). `/api/zoom/connection` returns the full installs[] array; `/api/zoom/disconnect` accepts a `{"install_id": "..."}` body and removes one install at a time.

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

## Step 1 — Configure the Zoom General App (single primary app)

This is the only Zoom app the deployed product needs. It handles **both** OAuth (teacher Connect Zoom Account) and Event Subscriptions (live meeting webhooks). The legacy Webhook Only app the project used during early exploration is now redundant and should be retired once the General App is validated.

1. Go to [Zoom App Marketplace](https://marketplace.zoom.us/develop/apps) → **Develop → Build App** → **General App**.
2. Under **App Credentials**, copy the **Client ID** and **Client Secret** (you'll set these as `ZOOM_OAUTH_CLIENT_ID` / `ZOOM_OAUTH_CLIENT_SECRET` on the server).
3. Under **Basic Information** select **User-managed app** (each teacher OAuth-installs for themselves) unless you want the institutional admin-managed install path.
4. Set **OAuth Redirect URL** to `https://<your-render-host>/api/zoom/oauth/callback` (this becomes `ZOOM_OAUTH_REDIRECT_URL`).
5. Under **Scopes**, add:
   - `user:read:user` (lets the server call `/v2/users/me` once on connect)
   - `user:read:email` (so the install record stores the connecting teacher's email)
6. Under **Features → Event Subscriptions**, toggle ON, then add:
   - **Subscription Name:** `IST505 Live Events`
   - **Event Notification URL:** `https://<your-render-host>/api/zoom/webhook`
   - **Subscribe to events:**
     - `meeting.started`
     - `meeting.ended`
     - `meeting.participant_joined`
     - `meeting.participant_left`
     - `meeting.chat_message_sent`
     - `meeting.participant_raised_hand`
     - `meeting.participant_lowered_hand`
     - `meeting.reaction_received`
7. Copy the **Secret Token** in the Event Subscriptions section (this becomes `ZOOM_WEBHOOK_SECRET`).
8. Click **Save**. Zoom posts an `endpoint.url_validation` event to the webhook URL; the server auto-responds with the HMAC challenge using `ZOOM_WEBHOOK_SECRET`. The status flips to validated.

While the General App stays in Local Test mode, only the developer Zoom account (yours) plus explicitly added Test Users can install it. Add teammate emails under **Local Test → Test User Account**.

---

## Step 2 — Set server env vars

### Render
1. Open the Render dashboard → service → **Environment**.
2. Add (or update) all of:
   - `ZOOM_OAUTH_CLIENT_ID`
   - `ZOOM_OAUTH_CLIENT_SECRET`
   - `ZOOM_OAUTH_REDIRECT_URL = https://<your-render-host>/api/zoom/oauth/callback`
   - `ZOOM_OAUTH_STORE_DIR = /tmp/sage_zoom_oauth_installs` (course-demo default; mount a persistent disk for production)
   - `ZOOM_WEBHOOK_SECRET` (the General App's Event Subscription Secret Token)
3. Render auto-redeploys on env-var change.

### Local
```bash
ZOOM_OAUTH_CLIENT_ID="..." \
ZOOM_OAUTH_CLIENT_SECRET="..." \
ZOOM_OAUTH_REDIRECT_URL="http://localhost:8080/api/zoom/oauth/callback" \
ZOOM_OAUTH_STORE_DIR="/tmp/sage_zoom_oauth_installs" \
ZOOM_WEBHOOK_SECRET="..." \
python3 server.py
```
For local OAuth round-trip the redirect URL must be reachable from a browser, so a tunnel (e.g., cloudflared, ngrok with reserved domain) is useful when testing without Render.

---

## Step 3 — Validate the webhook handshake and OAuth wiring

```bash
curl https://<your-render-host>/api/health | jq .
# expect: zoom_webhook_configured: true, zoom_oauth_configured: true

curl https://<your-render-host>/api/zoom/connection | jq .
# expect: oauth_configured: true, install_count: 0 before any teacher connects

curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" https://<your-render-host>/api/zoom/connect
# expect: 302 with redirect_url starting with https://zoom.us/oauth/authorize
```

If `/api/zoom/connection` reports `storage_warning`, installs are persisted under `/tmp` and will be wiped on redeploy. For real classroom use, mount a Render persistent disk and set `ZOOM_OAUTH_STORE_DIR` to that mount.

---

## Step 4 — Connect a teacher and start a meeting

1. Open the dashboard at `https://<your-render-host>/`.
2. Click **🔌 Connect Zoom Account**. Zoom redirects to the OAuth authorize page; the teacher signs in and approves the requested scopes; control returns to the dashboard with `?zoom_connected=1` and the chip flips to `Connected: <email>`.
3. (Multi-install) Other teachers repeat step 2 from their own Zoom logins. The dropdown chip lists every connected install; the teacher viewing the dashboard picks **Switch to** to scope the live view to a different install.
4. Start a Zoom meeting from the connected account. Have at least one other participant join (a guest joining via incognito browser counts).
5. Click **📡 Monitor Live Class** on the dashboard. The dashboard polls `/api/zoom/state?install_id=...` and renders:
   - Live Meeting Overview index updating
   - Current Participants populated
   - Live Signal Trace showing recent raw events
6. (Decision Support mode) Recommendation cards surface as patterns trigger. The 5-way taxonomy (ignore / acknowledge / accept / modify / reject) is active and writes to the live receipt.
7. (Monitor Only mode) Recommendation panel hidden; everything else still flows. Pattern detections continue server-side and are logged to the receipt regardless of mode.

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
   - Instructor responses recorded through the live 5-way decision UI
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
