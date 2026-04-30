# Deployment Options
## How To Share The Current Prototype Without Running It Locally

## Short Answer

Yes. This build can be deployed so other people can open a URL and use it without your laptop running.

The simplest path is to deploy the existing server-based app to **Render** or **Railway**.

## Best Option For Tonight

### Use Render or Railway

This project is a better fit for a long-running Python web service than for a serverless platform.

Why:

- The dashboard depends on a persistent backend process
- The backend keeps simulation state in memory
- Simulations run over time rather than as instant request-response calls
- Live and LLM modes are easier to support on a conventional web service

## Why Vercel Is Not Ideal

The current architecture is not a great fit for Vercel-style serverless deployment.

Main reasons:

- The backend is a stateful Python process
- Session state is stored in memory, not in a database
- Simulations are long-running
- Webhook and live-mode flows are easier in a persistent service model

Vercel is still useful for static front-end demos, but not the best home for the full current build.

## What Already Exists

- [render.yaml](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/render.yaml)
- [Procfile](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/Procfile)
- [server.py](/Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505/server.py)

This means the app is already close to deployable as a standard hosted service.

## What To Configure

### Minimum

- Deploy the `projects/ist505` folder as a Python web service
- Start command:
  `python3 server.py --host 0.0.0.0 --port $PORT`

### For AI mode

- Set `GROQ_API_KEY` in the host environment

### For Zoom webhook mode

- Set `ZOOM_WEBHOOK_SECRET`
- Point Zoom webhooks to the hosted `/api/zoom/webhook` endpoint

## Current Limitation State

The current server now supports **per-session in-memory state** rather than one single global simulation state.

That means:

- Multiple people can open the same hosted URL
- Each browser session can run its own simulation independently
- Session state is still in memory, so it is good for demos and team use but not yet designed for durable long-term storage

## Honest Framing

### What is already solved

- Hosted demo access without your machine running
- Shared team access via one deployed URL
- Independent concurrent per-browser sessions
- AI mode if API key is configured

### What is not fully solved yet

- Durable multi-user storage
- Session recovery after server restart
- Production-grade retention and cleanup policies

## If We Want More Durable Independent Use

The next architectural step would be:

1. Replace in-memory session storage with a persistent backing store
2. Add stronger cleanup and expiration controls
3. Add recovery or restoration behavior across server restarts

That is the next step beyond the current hosted independent-session demo architecture.

## Recommendation

For the group meeting and near-term sharing:

- Deploy one hosted demo on Render or Railway
- Use that as the shared live artifact
- Treat persistence and production hardening as the next-step improvement rather than a blocker for Phase 3
