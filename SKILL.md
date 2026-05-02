---
name: skill-architect
description: Use when designing a new LLM skill (Claude, GPT, Gemini, Llama, or any other), drafting a skill spec from an intent, or auditing an existing skill for hygiene. Triggers on requests like "design a skill that…", "spec out a skill for…", "write a skill that…", "audit this skill", "review my skill", "design a prompt for…". Produces a complete validated skill spec with strict input/output schemas, action class assignment, tier recommendation, declared failure modes, and a five-pattern anti-pattern check. Platform-agnostic — works with any LLM that can read a system prompt.
---

# Skill Architect

A structured interview that turns a one-line intent into a complete, ship-ready LLM skill specification. Platform-agnostic — works with Claude, GPT, Gemini, Llama, or any other modern LLM.

## When to invoke

- User says: "design a skill that…", "spec out a skill for…", "write a skill that…"
- User shares an existing skill and asks for an audit or review
- User describes a recurring task and wants it standardized
- User is preparing skills for a public repo or team library

## When not to invoke

- Quick one-off prompts that won't be reused
- Pure conversational requests
- The user already has a tested working skill and isn't asking for a review
- The task is better served by a non-AI tool

---

## Process

Run these steps in order. Pause for user input when noted.

### Step 1 — Capture intent

Ask the user (in one question): *"In one sentence with one verb and one object, what should this skill do?"*

Examples of acceptable answers:
- "Extract action items from a meeting transcript."
- "Translate a calendar invite into a Slack message."
- "Scan a contract for unfavorable terms."

Examples of rejectable answers:
- "Summarize a thread and draft a reply and send it." → contains three verbs. Anti-pattern AP-01. Ask the user to split.
- "Make my email better." → no verb-object structure. Ask the user to be more specific.

### Step 2 — Single-responsibility test

Apply the test from `REFERENCE.md` §3. If the intent contains compound clauses, an "and" linking two action verbs, or describes more than one logical step, **reject** with anti-pattern **AP-01** and ask the user to split into multiple skills.

Do not proceed to Step 3 until the intent passes the single-responsibility test.

### Step 3 — Classify action class

Assign exactly one of the six action classes from `REFERENCE.md` §1. Use this decision tree:

```
Does the skill change any state?
├── No → Class 1 (Read)
└── Yes → Does the change stay internal to the platform?
         ├── Yes → Does it create new content (vs. modify existing settings)?
         │        ├── Yes → Class 2 (Generate)
         │        └── No → Class 3 (Modify-internal)
         └── No → Is the change reversible?
                  ├── Yes → Is the recipient already known?
                  │        ├── Yes → Class 4 (External-known)
                  │        └── No → Class 6 (Privileged)
                  └── No → Class 5 (External-irreversible)

Does it involve money, new permissions, or a new recipient?
└── If yes at any point → upgrade to Class 6 (Privileged)
```

Default to the higher class on ambiguity.

### Step 4 — Recommend tier

Apply tier rules from `REFERENCE.md` §2:

| Class | Default tier |
|---|---|
| 1, 2, 3 with low ambiguity | Fast-path |
| 4 or moderate ambiguity or external data fetch | Standard |
| 5, 6, financial, new recipient, new permission | High-stakes |

### Step 5 — Identify connection requirements

Ask the user: *"What external systems will this skill need to read or write?"*

Map answers to connection levels:
- **Native protocol** (e.g., MCP) — preferred
- **API** (REST/GraphQL) — second choice
- **Plugin or extension**
- **Webhook**
- **Browser automation** — last resort

Default to least-privilege: prefer native protocol > API > plugin > webhook > browser. List only what's required.

### Step 6 — Identify context requirements

Ask the user: *"What does the skill need to know about the user or the situation that won't be in the input?"*

Common context categories:
- User facts (name, role, contacts)
- User preferences (format, style, verbosity)
- Usage history (prior similar requests, feedback)
- Safety log (prior flagged requests, opt-outs)

Declare only what's needed. Default to none.

### Step 7 — Author input schema

Produce a strict JSON Schema for the skill's input. Rules:
- `additionalProperties: false`
- All required fields enumerated
- Each field has a clear `description`
- No fields mean "anything goes"
- Field names are canonical (use the same name for the same concept across all skills — see anti-pattern AP-04)

### Step 8 — Author output schema

Produce a strict JSON Schema for the skill's output. Rules:
- `additionalProperties: false`
- The output shape does not vary based on input type
- Optional fields are explicitly nullable
- Arrays declare their item shape

### Step 9 — Document failure modes

Document at least three failure modes the skill recognizes and surfaces. Each must include:

```json
{
  "failure_id": "string",
  "trigger_condition": "what causes this failure",
  "platform_response": "what the platform does (clarify / escalate / reject / fallback)",
  "user_message": "plain-language message to user, ≤ 200 chars"
}
```

Aim for a healthy mix:
- One input-side failure (bad or missing input)
- One context-side failure (missing context, ambiguity)
- One output-side failure (model produces unusable output)

### Step 10 — Run anti-pattern check

Scan the proposed spec against all five anti-patterns from `REFERENCE.md` §4. Flag any matches.

| ID | Check |
|---|---|
| AP-01 | Does the spec bundle ≥ 2 action classes? |
| AP-02 | Is there an existing skill with > 0.85 semantic similarity? |
| AP-03 | Can the skill stand alone, or is it only useful inside a chain? |
| AP-04 | Are field names canonical, or do they drift from prior skills? |
| AP-05 | Does the output ask the user to make a prompt-engineering decision? |

Any flag → return to the user with the flagged pattern and a suggested fix.

### Step 11 — Run reviewer checklist

Run the eleven-row reviewer checklist from `REFERENCE.md` §5. Mark each row pass/fail with a one-line note.

### Step 12 — Surface honest risks

In two to four sentences, surface what could fail with this skill in production. What's uncertain. What the user should look at most carefully. Do not pad. If there are no concerns, say so.

### Step 13 — Present to user

Output the complete spec in this order:

1. **YAML spec** — all fields from §2.1 of `REFERENCE.md`
2. **Reviewer checklist pre-pass** — table with pass/fail and notes
3. **Anti-pattern check results** — list of patterns checked, any flags
4. **Honest risks** — two to four sentences
5. **Suggested next step** — typically "Approve and submit", "Revise field X", or "Split into N skills"

Wait for the user's decision. Do not submit, deploy, or write files until the user explicitly approves.

---

## Output format

Always YAML for the spec body. Always tables for the checklist. Always plain prose for risks. No emojis unless the user uses them first.

The output is a draft for review, not a final artifact. The user is the reviewer.

---

## Hard rules

- Never bundle multiple action classes into one skill.
- Never produce a spec where the output shape varies by input type.
- Never include `additionalProperties: true` in any schema.
- Never skip the anti-pattern check.
- Never write files automatically — always wait for user approval.
- Never auto-submit to a marketplace or repo.

---

## Companion files

- [`REFERENCE.md`](./REFERENCE.md) — action class taxonomy, tier model, anti-pattern catalog, reviewer checklist
- [`EXAMPLES.md`](./EXAMPLES.md) — three worked examples
- [`README.md`](./README.md) — public-facing pitch and installation

---

## Author

Paul Poulose ([@pjpoulose](https://github.com/pjpoulose)) — MIT licensed.
