#!/usr/bin/env bash
set -euo pipefail

REPO="bipaulr/jenky"
DB_PATH="test-scripts/results/test_results.db"
CURRENT_BUILD="${BUILD_NUMBER:?BUILD_NUMBER not set}"
CURRENT_SHA="${GIT_COMMIT:?GIT_COMMIT not set}"
TOKEN="${GITHUB_TOKEN_WRITE:?GITHUB_TOKEN_WRITE not set}"

echo "== Rollback: looking for last known-good version before build #${CURRENT_BUILD} =="

GOOD_ROW=$(sqlite3 -separator '|' "$DB_PATH" \
    "SELECT build_number, git_commit_sha, script_version FROM audit_log
     WHERE gate_outcome='promoted' AND test_outcome='passed' AND smoke_outcome='passed'
       AND build_number != ${CURRENT_BUILD}
     ORDER BY build_number DESC LIMIT 1;")

if [[ -z "$GOOD_ROW" ]]; then
    echo "REJECTED: no prior known-good build found in audit_log - nothing to roll back to" >&2
    exit 1
fi

GOOD_BUILD=$(echo "$GOOD_ROW" | cut -d'|' -f1)
GOOD_SHA=$(echo "$GOOD_ROW" | cut -d'|' -f2)
GOOD_VERSION=$(echo "$GOOD_ROW" | cut -d'|' -f3)

echo "last known-good: build #${GOOD_BUILD}, commit ${GOOD_SHA}, version ${GOOD_VERSION}"

BRANCH="rollback/build-${CURRENT_BUILD}"

git config user.email "jenky-pipeline@localhost"
git config user.name "jenky-pipeline"

git fetch origin main
git checkout -B "$BRANCH" "origin/main"
git checkout "${GOOD_SHA}" -- test-scripts

if git diff --cached --quiet; then
    echo "REJECTED: test-scripts is already identical to the last known-good version, nothing to revert" >&2
    exit 1
fi

git commit -m "Rollback test-scripts to v${GOOD_VERSION} (build #${CURRENT_BUILD} failed post-promotion smoke check)"
git push "https://x-access-token:${TOKEN}@github.com/${REPO}.git" "${BRANCH}:${BRANCH}"

PR_PAYLOAD=$(jq -n \
    --arg title "Rollback test-scripts to v${GOOD_VERSION}" \
    --arg body "Automated rollback: build #${CURRENT_BUILD} (commit ${CURRENT_SHA}) failed its post-promotion smoke check. Reverting test-scripts/ to the last known-good state from build #${GOOD_BUILD} (commit ${GOOD_SHA}, v${GOOD_VERSION})." \
    --arg head "$BRANCH" \
    --arg base "main" \
    '{title: $title, body: $body, head: $head, base: $base}')

PR_RESPONSE=$(curl -sf -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${REPO}/pulls" \
    -d "$PR_PAYLOAD")

PR_NUMBER=$(echo "$PR_RESPONSE" | jq -r '.number')
echo "opened rollback PR #${PR_NUMBER}"

MERGE_RESPONSE=$(curl -s -X PUT \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${REPO}/pulls/${PR_NUMBER}/merge" \
    -d '{"merge_method":"merge"}')

MERGED=$(echo "$MERGE_RESPONSE" | jq -r '.merged // false')
if [[ "$MERGED" != "true" ]]; then
    echo "REJECTED: failed to merge rollback PR #${PR_NUMBER}: $(echo "$MERGE_RESPONSE" | jq -r '.message // "unknown error"')" >&2
    exit 1
fi

echo "== rollback complete: PR #${PR_NUMBER} merged, reverted to v${GOOD_VERSION} =="
