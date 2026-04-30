#!/usr/bin/env python3
"""
Capture reproducible dashboard screenshots for the Phase 4 paper.

Drives a running SAGE server through scripted scenarios and saves PNGs at
known checkpoints (start, mid-session, after-recommendation, after-response,
end-of-run). Output goes to docs/figures/ by default; the paper's Artifact
Description section can reference these directly without the figures
drifting between runs.

Requires: a running server (default http://localhost:8080) and Playwright
(install via `requirements-dev.txt`, then `python3 -m playwright install
chromium`). If Playwright is not available, prints the install command and
exits 0 — the script is best-effort, not a hard build dependency.

Usage:
    python3 scripts/capture_dashboard.py
    python3 scripts/capture_dashboard.py --base-url http://localhost:8080
    python3 scripts/capture_dashboard.py --output-dir docs/figures
    python3 scripts/capture_dashboard.py --scenario full_scenario --university gatech --seed 42

Each capture saves a PNG plus a .meta.json sidecar with scenario / preset /
seed / minute / git SHA, so figures in the paper can be regenerated exactly.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "docs" / "figures"


def _git_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def _try_import_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _print_install_hint():
    print(
        "Playwright is not installed. To enable screenshot capture:\n"
        "    python3 -m venv .venv && source .venv/bin/activate\n"
        "    pip install -r requirements-dev.txt\n"
        "    python3 -m playwright install chromium\n"
        "\n"
        "Then re-run with the SAGE server up:\n"
        "    python3 scripts/capture_dashboard.py --output-dir docs/figures\n"
        "\n"
        "This script is optional — Phase 4 paper figures can also be captured "
        "manually. Skipping cleanly.",
        file=sys.stderr,
    )


def capture(base_url, output_dir, scenario, university, seed, duration, viewport):
    from playwright.sync_api import sync_playwright

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    sha = _git_sha()
    meta_common = {
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": sha,
        "base_url": base_url,
        "scenario": scenario,
        "university": university,
        "seed": seed,
        "duration": duration,
        "viewport": {"width": viewport[0], "height": viewport[1]},
    }

    def save(name, page, extra_meta):
        png_path = output_dir / f"{name}.png"
        meta_path = output_dir / f"{name}.meta.json"
        page.screenshot(path=str(png_path), full_page=True)
        meta = dict(meta_common)
        meta["name"] = name
        meta.update(extra_meta or {})
        meta_path.write_text(json.dumps(meta, indent=2))
        try:
            display_path = png_path.relative_to(ROOT)
        except ValueError:
            display_path = png_path
        print(f"saved {display_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        page = context.new_page()

        # Initial dashboard load
        page.goto(f"{base_url}/?source=capture", wait_until="networkidle")
        page.wait_for_selector("#overview-panel", timeout=10000)
        save("00_dashboard_initial", page, {"checkpoint": "before_run"})

        # Configure scenario controls
        page.select_option("#scenario-select", scenario)
        page.select_option("#university-select", university)
        page.fill("#seed-input", str(seed))
        # Manual instructor mode so the 5-way taxonomy is visible
        try:
            page.select_option("#professor-select", "none")
        except Exception:
            pass

        # Click Run
        page.click("#run-btn")
        # Wait for first frames to populate
        page.wait_for_function(
            "document.querySelector('#stat-engagement .value')?.textContent !== '--'",
            timeout=20000,
        )
        time.sleep(2)
        save("01_dashboard_running", page, {"checkpoint": "running_early"})

        # Wait until at least one recommendation is rendered or duration/2 minutes
        try:
            page.wait_for_function(
                "document.querySelectorAll('#rec-list .rec-item').length > 0",
                timeout=duration * 1500,
            )
            save("02_recommendation_visible", page, {"checkpoint": "first_recommendation"})
        except Exception:
            print("note: no recommendation surfaced before timeout — saving snapshot anyway")
            save("02_recommendation_visible", page, {"checkpoint": "no_recommendation_yet"})

        # Switch to classroom view to capture camera caveat + grid
        try:
            page.evaluate("setView('classroom')")
            page.wait_for_selector(".camera-caveat", timeout=5000)
            time.sleep(1)
            save("03_classroom_view", page, {"checkpoint": "classroom_view"})
            # Switch back to dashboard for the metrics-panel screenshot
            page.evaluate("setView('dashboard')")
            page.wait_for_selector("#overview-panel", timeout=5000)
            time.sleep(1)
        except Exception as e:
            print(f"note: view-switch failed: {e}")

        # Expand metrics panel for live perf metrics screenshot
        try:
            page.evaluate(
                "() => { const d = document.getElementById('metrics-disclosure'); if (d) d.open = true; }"
            )
            time.sleep(1)
            save("04_metrics_panel", page, {"checkpoint": "metrics_panel_open"})
        except Exception:
            pass

        # Wait for run to complete or a fixed window
        target_minute = max(8, duration // 3)
        try:
            page.wait_for_function(
                f"() => {{ const v = document.getElementById('zoom-minute')?.textContent || ''; const m = /Min: (\\d+)/.exec(v); return m && parseInt(m[1]) >= {target_minute}; }}",
                timeout=duration * 2000,
            )
        except Exception:
            time.sleep(target_minute * 0.5)
        save("05_dashboard_mid_run", page, {"checkpoint": f"minute_{target_minute}"})

        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--scenario", default="full_scenario")
    parser.add_argument("--university", default="cgu")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=int, default=20,
                        help="Minutes to allow the sim to run before final capture")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args()

    if not _try_import_playwright():
        _print_install_hint()
        return 0

    capture(
        base_url=args.base_url,
        output_dir=Path(args.output_dir),
        scenario=args.scenario,
        university=args.university,
        seed=args.seed,
        duration=args.duration,
        viewport=(args.width, args.height),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
