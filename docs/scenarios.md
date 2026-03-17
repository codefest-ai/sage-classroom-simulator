# Evaluation Scenarios

Predefined scenarios for systematic testing of the dashboard and instructor response patterns. Each scenario is repeatable with a fixed seed.

## Baseline
**What it simulates:** Normal class session with natural engagement variation. No artificial events.
**Why it matters:** Establishes control condition for comparison.
**Expected patterns:** Mild energy decay after ~25 minutes, natural speaking equity variation.
```bash
python3 -m simulator.engine --scenario baseline --seed 42
```

## Energy Decay
**What it simulates:** Extended lecture with no interactive activities. Drift rate multiplied 1.5x.
**Why it matters:** Tests whether the dashboard detects gradual disengagement and recommends activity breaks at appropriate thresholds.
**Expected patterns:** Moderate-to-severe energy decay by minute 20, fade cascade by minute 30.
```bash
python3 -m simulator.engine --scenario energy_decay --seed 42
```

## Equity Imbalance
**What it simulates:** Two dominant students (Rachel Torres + Marcus Chen) monopolize discussion while others are suppressed.
**Why it matters:** Tests Gini coefficient detection and equity-focused recommendations.
**Expected patterns:** High Gini (>0.6) by minute 10, equity imbalance alerts.
```bash
python3 -m simulator.engine --scenario equity_imbalance --seed 42
```

## Confusion Cluster
**What it simulates:** Difficult topic introduced at minute 20 triggers widespread confusion for ~8 minutes.
**Why it matters:** Tests NLP confusion detection and clarification recommendations.
**Expected patterns:** 3+ students signaling confusion at minute 20-28, confusion cluster alert.
```bash
python3 -m simulator.engine --scenario confusion_cluster --seed 42
```

## Intervention Test
**What it simulates:** Baseline scenario with breakout rooms at minute 20 and poll at minute 35.
**Why it matters:** Tests whether intervention effects are visible in the data (engagement boost post-intervention).
**Expected patterns:** Engagement dip pre-breakout, boost post-breakout, sustained engagement post-poll.
```bash
python3 -m simulator.engine --scenario intervention_test --seed 42
```

## Full Scenario
**What it simulates:** Combined energy decay (1.3x drift) + confusion spike at minute 18 + breakout at minute 25 + poll at minute 40.
**Why it matters:** Most realistic scenario — tests the full recommendation pipeline under compound conditions.
**Expected patterns:** Energy decay + confusion cluster + intervention boost + recovery pattern.
```bash
python3 -m simulator.engine --scenario full_scenario --seed 42
```

---

## Creating Custom Scenarios

Edit `SCENARIOS` in `simulator/engine.py` or use CLI flags:

```bash
# Custom: 60-minute session with interventions at minutes 15 and 30
python3 -m simulator.engine --duration 60 --intervention 15:breakout --intervention 30:poll --seed 123

# Closed-loop with simulated professor
python3 -m simulator.professor --scenario full_scenario --style adaptive --seed 42
```

## Student Archetype Reference

| ID | Name | Archetype | Key Trait |
|----|------|-----------|-----------|
| S11 | Alex Kim | The Lurker | Invisible but present — tests false negative detection |
| S12 | Chris O'Brien | The Fader | Starts high, fades fast — tests decay detection |
| S13 | Rachel Torres | The Dominator | Monopolizes discussion — tests equity detection |
| S14 | Sam Rivera | The Confused | Frequent confusion signals — tests NLP detection |
| S15 | Jordan Lee | The Ideal | Balanced engagement — control profile |
