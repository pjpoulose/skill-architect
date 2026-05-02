# Skill Architect

> **Design rigorous, single-responsibility LLM skills that don't drift, sprawl, or break.**

A platform-agnostic skill design framework that helps you turn vague AI intents into validated, ship-ready specs. Works with any modern LLM — Claude, GPT, Gemini, Llama, Mistral, or anything else that can read a system prompt.

---

## The problem

LLM skills, prompt templates, and "agents" proliferate without contracts. Three failure modes show up in almost every collection:

| Failure | What it looks like |
|---|---|
| **Mega-prompts** | One prompt that summarizes a thread, drafts a reply, and sends it. One bug breaks all three. Cannot be reused, debugged, or evaluated. |
| **Skill sprawl** | `summarize-email`, `email-summary`, `tldr-thread`, `condense-message` — same intent, four prompts. Users pick the wrong one. |
| **Naming drift** | One prompt calls a recipient `to`, another calls it `recipient`, another calls it `target`. Prompts can't be chained. |

Most prompt collections die from these three failures, not from missing features.

---

## What Skill Architect does

Skill Architect is a structured interview that turns a one-line intent into a complete, validated skill specification.

You say: *"Design a skill that extracts action items from a meeting transcript."*

It returns:

- A skill name and ID
- An action class assignment (read · generate · modify · external · irreversible · privileged)
- A tier recommendation (fast-path · standard · high-stakes)
- Strict input and output JSON schemas
- A list of context requirements (what the skill reads from memory)
- A list of connection requirements (which external systems it needs)
- At least three documented failure modes
- A reviewer checklist pre-pass
- A scan against the five core anti-patterns

You get a spec that's ready to ship. No prompt engineering required by the end user.

---

## Why this matters

**Single-responsibility skills compose.** Mega-prompts don't.

**Strict schemas enable chaining.** If skill A's output matches skill B's input, you can pipe them. If they drift, you can't.

**Declared failure modes prevent silent breakage.** A skill that documents what it does when things go wrong fails gracefully. A skill that doesn't, surprises you in production.

**Context lives in memory, not in the skill template.** The same skill produces different output for different users *because of context injection*, not because the template differs. Skill Architect enforces this separation.

---

## LLM compatibility

Skill Architect itself is just a structured prompt + reference docs. It runs anywhere an LLM can read a system prompt.

| Platform | How to install |
|---|---|
| **Claude Code / Claude desktop with skills** | Drop the folder into your skills directory (`~/.claude/skills/skill-architect/`). The YAML frontmatter in `SKILL.md` is Claude Code's discovery format. |
| **Claude API / chat.com** | Paste `SKILL.md` (without the YAML frontmatter) as your system prompt. Add `REFERENCE.md` if you want the model to apply the full taxonomy. |
| **OpenAI / GPT** | Paste `SKILL.md` (without the YAML frontmatter) as a system message. Or upload to a Custom GPT as instructions. |
| **Google Gemini** | Paste as system instructions in the API or a Gem. |
| **Llama / Mistral / open-weights via Ollama, LM Studio, etc.** | Paste as system prompt. Smaller models (≤ 7B) may struggle with the structured interview — recommend ≥ 13B or a hosted frontier model. |
| **Cursor / Aider / coding assistants** | Drop into project root or pass as part of the system prompt. |
| **No-code: Zapier, Make, n8n LLM nodes** | Paste `SKILL.md` body into the system prompt field of your LLM node. |

The framework — action classes, tier model, anti-pattern catalog — is platform-independent. Only the install mechanism varies.

---

## Platform requirements

What does your application or workflow need to actually *use* the skills Skill Architect helps you design?

### Required (you must have these)

| Capability | Why it's required |
|---|---|
| **An LLM** | Obvious. Hosted (Claude / GPT / Gemini) or local (Llama / Mistral). Frontier models work best for the design interview itself. |
| **A way to load instructions** | System prompts, function instructions, skill files, or upload — anything that lets you give the model a long-form set of rules to follow. |
| **A way for the user to invoke the skill** | Chat interface, API endpoint, CLI, or function call. |

That's it. If you have those three, Skill Architect can help you design skills.

### Recommended (you'll want these once you have ≥ 5 skills)

