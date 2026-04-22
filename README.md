# Instructional Decision Support Prototype

**Evaluated through SAGE (Simulated Agent-Generated Engagement)**

IST 505 – Design Research Methods (DSR)
Dr. Samir Chatterjee
Claremont Graduate University — Spring 2026

**Group:** Ahmed Alhussain, Evren Arat, Hamad Almarry, Olga Serebryannaya, Samantha Aguirre

---

## What This Is

This project centers a working instructional decision-support prototype for synchronous online teaching. **SAGE** (Simulated Agent-Generated Engagement) is the classroom simulation and evaluation environment used to generate classroom states, route them through the dashboard, and record instructor-response behavior during formative evaluation.

### Current Project Framing

- **Class artifact:** an instructional decision support system for synchronous online teaching
- **Simulation and evaluation environment:** SAGE
- **Deployment-oriented live path:** Zoom/webhook ingestion (current implementation still prototype-level)

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Student Agent Profiles | `simulator/profiles.py` | 15 student agents with demographic, behavioral, and response profiles |
| Simulator Engine | `simulator/engine.py` | Runs N-minute class sessions, generates timestamped observable-participation streams |
| Participation Scoring | `simulator/scoring.py` | Weighted observable-participation index, state classification (Endsley SA Levels 2-3) |
| NLP Analyzer | `simulator/nlp.py` | Confusion detection, sentiment, participation patterns from chat |
| Instructor Dashboard | `dashboard/index.html` | Real-time heatmap, timeline, recommendations, response taxonomy |
| Simulated Professor | `simulator/professor.py` | AI professor agent that responds to dashboard recommendations |

### Theoretical Grounding

- **Endsley (1995):** SA Levels 1-3 map to signal collection → pattern interpretation → advisory recommendations
- **Sweller (1988):** Dashboard reduces extraneous cognitive load on instructor
- **Van Leeuwen et al. (2019):** Advising mode > mirroring mode under time pressure
- **Wise & Jung (2019):** Instructional decision-making is situated rather than one-size-fits-all

### Instructor Response Taxonomy (Construct Artifact)

| Category | Description |
|----------|-------------|
| **Ignore** | No action taken |
| **Acknowledge** | Awareness without behavior change |
| **Accept** | Adopt recommendation as given |
| **Modify** | Adapt recommendation using pedagogical judgment |
| **Reject** | Override with contextual rationale |

---

## Quick Start

### Requirements
- Python 3.10+
- No external dependencies for core simulator (stdlib only)

### Run a Simulation

```bash
cd projects/ist505
python3 -m simulator.engine --duration 45 --output data/session.json
```

Options:
- `--duration N` — Session length in minutes (default: 45)
- `--output PATH` — Output file (default: stdout)
- `--scenario NAME` — Predefined scenario: `baseline`, `energy_decay`, `equity_imbalance`, `confusion_cluster` (default: baseline)
- `--seed N` — Random seed for reproducibility
- `--intervention MIN:TYPE` — Inject intervention at minute MIN (e.g., `20:breakout`, `30:poll`)

### View Dashboard

```bash
# Server-backed dashboard
python3 server.py
# Then open http://localhost:8000

# Optional AI mode
python3 server.py --llm
```

Browser-only mode still works as a fallback:

```bash
open dashboard/index.html
```

Use the server-backed surface for the main dashboard workflow, sessionized runs, and the optional Zoom/webhook extension.

### Recommended Live Demo Path

For classroom demos, prefer a hosted endpoint over a temporary localhost tunnel:

1. Deploy the app with `render.yaml`
2. Configure `ZOOM_WEBHOOK_SECRET` in Render
3. Point the Zoom webhook app at the hosted `/api/zoom/webhook`
4. Use `/api/zoom/debug`, `/api/zoom/state`, and `/api/zoom/history` to verify what Zoom is actually sending

This keeps the real-time Zoom path aligned with the intended deployment context while SAGE remains the primary simulation and evaluation environment.

Current recommendation logic is rule-based and advisory. The system maps detected patterns such as observable participation decline, participation concentration, confusion signals, and low observable activity to candidate instructional moves. LLMs may enrich simulated dialogue, but they do not replace the core recommendation rules. Camera state is treated as non-scoring context rather than a core engagement signal because camera use can reflect bandwidth, privacy, culture, disability, and access constraints.

Note: if in-meeting chat events never arrive even after the webhook is validated and subscribed, Zoom may require account-level in-meeting chat DLP/support enablement in addition to the webhook subscription.

Quick smoke check after deployment:

```bash
python3 scripts/check_zoom_live.py https://your-app.onrender.com
```

Synthetic webhook verification after deployment or on localhost:

```bash
python3 scripts/send_zoom_fixture.py https://your-app.onrender.com --secret "$ZOOM_WEBHOOK_SECRET"
python3 scripts/send_zoom_fixture.py http://localhost:8096 --mode rich
```

This pushes a small signed Zoom-like event sequence through `/api/zoom/webhook` so you can verify the live pipeline before relying on a real meeting.

### Run with Simulated Professor

```bash
python3 -m simulator.professor --duration 45 --style adaptive
```

Professor styles: `adaptive`, `lecture_focused`, `discussion_based`, `hands_off`

---

## File Structure

```
ist505/
├── README.md
├── simulator/
│   ├── __init__.py
│   ├── profiles.py      # 15 student agent definitions
│   ├── engine.py        # Simulation engine (main entry point)
│   ├── scoring.py       # Observable participation scoring model
│   ├── nlp.py           # Chat analysis / confusion detection
│   └── professor.py     # Simulated professor agent
├── dashboard/
│   └── index.html       # Single-file instructor dashboard
├── data/                # Generated session data (gitignored)
└── docs/
    └── scenarios.md     # Scenario descriptions for evaluation
```

---

## For Group Members

This folder is self-contained. You can copy it anywhere and it works. No external dependencies beyond Python 3.10+ standard library.

To modify student profiles, edit `simulator/profiles.py`. Each profile is a dictionary with clearly labeled fields.

To create new scenarios, see `docs/scenarios.md`.
