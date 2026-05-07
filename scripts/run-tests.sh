#!/usr/bin/env bash
# Runs fixture validation for all test cases.
# Usage: bash scripts/run-tests.sh [agent_name]
#   agent_name (optional): run only cases for this agent, e.g. monitor-edo
#
# Exit code: 0 — all passed, 1 — one or more failed

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASES_DIR="${REPO_ROOT}/tests/cases"
RESULTS_DIR="${REPO_ROOT}/tests/results"
VALIDATE="${REPO_ROOT}/scripts/validate-artifact.py"

AGENT_FILTER="${1:-}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
RESULT_FILE="${RESULTS_DIR}/run-${TIMESTAMP}.txt"

passed=0
failed=0

mkdir -p "${RESULTS_DIR}"

lines=()
lines+=("Test run: ${TIMESTAMP}")
lines+=("Agent filter: ${AGENT_FILTER:-all}")
lines+=("================================")

while IFS= read -r -d '' case_file; do
  agent_dir=$(basename "$(dirname "${case_file}")")
  if [[ -n "${AGENT_FILTER}" && "${agent_dir}" != "${AGENT_FILTER}" ]]; then
    continue
  fi

  case_id=$(python3 -c "import json; print(json.load(open('${case_file}'))['case_id'])" 2>/dev/null || echo "${case_file}")
  fixture=$(python3 -c "import json; print(json.load(open('${case_file}'))['fixture'])" 2>/dev/null || echo "")

  if [[ -z "${fixture}" ]]; then
    lines+=("SKIP ${case_id}: no fixture defined")
    continue
  fi

  fixture_path="${REPO_ROOT}/${fixture}"

  if [[ ! -f "${fixture_path}" ]]; then
    lines+=("FAIL ${case_id}: fixture not found: ${fixture}")
    failed=$((failed + 1))
    continue
  fi

  if python3 "${VALIDATE}" "${fixture_path}" > /dev/null 2>&1; then
    lines+=("PASS ${case_id}")
    passed=$((passed + 1))
  else
    lines+=("FAIL ${case_id}: schema validation failed")
    while IFS= read -r err_line; do
      lines+=("     ${err_line}")
    done < <(python3 "${VALIDATE}" "${fixture_path}" 2>&1)
    failed=$((failed + 1))
  fi

done < <(find "${CASES_DIR}" -name "*.json" -print0 | sort -z)

lines+=("================================")
lines+=("Results: ${passed} passed, ${failed} failed")

for line in "${lines[@]}"; do
  echo "${line}"
done | tee "${RESULT_FILE}"

echo ""
echo "Saved to: ${RESULT_FILE}"

[[ ${failed} -eq 0 ]]
