#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

URL=""
if [[ "${1:-}" == "--url" ]]; then
  URL="${2:-}"
fi

echo "== IST505 Phase 4 static verification =="

python3 -m py_compile \
  server.py \
  simulator/engine.py \
  simulator/llm_client.py \
  simulator/professor.py \
  simulator/professor_agent.py \
  simulator/zoom_adapter.py \
  simulator/scoring.py \
  scripts/send_zoom_fixture.py \
  scripts/check_zoom_live.py

node -e "const fs=require('fs');const html=fs.readFileSync('dashboard/index.html','utf8');const scripts=[...html.matchAll(/<script[^>]*>([\\s\\S]*?)<\\/script>/gi)].map(m=>m[1]).join('\\n');new Function(scripts);console.log('dashboard-script-ok');"

git diff --check

FRAMING_PATTERN="engagement score|engagement scores|AI-generated recommendations|camera_status|directly measures engagement|measure engagement directly"

set +e
if command -v rg >/dev/null 2>&1; then
  rg -n --glob '!**/__pycache__/**' --glob '!**/*.pyc' "$FRAMING_PATTERN" README.md dashboard/index.html simulator
else
  grep -RnE --exclude-dir=__pycache__ --exclude='*.pyc' "$FRAMING_PATTERN" README.md dashboard/index.html simulator
fi
FRAMING_RC=$?
set -e
if [[ $FRAMING_RC -eq 0 ]]; then
  echo "Framing scan found potentially unsafe wording. Review the matches above." >&2
  exit 1
elif [[ $FRAMING_RC -eq 1 ]]; then
  echo "framing-scan-ok"
else
  echo "Framing scan tool error (exit $FRAMING_RC)." >&2
  exit 1
fi

if [[ -n "$URL" ]]; then
  echo "== IST505 Phase 4 live endpoint verification: $URL =="
  curl -fsS "$URL/api/health" >/dev/null
  curl -fsS "$URL/api/zoom/state" >/dev/null
  curl -fsS "$URL/api/zoom/history" >/dev/null
  echo "live-endpoints-ok"
fi

echo "phase4-demo-verify-ok"
