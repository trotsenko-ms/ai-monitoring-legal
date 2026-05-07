#!/usr/bin/env bash
# Invokes a Claude Code agent in non-interactive mode.
# Usage: bash scripts/run-agent.sh <agent_type> <agent_name>
#   agent_type: monitors | validators | orchestrators
#   agent_name: monitor-edo | validator-state | orchestrator-state | ...
#
# Required env: ANTHROPIC_API_KEY
# Optional env: GMAIL_APP_PASSWORD (for validator agents that send email)

set -euo pipefail

AGENT_TYPE="${1:?agent_type required (monitors|validators|orchestrators)}"
AGENT_NAME="${2:?agent_name required}"

AGENT_DIR="agents/${AGENT_TYPE}/${AGENT_NAME}"
CONFIG_FILE="${AGENT_DIR}/config.json"
PROMPT_FILE="${AGENT_DIR}/prompt.md"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "ERROR: config not found at ${CONFIG_FILE}" >&2
  exit 1
fi
if [[ ! -f "${PROMPT_FILE}" ]]; then
  echo "ERROR: prompt not found at ${PROMPT_FILE}" >&2
  exit 1
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
MODEL=$(python3 -c "import json; c=json.load(open('${CONFIG_FILE}')); print(c['model'])")

# Merge tools from config with Read/Write (always needed for file I/O)
TOOLS=$(python3 -c "
import json
c = json.load(open('${CONFIG_FILE}'))
tools = c.get('tools', []) + ['Read', 'Write']
print(','.join(dict.fromkeys(tools)))
")

SYSTEM_PROMPT=$(cat "${PROMPT_FILE}")

echo "▶ [${AGENT_NAME}] model=${MODEL} tools=${TOOLS} run_id=${TIMESTAMP}"

claude -p "Execute your task. Current run timestamp: ${TIMESTAMP}. Run ID: ${TIMESTAMP}." \
  --system-prompt "${SYSTEM_PROMPT}" \
  --model "${MODEL}" \
  --allowedTools "${TOOLS}"

echo "✓ [${AGENT_NAME}] completed"
