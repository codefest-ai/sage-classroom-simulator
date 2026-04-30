# Render Deploy Checklist
## Hosted Demo For The Current Prototype

## Goal

Deploy the current IST505 build so teammates can use it from a URL without your laptop running.

## Before You Start

- Make sure the latest `projects/ist505` changes are committed or otherwise available in the repo you plan to connect to Render.
- Decide whether you want:
  - **Rule-based hosted demo only**
  - **AI mode enabled** with `GROQ_API_KEY`

## Files Already In Place

- [render.yaml](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/render.yaml)
- [Procfile](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/Procfile)
- [server.py](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/server.py)
- [.env.example](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/.env.example)
- [scripts/check_zoom_live.py](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/scripts/check_zoom_live.py)

## Render Setup

1. Push the project to GitHub if needed.
2. In Render, click **New +** -> **Web Service**.
3. Connect the repo.
4. Set the service root to the `projects/ist505` folder if the repo contains more than this app.
5. Confirm:
   - Runtime: `Python`
   - Build command: leave blank
   - Start command:
     `python3 server.py --host 0.0.0.0 --port $PORT`
6. Confirm the health check path is:
   `/api/health`

## Environment Variables

### Required for AI mode

- `GROQ_API_KEY`

### Optional

- `ZOOM_WEBHOOK_SECRET`
- `SESSION_MAX_AGE_SEC`

Recommended default for demo hosting:

- `SESSION_MAX_AGE_SEC=7200`

## Zoom Webhook Setup

After the Render service is live:

1. Copy the hosted base URL.
2. In Zoom Marketplace, set the webhook endpoint to:
   `https://your-service.onrender.com/api/zoom/webhook`
3. Subscribe to these events:
   - `meeting.started`
   - `meeting.ended`
   - `meeting.participant_joined`
   - `meeting.participant_left`
   - `meeting.chat_message_sent`
   - `meeting.participant_raised_hand`
   - `meeting.participant_lowered_hand`
   - `meeting.reaction_received`
4. Copy the Zoom secret token into Render as `ZOOM_WEBHOOK_SECRET`.
5. Re-deploy if Render does not hot-apply the env var immediately.

### Important Chat Caveat

If participant join/leave events arrive but in-meeting chat never appears in the live trace, that is not always a code problem.

Zoom may require additional account-level support or in-meeting chat DLP enablement for chat webhook delivery.

## What To Test After Deploy

1. Open the root URL.
2. Confirm the dashboard loads.
3. Run one simulation.
4. Open `/api/health` and confirm it returns JSON.
5. Open `/api/zoom/debug` and confirm the service reports whether the webhook secret is configured.
6. Run:
   `python3 scripts/check_zoom_live.py https://your-service.onrender.com`
7. Send a synthetic rich live sequence:
   `python3 scripts/send_zoom_fixture.py https://your-service.onrender.com --secret "$ZOOM_WEBHOOK_SECRET"`
8. Open the URL in a second browser or incognito window and run another simulation.
9. Confirm the two browsers do not overwrite each other’s runs.

## What “Working” Looks Like

- `/api/health` returns service metadata
- `/api/zoom/debug` returns live signal status information
- A signed synthetic webhook sequence reaches `/api/zoom/webhook` and produces live state/debug output
- The dashboard loads without local server dependency
- A session can be started from the hosted UI
- Separate browsers can run separate simulations
- Zoom webhook validation succeeds against the hosted `/api/zoom/webhook`
- A fresh Zoom meeting can move live mode out of “waiting” or “presence only” once richer signals arrive

## Caveat

Sessions are independent but still stored in memory. If the hosted service restarts, sessions will be lost. That is acceptable for a meeting/demo deployment and Phase 3 proof of concept.

## Recommendation

For tonight or the next 24 hours:

- Deploy on Render
- Enable AI mode only if you want the hosted demo to show LLM behavior
- Use the hosted URL as the primary demo webhook target instead of a temporary localhost tunnel
- Share one hosted URL with the team
