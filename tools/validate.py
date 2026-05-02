#!/usr/bin/env python3
"""
Skill Architect — Spec Validator

Validates a skill spec (YAML or JSON) against the canonical Skill Architect schema.
Also runs lightweight anti-pattern checks that don't require LLM judgment.

Usage:
    python tools/validate.py path/to/spec.yaml
    python tools/validate.py path/to/spec.json
    python tools/validate.py specs/  # recursively validates all *.yaml, *.yml, *.json

Exit codes:
    0  all specs pass
    1  one or more specs fail
    2  usage error or missing dependencies

Dependencies:
    pip install -r tools/requirements.txt

License: MIT — see LICENSE
Author:  Paul Poulose (@pjpoulose)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    print("ERROR: pyyaml is required. Run: pip install -r tools/requirements.txt", file=sys.stderr)
    sys.exit(2)

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema is required. Run: pip install -r tools/requirements.txt", file=sys.stderr)
    sys.exit(2)


SCHEMA_PATH = Path(__file__).parent / "spec_schema.json"

# Lightweight anti-pattern heuristics (catchable without an LLM).
# AP-02, AP-03, AP-05 require human or model judgment and are not checked here.

COMPOUND_INTENT_TOKENS = [
    r"\band\s+then\b",
    r"\band\b.*\b(send|publish|delete|submit|post|push|notify)\b",
    r"\b,\s*then\b",
]

NAMING_DRIFT_CANONICAL = {
    # Common drift patterns. Add more as your library grows.
    "to": "recipient",
    "target": "recipient",
    "target_email": "recipient",
    "from": "sender",
    "txt": "text",
    "msg": "message",
    "ts": "timestamp",
    "dt": "date",
}


def load_spec(path: Path) -> dict[str, Any]:
    """Load a spec from YAML or JSON. Raises on parse errors."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text)
    if path.suffix.lower() == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported file extension: {path.suffix} (expected .yaml, .yml, or .json)")


def load_schema() -> dict[str, Any]:
    """Load the canonical schema."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema not found at {SCHEMA_PATH}. "
            "Run from the skill-architect repo root."
        )
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(spec: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Return a list of human-readable schema validation errors."""
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(spec), key=lambda e: e.path):
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"  [SCHEMA] {path}: {err.message}")
    return errors


def ap01_check(spec: dict[str, Any]) -> list[str]:
    """AP-01 Monolithic Mega-Prompt: heuristic check on single_responsibility_assertion."""
    sra = spec.get("single_responsibility_assertion", "") or ""
    findings: list[str] = []
    sra_lower = sra.lower()
    for pattern in COMPOUND_INTENT_TOKENS:
        if re.search(pattern, sra_lower):
            findings.append(
                f"  [AP-01] single_responsibility_assertion may be compound (matched /{pattern}/). "
                "Consider splitting into multiple skills."
            )
            break  # one warning is enough
    return findings


def ap04_check(spec: dict[str, Any]) -> list[str]:
    """AP-04 Naming Drift: warn on field names with known canonical alternatives."""
    findings: list[str] = []
    for schema_key in ("input_schema", "output_schema"):
        sub = spec.get(schema_key, {}) or {}
        properties = sub.get("properties", {}) or {}
        for field_name in properties.keys():
            if field_name in NAMING_DRIFT_CANONICAL:
                canonical = NAMING_DRIFT_CANONICAL[field_name]
                findings.append(
                    f"  [AP-04] {schema_key}.properties.{field_name}: "
                    f"prefer canonical name '{canonical}'."
                )
    return findings


def class_tier_consistency_check(spec: dict[str, Any]) -> list[str]:
    """Ensure tier_recommendation is consistent with action_class per REFERENCE.md §2."""
    findings: list[str] = []
    action_class = spec.get("action_class")
    tier = spec.get("tier_recommendation")
    if action_class in (5, 6) and tier != "high-stakes":
        findings.append(
            f"  [TIER] action_class={action_class} requires tier_recommendation=high-stakes "
            f"(got {tier!r})."
        )
    if action_class == 4 and tier == "fast-path":
        findings.append(
            f"  [TIER] action_class=4 should not be fast-path (external communication). "
            f"Got {tier!r}."
        )
    return findings


def failure_mode_diversity_check(spec: dict[str, Any]) -> list[str]:
    """Encourage at least one input-side, one context/runtime-side, one output-side failure mode.

    Heuristic: keyword scan over trigger_condition. Not authoritative — informational only.
    """
    modes = spec.get("failure_modes", []) or []
    if len(modes) < 3:
        return []  # schema check already flagged this

    text = " ".join(m.get("trigger_condition", "").lower() for m in modes)
    has_input_side = any(k in text for k in ("input", "missing", "invalid", "exceeds", "too long", "empty"))
    has_runtime_side = any(k in text for k in ("connection", "api", "context", "memory", "unavailable", "permission"))
    has_output_side = any(k in text for k in ("output", "fabricat", "no result", "ambiguous", "no action", "not found"))

    findings: list[str] = []
    if not has_input_side:
        findings.append("  [INFO] failure_modes may be missing an input-side failure (e.g. invalid input).")
    if not has_runtime_side:
        findings.append("  [INFO] failure_modes may be missing a runtime/context-side failure.")
    if not has_output_side:
        findings.append("  [INFO] failure_modes may be missing an output-side failure.")
    return findings


def validate_spec(path: Path, schema: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a single spec file. Returns (passed, errors)."""
    try:
        spec = load_spec(path)
    except Exception as exc:
        return False, [f"  [PARSE] Could not parse {path.name}: {exc}"]

    if not isinstance(spec, dict):
        return False, [f"  [PARSE] {path.name}: top-level must be an object/mapping."]

    errors: list[str] = []
    errors.extend(schema_errors(spec, schema))
    errors.extend(ap01_check(spec))
    errors.extend(ap04_check(spec))
    errors.extend(class_tier_consistency_check(spec))
    errors.extend(failure_mode_diversity_check(spec))

    # Distinguish hard failures from informational notes.
    hard_failures = [e for e in errors if not e.lstrip().startswith("[INFO]")]
    return (len(hard_failures) == 0), errors


def collect_specs(target: Path) -> list[Path]:
    """Collect spec files from a path. Path may be a file or a directory."""
    if target.is_file():
        return [target]
    if target.is_dir():
        files: list[Path] = []
        for ext in ("*.yaml", "*.yml", "*.json"):
            files.extend(sorted(target.rglob(ext)))
        return files
    raise FileNotFoundError(f"No such file or directory: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate one or more Skill Architect skill specs."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a spec file (.yaml, .yml, .json) or a directory containing specs.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only failures.",
    )
    args = parser.parse_args()

    try:
        schema = load_schema()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        specs = collect_specs(args.path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not specs:
        print(f"WARNING: no spec files found under {args.path}", file=sys.stderr)
        return 0

    overall_pass = True
    pass_count = 0
    fail_count = 0
    for path in specs:
        passed, errors = validate_spec(path, schema)
        if passed and not errors:
            pass_count += 1
            if not args.quiet:
                print(f"PASS  {path}")
        elif passed and errors:
            # Has informational notes only.
            pass_count += 1
            if not args.quiet:
                print(f"PASS  {path}  (with notes)")
                for e in errors:
                    print(e)
        else:
            fail_count += 1
            overall_pass = False
            print(f"FAIL  {path}")
            for e in errors:
                print(e)

    print()
    print(f"Summary: {pass_count} passed, {fail_count} failed.")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
