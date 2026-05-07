#!/usr/bin/env bash
#
# verify_multi_install.sh — synthetic spine check for the IDSS multi-install
# Zoom OAuth flow.
#
# Boots the server with two simulated OAuth installs, fires synthetic webhook
# events for each, and asserts that:
#   1. /api/zoom/connection lists both installs
#   2. /api/zoom/state?install_id=A returns A's meeting only
#   3. /api/zoom/state?install_id=B returns B's meeting only
#   4. an unmatched account_id does not appear in any teacher-scoped state
#   5. POST /api/zoom/response targets the correct install's meeting
#   6. Two installs can hold meetings with the same meeting_id without collision
#
# Exit code 0 on pass; non-zero on first failure with a printed reason.

set -u
PORT="${PORT:-8765}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STORE="/tmp/sage_oauth_test_$$"
PID=""

cleanup() {
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
  fi
  rm -rf "$STORE"
}
trap cleanup EXIT

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

mkdir -p "$STORE"
cat > "$STORE/acct-AAA.json" <<'JSON'
{"access_token":"tokA","scope":"meeting:read","expires_at":9999999999,"installed_at":1700000000,"me":{"id":"u-A","account_id":"acct-AAA","email":"alice@example.edu"}}
JSON
cat > "$STORE/acct-BBB.json" <<'JSON'
{"access_token":"tokB","scope":"meeting:read","expires_at":9999999999,"installed_at":1700000001,"me":{"id":"u-B","account_id":"acct-BBB","email":"bob@example.edu"}}
JSON

cd "$ROOT"

ZOOM_OAUTH_CLIENT_ID=fake-client \
ZOOM_OAUTH_CLIENT_SECRET=fake-secret \
ZOOM_OAUTH_REDIRECT_URL=https://example.com/cb \
ZOOM_OAUTH_STORE_DIR="$STORE" \
PYTHONDONTWRITEBYTECODE=1 \
python3 server.py --host 127.0.0.1 --port "$PORT" >/dev/null 2>&1 &
PID=$!

# Wait for the server to come up.
for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null; then
    break
  fi
  sleep 0.2
done
curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null \
  || fail "server did not start on port ${PORT}"

# 1. /api/zoom/connection lists both installs
COUNT=$(curl -s "http://127.0.0.1:${PORT}/api/zoom/connection" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['install_count'])")
[ "$COUNT" = "2" ] || fail "expected install_count=2, got=$COUNT"

# 2. Send meeting.started + participant_joined for AAA
curl -sf -X POST -H 'Content-Type: application/json' -d '{"event":"meeting.started","payload":{"account_id":"acct-AAA","object":{"id":"mtg-A","topic":"Alice Class"}}}' \
  "http://127.0.0.1:${PORT}/api/zoom/webhook" >/dev/null
curl -sf -X POST -H 'Content-Type: application/json' -d '{"event":"meeting.participant_joined","payload":{"account_id":"acct-AAA","object":{"id":"mtg-A","participant":{"user_id":"a-stu1","user_name":"Alice S1"}}}}' \
  "http://127.0.0.1:${PORT}/api/zoom/webhook" >/dev/null

# 3. Send meeting.started + participant_joined for BBB (deliberately same meeting_id)
curl -sf -X POST -H 'Content-Type: application/json' -d '{"event":"meeting.started","payload":{"account_id":"acct-BBB","object":{"id":"mtg-A","topic":"Bob Class"}}}' \
  "http://127.0.0.1:${PORT}/api/zoom/webhook" >/dev/null
curl -sf -X POST -H 'Content-Type: application/json' -d '{"event":"meeting.participant_joined","payload":{"account_id":"acct-BBB","object":{"id":"mtg-A","participant":{"user_id":"b-stu1","user_name":"Bob S1"}}}}' \
  "http://127.0.0.1:${PORT}/api/zoom/webhook" >/dev/null

# 4. AAA scope sees Alice only
ALICE=$(curl -s "http://127.0.0.1:${PORT}/api/zoom/state?install_id=acct-AAA" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); s=d.get('students') or []; print(','.join(x.get('name','?') for x in s))")
[ "$ALICE" = "Alice S1" ] || fail "AAA scope expected 'Alice S1', got='$ALICE'"

# 5. BBB scope sees Bob only (no collision despite same meeting_id)
BOB=$(curl -s "http://127.0.0.1:${PORT}/api/zoom/state?install_id=acct-BBB" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); s=d.get('students') or []; print(','.join(x.get('name','?') for x in s))")
[ "$BOB" = "Bob S1" ] || fail "BBB scope expected 'Bob S1', got='$BOB'"

# 6. Unmatched account_id (no install) does not appear in any teacher-scoped state
curl -sf -X POST -H 'Content-Type: application/json' -d '{"event":"meeting.started","payload":{"account_id":"acct-UNMATCHED","object":{"id":"mtg-X","topic":"Stranger"}}}' \
  "http://127.0.0.1:${PORT}/api/zoom/webhook" >/dev/null
curl -sf -X POST -H 'Content-Type: application/json' -d '{"event":"meeting.participant_joined","payload":{"account_id":"acct-UNMATCHED","object":{"id":"mtg-X","participant":{"user_id":"x-stu1","user_name":"Stranger S1"}}}}' \
  "http://127.0.0.1:${PORT}/api/zoom/webhook" >/dev/null

ALICE_AGAIN=$(curl -s "http://127.0.0.1:${PORT}/api/zoom/state?install_id=acct-AAA" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); s=d.get('students') or []; print(','.join(x.get('name','?') for x in s))")
[ "$ALICE_AGAIN" = "Alice S1" ] \
  || fail "AAA scope contaminated by unmatched event, got='$ALICE_AGAIN'"

BOB_AGAIN=$(curl -s "http://127.0.0.1:${PORT}/api/zoom/state?install_id=acct-BBB" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); s=d.get('students') or []; print(','.join(x.get('name','?') for x in s))")
[ "$BOB_AGAIN" = "Bob S1" ] \
  || fail "BBB scope contaminated by unmatched event, got='$BOB_AGAIN'"

# 7. POST /api/zoom/response with install_id=acct-AAA targets AAA's meeting only.
RESP=$(curl -s -X POST -H 'Content-Type: application/json' -d '{"install_id":"acct-AAA","minute":1,"response_category":"acknowledge","recommendation_id":"r1","recommendation_message":"test","rationale":"spine check"}' \
  "http://127.0.0.1:${PORT}/api/zoom/response")
RESP_INSTALL=$(echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('install_id') or '')")
[ "$RESP_INSTALL" = "acct-AAA" ] \
  || fail "response did not land on AAA, got='$RESP_INSTALL' resp=$RESP"

# 8. Storage warning surfaces because store is under /tmp.
WARN=$(curl -s "http://127.0.0.1:${PORT}/api/zoom/connection" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(bool(d.get('storage_warning')))")
[ "$WARN" = "True" ] || fail "expected storage_warning under /tmp, got=$WARN"

echo "multi-install-verify-ok"
