# IST505 Phase 4 Claude Code Handoff

## Purpose

Use Claude Code as the main implementation surface for the April 23 group-meeting prototype push, with Codex as the adversarial review layer through the installed Claude Code Codex plugin.

The job is not to expand the architecture. The job is to make the current prototype credible, runnable, and easy to demo.

Use one stable hierarchy to avoid naming confusion:

```text
Primary DSR artifact: Instructional Decision Support System (IDSS)
Simulation/formative evaluation environment: SAGE
Prototype-level real-time deployment path: Zoom live monitoring
```

## Current State

- Branch: `codex/ist505-phase4-push-2026-04-20`
- Claude Code is installed: `claude` 2.1.117
- Codex CLI is installed: `codex-cli` 0.122.0
- Claude plugin is installed and enabled: `codex@openai-codex` 1.0.4
- Automatic Codex review gate should stay disabled unless explicitly requested.
- Current local static checks have passed: Python compile, dashboard script parse, and `git diff --check`.

## Start Here In Claude Code

From this project directory:

```bash
cd /Users/evren/throughline-symbolic-os/Developer/evren-pcp/projects/ist505
claude
```

Inside Claude Code:

```text
/reload-plugins
/codex:setup
/codex:setup --disable-review-gate
/project:ist505-phase4-prototype
```

If Claude Code lists the command under a bare `/ist505-phase4-prototype` name instead, use that. If the project slash command is not listed at all, paste the contents of `.claude/commands/ist505-phase4-prototype.md` into Claude Code.

## Build Priorities

- Prototype readiness: server launches, dashboard loads, `Run` works, recommendations appear, manual instructor responses persist, and export still works.
- Professor-feedback alignment: preserve observable participation framing, no camera scoring, rule-based advisory recommendations, and instructor judgment.
- Zoom proof lane: make live mode useful as event-ingestion and monitoring evidence, not as a fully validated analytics claim.
- Meeting surface: protect one short demo path: Instructor Decision Mode, response taxonomy, instructor log/export, Live Zoom Monitoring/debug trace.
- Naming discipline: do not describe SAGE and IDSS as two competing artifacts. IDSS is the artifact; SAGE is how the artifact is simulated, exercised, and formatively evaluated.

## Verification

Run this after meaningful changes:

```bash
bash scripts/verify_phase4_demo.sh
```

If a server is already running, also check live endpoints:

```bash
bash scripts/verify_phase4_demo.sh --url http://localhost:8000
```

For synthetic Zoom verification:

```bash
python3 scripts/send_zoom_fixture.py http://localhost:8000 --mode rich
curl -s http://localhost:8000/api/zoom/state
curl -s http://localhost:8000/api/zoom/history
```

## Codex Review Loop

After Claude makes a meaningful patch:

```text
/codex:adversarial-review --background --scope working-tree challenge whether this is actually demo-ready for tomorrow; focus on misleading engagement claims, Zoom reliability, broken UI flows, export/logging regressions, and anything that could embarrass us in a group meeting
/codex:status
/codex:result
```

Fix only material findings. Run at most two adversarial loops before the meeting unless a real blocker appears.

Before committing:

```text
/codex:review --background --scope working-tree
/codex:status
/codex:result
```

## Commit Rules

- Do not run `git add -A`.
- Stage only the files needed for the prototype checkpoint.
- Suggested commit message: `prototype: stabilize IST505 phase 4 demo path`
- If not committing, leave a concise handoff with server command, demo URL, verification output, Codex review result, and changed files.

## Meeting Story

Use this framing:

```text
SAGE is the formative evaluation environment.
Zoom is the intended real-time deployment path.
The prototype uses observable participation signals to support instructor judgment.
The recommendation engine is rule-based and advisory, not an AI black box.
Camera status is not used as a scored engagement signal.
```
