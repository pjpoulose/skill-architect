# Tools

Programmatic validation for Skill Architect specs. Catches schema errors, lightweight anti-patterns, and class/tier consistency issues before submission or merge.

---

## What's here

| File | Purpose |
|---|---|
| `spec_schema.json` | JSON Schema for the canonical Skill Architect spec format |
| `validate.py` | Python validator — accepts YAML or JSON specs, returns pass/fail with errors |
| `requirements.txt` | Python dependencies (`pyyaml`, `jsonschema`) |

---

## Install

```bash
pip install -r tools/requirements.txt
```

Tested on Python 3.10+. No other dependencies.

---

## Usage

### Validate a single spec

```bash
python tools/validate.py specs/extract-action-items.yaml
```

### Validate a directory of specs

```bash
python tools/validate.py specs/
```

The validator recursively finds all `*.yaml`, `*.yml`, and `*.json` files.

### Quiet mode (CI-friendly)

```bash
python tools/validate.py specs/ --quiet
```

Prints only failures and the summary.

---

## What the validator checks

| Check | Description |
|---|---|
| **Schema conformance** | All required fields present, types correct, schemas strict (`additionalProperties: false`), enum values valid, semver and skill_id patterns respected. |
| **AP-01 — compound intent** | Heuristic scan of `single_responsibility_assertion` for "and then", "and send", etc. False positives possible — informational only. |
| **AP-04 — naming drift** | Field names in `input_schema` and `output_schema` checked against a known canonical list (`to` → `recipient`, etc.). Extend the list in `validate.py` for your library. |
| **Class/tier consistency** | Ensures `tier_recommendation` matches the floor mandated by `action_class` (e.g., Class 5–6 must be `high-stakes`). |
| **Failure-mode diversity** | Heuristic check that `failure_modes` covers input-side, runtime-side, and output-side failures. Informational only — keyword-based. |

### What the validator does **not** check

| Anti-pattern | Why not |
|---|---|
| **AP-02 — skill sprawl** | Requires comparing against your library; not solvable from a single spec file. |
| **AP-03 — excessive granularity** | Requires judgment about whether a skill stands alone. Use the LLM-based interview for this. |
| **AP-05 — exposed complexity** | Requires reading the user-facing copy embedded in `failure_modes` and `summary`. LLM judgment is more reliable. |

For full anti-pattern coverage, run the full Skill Architect interview against the spec.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All specs pass. Notes (if any) are informational. |
| `1` | One or more specs have hard failures. |
| `2` | Usage error or missing dependencies. |

CI-safe — wire into any CI system that respects exit codes.

---

## Continuous integration

A GitHub Actions workflow at `.github/workflows/validate.yml` runs the validator on every push and pull request. Fork this repo and your skill specs are validated automatically.

To add validation to a different CI system, run:

```bash
pip install -r tools/requirements.txt
python tools/validate.py specs/
```

Fail the build if exit code is non-zero.

---

## Extending the validator

### Add a new canonical name (AP-04)

Edit `NAMING_DRIFT_CANONICAL` in `validate.py`:

```python
NAMING_DRIFT_CANONICAL = {
    "to": "recipient",
    "target": "recipient",
    "your_field": "your_canonical",  # add here
}
```

### Add a new schema field

Edit `spec_schema.json`. Add to `properties` and (if required) `required`. Re-run the validator on existing specs to confirm they still pass.

### Add a custom check

Add a function to `validate.py` that takes a `spec: dict` and returns a `list[str]` of error strings (each prefixed with `[YOUR-CHECK]`). Call it from `validate_spec()`.

---

## Notes

- The schema enforces strict `additionalProperties: false` on input/output schemas. This is intentional — see `REFERENCE.md` §1 (single-responsibility) and §4 (anti-patterns) for why.
- The validator does not invoke an LLM. For full coverage, run the Skill Architect interview against any spec the validator approves.
- This is v0.1 tooling. Patches and extensions welcome — open a PR.

---

## License

MIT — see `../LICENSE`.