| Capability | Why it helps |
|---|---|
| **A canonical vocabulary list** | A shared file that documents your standard field names (e.g., always `recipient`, never `to` or `target`). Prevents anti-pattern AP-04 (naming drift). |
| **A persistent memory or context layer** | Lets skills read user facts, preferences, and history at runtime. Without this, you can still use skills, but every invocation is cold-start. |
| **A simple validator (provided)** | The `tools/` directory in this repo contains a JSON Schema and a Python validator. Run it on any spec to confirm it conforms before submission. |
| **A skill registry or library directory** | A place where all your skills live, versioned, with search. Could be a folder, a repo, or a database. |

### Optional (advanced; needed only at scale)

| Capability | Why it matters |
|---|---|
| **Tool / function calling** | If your skills need to invoke external systems (APIs, databases), the host platform must support tool calls or function calling. |
| **Tier-based routing** | A layer that inspects the request and decides which tier (fast-path / standard / high-stakes) to use. Most users start without this and add it once they have skills in multiple tiers. |
| **Critic / evaluator layer** | A second LLM call that evaluates the output of the first before returning to the user. Recommended for high-stakes skills. |
| **Audit log** | A record of every skill invocation, its input, output, and outcome. Required for any skill that touches money, irreversible actions, or sensitive data. |
| **Chain orchestration** | Lets one skill's output feed another skill's input. Can be as simple as sequential function calls, or as complex as a workflow engine. |

**You do not need any of the optional capabilities to start.** Skill Architect is useful at any maturity level. As you grow, you'll add layers — but the framework stays the same.

---

## Installation

### Option A — Claude Code skill (most users)

```bash
cd ~/.claude/skills
git clone https://github.com/pjpoulose/skill-architect.git
```

Then trigger: *"Design a skill that…"* in any Claude Code conversation.

### Option B — Any other LLM (Claude API / GPT / Gemini / etc.)

Clone the repo, then paste `SKILL.md` (skip the YAML frontmatter at the top) as your system prompt:

```bash
git clone https://github.com/pjpoulose/skill-architect.git
cat skill-architect/SKILL.md
# copy the body (skip the --- frontmatter block) and use as system prompt
```

If you want the model to apply the full taxonomy, also include `REFERENCE.md` in the system prompt or as an attached file.

### Option C — Reference only (just read it)

Read `SKILL.md`, `REFERENCE.md`, and `EXAMPLES.md` directly. Apply the framework manually. Skill Architect is as useful as a written checklist as it is as a live skill.

---

## Quick start

In any conversation where the skill is loaded (or the prompt is set), say:

> *"Design a skill that summarizes a meeting transcript into action items."*

or

> *"Spec out a skill that translates a calendar invite into a Slack message."*

or

> *"Write a skill that scans a contract for unfavorable terms."*

Skill Architect runs the interview, classifies the intent, generates the schemas, and returns a complete spec. See `EXAMPLES.md` for three end-to-end runs.

---

## The framework

Skill Architect operationalizes four ideas. Each one independently improves skill quality. Together they prevent most common failures.

### 1. Single-responsibility

Every skill performs exactly one action. Compound behaviors are constructed by chaining. The test: can you describe what the skill does in one sentence with one verb and one object, no compound clauses?

If yes → it's a skill. If no → split it.

### 2. Action class taxonomy

Six classes covering everything a skill can do. Each class has a different risk profile and a different approval ceiling.

| Class | Action | Autonomy |
|---|---|---|
| 1. Read | Observe, retrieve, report. No state change. | Fully autonomous |
| 2. Generate | Create content that stays internal until sent. | Fully autonomous |
| 3. Modify-internal | Change internal state (settings, memory, configuration). Reversible. | Requires explicit user instruction |
| 4. External-known | Communicate with a known recipient (email, message, calendar). | Autonomous, logged |
| 5. External-irreversible | Publish, delete, submit, order. Cannot be undone. | Approval required |
| 6. Privileged | Financial transactions, new permissions, new recipients. | Approval required |

### 3. Tier model

Three execution tiers based on risk and complexity.

