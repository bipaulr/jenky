#!/usr/bin/env bash
set -euo pipefail

REPO="bipaulr/jenky"
SHA="${GIT_COMMIT:?GIT_COMMIT not set}"

echo "== Change control gate for commit ${SHA} =="

CURRENT_VERSION=$(git show "${SHA}:test-scripts/VERSION.txt")
HAS_PARENT=$(git rev-parse -q --verify "${SHA}^" >/dev/null && echo yes || echo no)

echo "-- checking whether this commit touches test-scripts/ --"
if [[ "$HAS_PARENT" == "yes" ]]; then
    CHANGED_FILES=$(git diff --name-only "${SHA}^" "${SHA}" -- test-scripts/)
else
    CHANGED_FILES=$(git show --name-only --pretty=format: "${SHA}" -- test-scripts/)
fi

if [[ -z "$CHANGED_FILES" ]]; then
    echo "no test-scripts/ changes in this commit, skipping version-bump check"
    TEST_SCRIPTS_CHANGED="no"
else
    TEST_SCRIPTS_CHANGED="yes"
    echo "-- checking test-scripts/VERSION.txt was bumped --"
    if [[ "$HAS_PARENT" == "yes" ]]; then
        PREVIOUS_VERSION=$(git show "${SHA}^:test-scripts/VERSION.txt" 2>/dev/null || echo "")
    else
        PREVIOUS_VERSION=""
    fi

    if [[ "$CURRENT_VERSION" == "$PREVIOUS_VERSION" ]]; then
        echo "REJECTED: test-scripts/ changed but VERSION.txt was not bumped (still ${CURRENT_VERSION})" >&2
        exit 1
    fi
    echo "VERSION.txt bumped: ${PREVIOUS_VERSION:-<none>} -> ${CURRENT_VERSION}"
fi

echo "-- checking commit is associated with a merged pull request (not a direct push) --"
AUTH_HEADER=()
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    AUTH_HEADER=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

PR_RESPONSE=$(curl -sf "${AUTH_HEADER[@]}" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${REPO}/commits/${SHA}/pulls")

PR_COUNT=$(echo "$PR_RESPONSE" | jq 'length')
if [[ "$PR_COUNT" -eq 0 ]]; then
    echo "REJECTED: commit ${SHA} is not associated with any pull request (looks like a direct push)" >&2
    exit 1
fi

PR_NUMBER=$(echo "$PR_RESPONSE" | jq -r '.[0].number')
PR_MERGED=$(echo "$PR_RESPONSE" | jq -r '.[0].merged_at')
if [[ "$PR_MERGED" == "null" ]]; then
    echo "REJECTED: pull request #${PR_NUMBER} for commit ${SHA} has not been merged" >&2
    exit 1
fi
echo "commit went through pull request #${PR_NUMBER}, merged at ${PR_MERGED}"

if [[ "$TEST_SCRIPTS_CHANGED" == "yes" ]]; then
    echo "== change control gate PASSED: promoting test-scripts v${CURRENT_VERSION} =="
else
    echo "== change control gate PASSED: no test-scripts change to promote (pipeline/infra-only commit) =="
fi
