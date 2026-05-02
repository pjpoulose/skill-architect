# Changelog

All notable changes to Skill Architect are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-05-02

### Added
- Initial public release
- `SKILL.md` — the structured-interview skill itself, with YAML frontmatter for Claude Code discovery and a body usable as a system prompt for any LLM
- `REFERENCE.md` — action class taxonomy (6 classes), tier model (3 tiers), anti-pattern catalog (AP-01 through AP-05), 11-row reviewer checklist, canonical spec template, glossary
- `EXAMPLES.md` — three end-to-end worked examples covering Class 1 (read), Class 2 (generate), and Class 6 (privileged financial)
- `tools/spec_schema.json` — JSON Schema for canonical spec validation
- `tools/validate.py` — Python validator with schema check, AP-01 / AP-04 heuristics, class/tier consistency, failure-mode diversity
- `tools/requirements.txt` — Python dependencies (`pyyaml`, `jsonschema`)
- `tools/README.md` — validator usage and extension guide
- `.github/workflows/validate.yml` — GitHub Actions CI that validates `specs/` on every push and PR
- `specs/example-extract-action-items.yaml` — fixture spec for the validator
- `README.md` — public-facing pitch, problem, framework summary, LLM compatibility matrix, platform requirements section, install paths, contributing guide
- `LICENSE` — MIT
- `.gitignore` — standard ignores

### Notes
- Framework is platform-agnostic. Works with Claude, GPT, Gemini, Llama, Mistral, or any LLM that can read a system prompt.
- Validator catches schema errors, compound intents (AP-01), and naming drift (AP-04). AP-02, AP-03, and AP-05 require LLM judgment and are caught by the interview, not by the validator.
- Tooling is unverified in this initial release — no test suite yet. Run on your own specs to confirm correctness.

[0.1.0]: https://github.com/pjpoulose/skill-architect/releases/tag/v0.1.0