| Tier | When to use | Chain depth |
|---|---|---|
| Fast-path | Class 1–3, low ambiguity, single LLM call | Single skill |
| Standard | Class ≤ 4, moderate ambiguity, ≤ 2 LLM calls | Up to 2 chained |
| High-stakes | Class 5–6, financial, irreversible | Arbitrary chain length with review |

### 4. Anti-pattern catalog

Five failure shapes that account for most rejected submissions in production skill libraries.

| ID | Pattern | Symptom |
|---|---|---|
| AP-01 | Monolithic mega-prompt | One skill bundles ≥ 2 action classes |
| AP-02 | Skill sprawl | Same intent under different names |
| AP-03 | Excessive granularity | Skill cannot stand alone — only useful in a chain |
| AP-04 | Naming drift | Inconsistent field names across skills |
| AP-05 | Exposed complexity | User asked to make a prompt-engineering decision |

Skill Architect catches all five before submission.

Full reference: see [`REFERENCE.md`](./REFERENCE.md).

---

## Tooling

The `tools/` directory provides programmatic validation of skill specs.

| File | Purpose |
|---|---|
| `tools/spec_schema.json` | JSON Schema for the canonical skill spec format |
| `tools/validate.py` | Python validator — takes a YAML or JSON spec, returns pass/fail + errors |
| `tools/requirements.txt` | Python dependencies (`pyyaml`, `jsonschema`) |
| `tools/README.md` | Usage instructions |

### Run the validator

```bash
cd skill-architect
pip install -r tools/requirements.txt
python tools/validate.py path/to/your-spec.yaml
```

Returns exit code 0 on pass, 1 on fail. CI-friendly. See `tools/README.md` for details.

### Continuous integration

`.github/workflows/validate.yml` runs the validator on every push and PR. Fork the repo and your specs are validated automatically.

---

## Worked examples

See [`EXAMPLES.md`](./EXAMPLES.md) for three end-to-end runs:

1. **Read-only example** — extract action items from a transcript
2. **Generate example** — draft a follow-up email
3. **Privileged example** — schedule a payment

Each example shows the user input, the interview, the generated spec, and the reviewer checklist pre-pass.

---

## When to use Skill Architect

- Before writing a new LLM skill from scratch
- When auditing an existing skill or prompt for hygiene
- When standardizing skills across a team or organization
- When training others on skill design
- When preparing skills for a public marketplace, shared repo, or production deployment

## When not to use it

- Quick one-off prompts that won't be reused
- Pure conversational interactions
- A skill that already works and isn't drifting
- Tasks better served by a non-AI tool

---

## Design principles

1. **Hide the complexity.** Users invoke skills by saying what they want. They never see schemas, tiers, or action classes.
2. **Make the contract explicit.** Behind the scenes, every skill has a strict input schema, a strict output schema, and a declared failure-mode list.
3. **Compose, don't bundle.** Chains of single-responsibility skills are stronger than one mega-skill.
4. **Context is 80% of quality.** A skill that reads the right memory at runtime produces dramatically better output than one with a perfect template and no context.
5. **Friction-driven evolution.** The best skills are not designed up front — they are grown by watching real usage fail and encoding the fix.

---

## Contributing

Issues, anti-pattern submissions, and example contributions welcome. Open an issue or a PR.

**New anti-patterns require a documented production failure** — opinion alone isn't enough. See `REFERENCE.md` §4.1 for the required entry format.

**New examples** are welcome — read `EXAMPLES.md` to see the format. One example per PR. Cover an action class or platform pattern not already shown.

---

## Author

**Paul Poulose** ([@pjpoulose](https://github.com/pjpoulose))

Built from observed patterns across multiple LLM skill collections. The framework prioritizes longevity (skills that compose, evolve, and don't rot) over speed of first authorship.

---

## License

[MIT](./LICENSE) — use it, fork it, ship it. Attribution appreciated but not required.

---

## Acknowledgments

The single-responsibility principle, schema strictness, and chaining patterns draw on long-established software engineering ideas (Unix philosophy, microservices, type contracts) applied to LLM-orchestrated work. The "context is 80%, template is 20%" framing borrows from Andrej Karpathy's *context engineering*. The anti-pattern catalog is original to this skill, derived from observed failures across multiple production deployments.
