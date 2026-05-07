#!/usr/bin/env python3
"""
Validates a monitor/validator artifact JSON file against the appropriate schema.

Usage:
    python3 scripts/validate-artifact.py <artifact.json> [schema.json]

If schema is omitted, it's inferred from the artifact's agent_id field.

Exit codes:
    0 — valid
    1 — validation error
    2 — file not found or JSON parse error
"""

import json
import sys
import os
import re
from pathlib import Path

SCHEMA_MAP = {
    "monitor-edo":        "shared/schemas/monitor-artifact.schema.json",
    "monitor-rada-bills": "shared/schemas/monitor-artifact.schema.json",
    "monitor-kmu":        "shared/schemas/monitor-artifact.schema.json",
    "monitor-nbu":        "shared/schemas/monitor-artifact.schema.json",
    "validator-edo":      "shared/schemas/validated-artifact.schema.json",
    "validator-state":    "shared/schemas/validated-artifact.schema.json",
    "orchestrator-state": "shared/schemas/consolidated-artifact.schema.json",
}

REPO_ROOT = Path(__file__).parent.parent


def load_json(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse error in {path}: {e}", file=sys.stderr)
        sys.exit(2)


def validate_monitor_artifact(data: dict, schema: dict, artifact_path: str) -> list[str]:
    """Structural validation without jsonschema dependency."""
    errors = []

    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    if "agent_id" in data:
        allowed_ids = schema["properties"]["agent_id"].get("enum", [])
        if allowed_ids and data["agent_id"] not in allowed_ids:
            errors.append(f"Invalid agent_id '{data['agent_id']}', expected one of: {allowed_ids}")

    if "agent_version" in data:
        if not re.match(r"^\d+\.\d+$", str(data["agent_version"])):
            errors.append(f"agent_version '{data['agent_version']}' doesn't match \\d+\\.\\d+")

    if "run_id" in data:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$", str(data["run_id"])):
            errors.append(f"run_id '{data['run_id']}' must be YYYY-MM-DDTHH-MM-SSZ")

    if "period" in data:
        period = data["period"]
        if not isinstance(period, dict):
            errors.append("'period' must be an object")
        else:
            for key in ("from", "to"):
                if key not in period:
                    errors.append(f"'period.{key}' is required")

    if "items" in data:
        if not isinstance(data["items"], list):
            errors.append("'items' must be an array")
        else:
            for i, item in enumerate(data["items"]):
                for req in ("title", "url", "raw_status"):
                    if req not in item:
                        errors.append(f"items[{i}] missing required field '{req}'")
                if "raw_status" in item and item["raw_status"] != "found":
                    errors.append(f"items[{i}].raw_status must be 'found', got '{item['raw_status']}'")
                if "url" in item and not item["url"].startswith("http"):
                    errors.append(f"items[{i}].url doesn't look like a URI: {item['url']}")

    if "stats" in data:
        stats = data["stats"]
        if not isinstance(stats, dict):
            errors.append("'stats' must be an object")
        else:
            for key in ("items_found", "duplicates_filtered", "errors"):
                if key not in stats:
                    errors.append(f"'stats.{key}' is required")
            if "items_found" in stats and "items" in data:
                if stats["items_found"] != len(data["items"]):
                    errors.append(
                        f"stats.items_found={stats['items_found']} "
                        f"doesn't match len(items)={len(data['items'])}"
                    )

    return errors


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <artifact.json> [schema.json]", file=sys.stderr)
        sys.exit(2)

    artifact_path = Path(sys.argv[1])
    if not artifact_path.is_absolute():
        artifact_path = REPO_ROOT / artifact_path

    data = load_json(artifact_path)

    if len(sys.argv) >= 3:
        schema_path = Path(sys.argv[2])
    else:
        agent_id = data.get("agent_id", "")
        if agent_id not in SCHEMA_MAP:
            print(f"ERROR: unknown agent_id '{agent_id}', cannot infer schema. Pass schema path explicitly.", file=sys.stderr)
            sys.exit(2)
        schema_path = REPO_ROOT / SCHEMA_MAP[agent_id]

    if not schema_path.is_absolute():
        schema_path = REPO_ROOT / schema_path

    schema = load_json(schema_path)

    errors = validate_monitor_artifact(data, schema, str(artifact_path))

    if errors:
        print(f"INVALID: {artifact_path.name}")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        agent_id = data.get("agent_id", "?")
        run_id   = data.get("run_id", "?")
        n_items  = len(data.get("items", []))
        n_dup    = data.get("stats", {}).get("duplicates_filtered", "?")
        n_err    = len(data.get("stats", {}).get("errors", []))
        print(f"OK: {artifact_path.name}")
        print(f"    agent_id={agent_id}  run_id={run_id}")
        print(f"    items={n_items}  duplicates_filtered={n_dup}  errors={n_err}")


if __name__ == "__main__":
    main()
