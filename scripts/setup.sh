#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_SCRIPTS_DIR="$(cd "$SCRIPT_DIR/../test-scripts" && pwd)"
cd "$TEST_SCRIPTS_DIR"

echo "== NetTest environment provisioning =="
echo "python: $(python --version 2>&1)"
mkdir -p results

check_tcp_line() {
    local host="$1" port="$2" send="$3" timeout_s="$4"
    local reply=""
    if exec 9<>"/dev/tcp/${host}/${port}" 2>/dev/null; then
        printf '%s' "$send" >&9
        IFS= read -r -t "$timeout_s" reply <&9 || true
        exec 9<&- 9>&-
    fi
    printf '%s' "$reply"
}

wait_for_port() {
    local host="$1" port="$2" attempts="$3"
    for _ in $(seq 1 "$attempts"); do
        if exec 9<>"/dev/tcp/${host}/${port}" 2>/dev/null; then
            exec 9<&- 9>&-
            return 0
        fi
        sleep 0.25
    done
    return 1
}

echo "-- smoke-checking Flask API service can bind and respond --"
python -m app.server &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT

if ! wait_for_port 127.0.0.1 5000 20; then
    echo "API did not bind to port 5000 in time" >&2
    exit 1
fi
STATUS_LINE=$(check_tcp_line 127.0.0.1 5000 $'GET /devices HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n' 3)
kill "$API_PID" 2>/dev/null || true
wait "$API_PID" 2>/dev/null || true
trap - EXIT

if [[ "$STATUS_LINE" != *"200"* ]]; then
    echo "API smoke check failed, got: $STATUS_LINE" >&2
    exit 1
fi
echo "API responded: $STATUS_LINE"

echo "-- smoke-checking SCPI mock instrument can bind and respond --"
python -m scpi_sim.server &
SCPI_PID=$!
trap 'kill "$SCPI_PID" 2>/dev/null || true' EXIT

if ! wait_for_port 127.0.0.1 5025 20; then
    echo "SCPI mock instrument did not bind to port 5025 in time" >&2
    exit 1
fi
IDN=$(check_tcp_line 127.0.0.1 5025 $'*IDN?\n' 3)
kill "$SCPI_PID" 2>/dev/null || true
wait "$SCPI_PID" 2>/dev/null || true
trap - EXIT

if [[ -z "$IDN" ]]; then
    echo "SCPI mock instrument did not respond to *IDN?" >&2
    exit 1
fi
echo "SCPI mock responded: $IDN"

echo "== environment provisioning complete, ready for test execution =="
