#!/usr/bin/env bash
set -euo pipefail

# Runs against /suite - the copy of test-scripts/ baked into the Docker
# image at build time (Dockerfile.test-runner's `COPY test-scripts/ .`),
# not the live Jenkins workspace. testImage.inside() only overlays the
# workspace's own path, so /suite stays the pristine as-committed snapshot
# even while running inside that same container.

if [[ -f /suite/SIMULATE_SMOKE_FAILURE ]]; then
    echo "SMOKE CHECK FAILED: /suite/SIMULATE_SMOKE_FAILURE marker present" >&2
    echo "(deliberate demo trigger for Phase 6 rollback - not a real defect)" >&2
    exit 1
fi

cd /suite
echo "== post-promotion smoke check against the promoted build artifact (/suite) =="
python -m pytest -k "test_idn_returns_identification_string or test_create_device_returns_201" -v
echo "== smoke check PASSED =="
