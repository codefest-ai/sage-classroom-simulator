# SAGE — Simulated Agent-Generated Engagement

**An Agent-Based Simulation Framework for Evaluating AI-Augmented Instructional Decision Support in Synchronous Online Learning Environments**

IST 505 – Design Research Methods (DSR)
Dr. Samir Chatterjee
Claremont Graduate University — Spring 2026

**Group:** Ahmed Alhussain, Evren Arat, Hamad Almarry, Olga Serebryannaya, Samantha Aguirre

---

## What This Is

**SAGE** (Simulated Agent-Generated Engagement) is a Stage 1 prototype: an agent-based classroom simulator with 15 AI "students" that generates realistic engagement data, paired with an instructor dashboard that displays engagement patterns and AI-generated recommendations.

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Student Agent Profiles | `simulator/profiles.py` | 15 student agents with demographic, behavioral, and response profiles |
| Simulator Engine | `simulator/engine.py` | Runs N-minute class sessions, generates timestamped engagement streams |
| Engagement Scoring | `simulator/scoring.py` | Weighted engagement index, state classification (Endsley SA Levels 2-3) |
| NLP Analyzer | `simulator/nlp.py` | Confusion detection, sentiment, participation patterns from chat |
| Instructor Dashboard | `dashboard/index.html` | Real-time heatmap, timeline, recommendations, response taxonomy |
| Simulated Professor | `simulator/professor.py` | AI professor agent that responds to dashboard recommendations |

### Theoretical Grounding

- **Endsley (1995):** SA Levels 1-3 map to signal collection → engagement scoring → recommendations
- **Sweller (1988):** Dashboard reduces extraneous cognitive load on instructor
- **Van Leeuwen et al. (2019):** Advising mode > mirroring mode under time pressure
- **Li et al. (2025):** Instructor heterogeneity → suggestions not directives

### Instructor Response Taxonomy (Construct Artifact)

| Category | Description |
|----------|-------------|
| **Ignore** | No action taken |
| **Acknowledge** | Awareness without behavior change |
| **Accept & Adjust** | Adopt recommendation as given |
| **Modify & Adjust** | Adapt recommendation using pedagogical judgment |
| **Reject with Reason** | Override with contextual rationale |

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
# Option 1: Just open the HTML file
open dashboard/index.html

# Option 2: Serve locally (for fetch API support)
python3 -m http.server 8080 --directory .
# Then open http://localhost:8080/dashboard/
```

Load a session file into the dashboard, or run live simulation from the dashboard UI.

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
│   ├── scoring.py       # Engagement scoring model
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
