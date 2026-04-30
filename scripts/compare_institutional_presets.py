#!/usr/bin/env python3
"""
Compare institutional presets — empirical evidence for the institutional
context sensitivity claim (packet novelty #1, 2026-03-28).

Generates 15 student profiles for each university preset, computes mean
behavioral parameters that flow into the five-signal observable participation
composite, and prints a side-by-side markdown table.

Run before a demo or as a quick regression check: if the deltas collapse,
the institutional differentiation claim has drifted.

Usage:
    python3 scripts/compare_institutional_presets.py
    python3 scripts/compare_institutional_presets.py --seed 7
    python3 scripts/compare_institutional_presets.py --simulate --duration 20

The --simulate flag also runs a short scripted simulation under each preset
and reports end-of-session class observable participation and speaking Gini.
This is slower but gives a stronger empirical signal than parameter means alone.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

# Repo root on sys.path so simulator imports work from any CWD
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulator.university_presets import (  # noqa: E402
    INSTITUTIONAL_MODIFIERS,
    generate_preset_profiles,
    list_presets,
)


def parameter_summary(uni_key: str, seed: int) -> dict:
    profiles = generate_preset_profiles(uni_key, seed=seed)
    return {
        "drift_rate": statistics.mean(p["drift_rate"] for p in profiles),
        "attention_min": statistics.mean(p["attention_span_minutes"] for p in profiles),
        "speak_tendency": statistics.mean(p["speak_tendency"] for p in profiles),
        "chat_frequency": statistics.mean(p["chat_frequency"] for p in profiles),
        "breakout_response": statistics.mean(p["breakout_response"] for p in profiles),
        "description": INSTITUTIONAL_MODIFIERS[uni_key]["description"],
    }


def percent_delta(value: float, baseline: float) -> str:
    if baseline == 0:
        return "n/a"
    delta = (value - baseline) / baseline * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.1f}%"


def print_parameter_table(seed: int) -> None:
    presets = list_presets()
    summaries = {k: parameter_summary(k, seed) for k in presets}
    baseline = summaries["cgu"]

    print(f"# Institutional Preset Comparison (seed={seed})\n")
    print("Behavioral parameters fed into the five-signal observable-participation composite.")
    print("CGU is the baseline; deltas show how each preset diverges from it.\n")

    print("| Preset | Drift rate | Attention (min) | Speak tendency | Chat frequency | Breakout response |")
    print("|---|---|---|---|---|---|")
    for k in presets:
        s = summaries[k]
        if k == "cgu":
            drift = f"{s['drift_rate']:.4f}"
            attn = f"{s['attention_min']:.1f}"
            speak = f"{s['speak_tendency']:.3f}"
            chat = f"{s['chat_frequency']:.3f}"
            breakout = f"{s['breakout_response']:.3f}"
        else:
            drift = f"{s['drift_rate']:.4f} ({percent_delta(s['drift_rate'], baseline['drift_rate'])})"
            attn = f"{s['attention_min']:.1f} ({percent_delta(s['attention_min'], baseline['attention_min'])})"
            speak = f"{s['speak_tendency']:.3f} ({percent_delta(s['speak_tendency'], baseline['speak_tendency'])})"
            chat = f"{s['chat_frequency']:.3f} ({percent_delta(s['chat_frequency'], baseline['chat_frequency'])})"
            breakout = f"{s['breakout_response']:.3f} ({percent_delta(s['breakout_response'], baseline['breakout_response'])})"
        print(f"| **{k}** | {drift} | {attn} | {speak} | {chat} | {breakout} |")

    print("\n## Preset descriptions\n")
    for k in presets:
        print(f"- **{k}**: {summaries[k]['description']}")


def simulate_summary(uni_key: str, duration: int, seed: int) -> dict:
    """Run a short scripted simulation under the preset. Returns end-of-session metrics."""
    from simulator.engine import SimulationEngine

    sim = SimulationEngine(
        duration=duration,
        seed=seed,
        scenario="baseline",
        university=uni_key,
        use_llm=False,
    )
    final = None
    for frame in sim.step():
        final = frame

    if final is None:
        return {"class_engagement": 0.0, "speaking_gini": 0.0, "patterns": [], "active_speakers": 0}

    return {
        "class_engagement": final.get("class_engagement", 0.0),
        "speaking_gini": final.get("speaking_gini", 0.0),
        "patterns": [p.get("type", "") for p in final.get("patterns", [])],
        "active_speakers": final.get("active_speakers", 0),
    }


def print_simulation_table(duration: int, seed: int) -> None:
    presets = list_presets()
    print(f"\n## Simulation outcomes (duration={duration} min, seed={seed})\n")
    print("Same scenario (baseline) under each preset. Differences in end-of-session")
    print("class observable participation and speaking Gini reflect the institutional")
    print("differentiation flowing through the scoring pipeline.\n")

    print("| Preset | End participation | Speaking Gini | Active speakers | Patterns at end |")
    print("|---|---|---|---|---|")
    for k in presets:
        s = simulate_summary(k, duration, seed)
        patterns = ", ".join(s["patterns"]) or "—"
        print(f"| **{k}** | {s['class_engagement']:.2f} | {s['speaking_gini']:.2f} | {s['active_speakers']} | {patterns} |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    parser.add_argument("--simulate", action="store_true",
                        help="Also run a short scripted simulation per preset")
    parser.add_argument("--duration", type=int, default=20,
                        help="Simulation duration in minutes when --simulate (default: 20)")
    args = parser.parse_args()

    print_parameter_table(args.seed)
    if args.simulate:
        print_simulation_table(args.duration, args.seed)


if __name__ == "__main__":
    main()
