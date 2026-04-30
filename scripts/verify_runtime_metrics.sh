#!/usr/bin/env bash
# Runtime regression check for the C1/C3/C4 metrics + export endpoints.
# Boots a local server, runs a short sim, exercises /api/metrics and
# /api/export, and fails on missing keys or structure regression. Separate
# from verify_phase4_demo.sh because it actually starts a server (slower).
#
# Usage:
#   bash scripts/verify_runtime_metrics.sh
#   bash scripts/verify_runtime_metrics.sh --port 8765
#
# Exit 0: all checks pass.
# Exit 1: a regression was detected (output names which check failed).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT=8080
if [[ "${1:-}" == "--port" ]]; then
  PORT="${2:-8080}"
fi
URL="http://localhost:${PORT}"

echo "== runtime metrics regression check (port ${PORT}) =="

# Boot server in background. Use a temp log so failures can be inspected.
LOG="$(mktemp -t sage_verify.XXXXXX.log)"
ENABLE_ZOOM_API_PROBE=1 PORT="${PORT}" python3 server.py >"${LOG}" 2>&1 &
SERVER_PID=$!
trap 'kill ${SERVER_PID} 2>/dev/null; wait 2>/dev/null; rm -f "${LOG}"' EXIT

# Wait for server to come up (up to 10s).
for _ in $(seq 1 20); do
  if curl -sf "${URL}/api/health" >/dev/null 2>&1; then break; fi
  sleep 0.5
done
if ! curl -sf "${URL}/api/health" >/dev/null 2>&1; then
  echo "FAIL: server did not boot within 10s. Tail of server log:" >&2
  tail -20 "${LOG}" >&2
  exit 1
fi

# Start a short sim.
SID="$(curl -s -X POST "${URL}/api/start" \
  -H "Content-Type: application/json" \
  -d '{"scenario":"full_scenario","duration":12,"seed":42,"university":"cgu","speed":0.04,"professor_style":"none"}' \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("session_id",""))')"

if [[ -z "${SID}" ]]; then
  echo "FAIL: /api/start returned no session_id" >&2
  exit 1
fi

# Let the sim run a few ticks.
sleep 5

# Log a response so the taxonomy + behavioral-impact paths get exercised.
curl -s -X POST "${URL}/api/response" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"${SID}\",\"response_category\":\"accept\",\"intervention_type\":\"poll\",\"recommendation_id\":\"verify-r1\",\"minute\":3}" \
  >/dev/null

sleep 4

# /api/metrics structure check.
python3 - "${URL}" "${SID}" <<'PY'
import json, sys, urllib.request

base, sid = sys.argv[1], sys.argv[2]
required = {
    "available", "session_id", "is_running", "tick_count",
    "session_duration_sec",
    "pattern_detection_precision", "pattern_triggers_total",
    "pattern_triggers_emitted", "pattern_triggers_throttled",
    "pattern_counts_by_type", "throttle_counts_by_type",
    "throttle_effectiveness",
    "latency_mean_ms", "latency_p50_ms", "latency_p95_ms",
    "response_taxonomy_distribution", "response_total",
    "taxonomy_adoption_rate", "behavioral_impact",
}
distribution_required = {"ignore", "acknowledge", "accept", "modify", "reject"}
behavioral_required = {"available", "window_minutes", "deltas", "means_by_category"}

with urllib.request.urlopen(f"{base}/api/metrics?session_id={sid}", timeout=5) as r:
    body = json.loads(r.read())

missing = required - set(body.keys())
if missing:
    print(f"FAIL: /api/metrics missing keys: {sorted(missing)}", file=sys.stderr)
    sys.exit(2)

dist = body.get("response_taxonomy_distribution", {})
missing_cats = distribution_required - set(dist.keys())
if missing_cats:
    print(f"FAIL: distribution missing categories: {sorted(missing_cats)}", file=sys.stderr)
    sys.exit(3)

bi = body.get("behavioral_impact", {})
missing_bi = behavioral_required - set(bi.keys())
if missing_bi:
    print(f"FAIL: behavioral_impact missing keys: {sorted(missing_bi)}", file=sys.stderr)
    sys.exit(4)

# Sanity: tick_count > 0, precision = 1.0, response_total >= 1.
if body["tick_count"] <= 0:
    print(f"FAIL: tick_count <= 0 ({body['tick_count']})", file=sys.stderr); sys.exit(5)
if body["pattern_detection_precision"] is not None and body["pattern_detection_precision"] != 1.0:
    print(f"FAIL: precision != 1.0 ({body['pattern_detection_precision']})", file=sys.stderr); sys.exit(6)
if body["response_total"] < 1:
    print(f"FAIL: response_total < 1 (was the response logged?)", file=sys.stderr); sys.exit(7)

print("metrics-structure-ok")
PY

# /api/export?format=json structure check.
python3 - "${URL}" "${SID}" <<'PY'
import json, sys, urllib.request

base, sid = sys.argv[1], sys.argv[2]
required = {
    "export_format_version", "export_generated_at", "session_id",
    "metadata", "students", "timeline", "events",
    "recommendations", "professor_actions", "metrics", "timeline_csv",
}
with urllib.request.urlopen(f"{base}/api/export?session_id={sid}", timeout=5) as r:
    body = json.loads(r.read())
missing = required - set(body.keys())
if missing:
    print(f"FAIL: /api/export missing keys: {sorted(missing)}", file=sys.stderr); sys.exit(8)
if body["export_format_version"] != 1:
    print(f"FAIL: unexpected export_format_version {body['export_format_version']}", file=sys.stderr); sys.exit(9)
if not body["timeline"]:
    print("FAIL: export has empty timeline", file=sys.stderr); sys.exit(10)
print("export-json-structure-ok")
PY

# /api/export?format=csv content-type + header check.
RESP_HEADERS="$(curl -s -D - -o /dev/null "${URL}/api/export?session_id=${SID}&format=csv")"
if ! echo "${RESP_HEADERS}" | grep -qi "content-type: text/csv"; then
  echo "FAIL: csv export did not return text/csv content-type" >&2
  exit 11
fi
CSV_BODY="$(curl -s "${URL}/api/export?session_id=${SID}&format=csv")"
if ! echo "${CSV_BODY}" | head -2 | tail -1 | grep -q "minute,observable_participation,active_speakers,speaking_gini,patterns"; then
  echo "FAIL: csv export header row missing or wrong" >&2
  exit 12
fi
echo "export-csv-structure-ok"

# /api/zoom/probe: enabled only for local/dev by ENABLE_ZOOM_API_PROBE=1.
# With no token, should be 400 with a helpful error.
PROBE_CODE="$(curl -s -o /tmp/probe.json -w '%{http_code}' "${URL}/api/zoom/probe")"
if [[ "${PROBE_CODE}" != "400" ]]; then
  echo "FAIL: /api/zoom/probe with no token expected 400, got ${PROBE_CODE}" >&2
  exit 13
fi
if ! grep -q "ZOOM_API_TOKEN" /tmp/probe.json; then
  echo "FAIL: /api/zoom/probe error did not mention ZOOM_API_TOKEN" >&2
  exit 14
fi
echo "zoom-probe-no-token-ok"

echo "runtime-metrics-verify-ok"
