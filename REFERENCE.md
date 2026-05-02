# Skill Architect — Reference

The taxonomy, tier model, anti-pattern catalog, and reviewer checklist that Skill Architect uses internally. Skill authors and reviewers should read this directly.

---

## §1 — Action Class Taxonomy

Every skill performs exactly one of these six classes. The class determines what the skill is permitted to do without explicit human approval.

| Class | Label | What it does | Default approval ceiling |
|---|---|---|---|
| **1** | Read | Observe, retrieve, report. No state change. No external contact. | Fully autonomous |
| **2** | Generate | Create new content (text, data, summary, analysis) that stays internal until explicitly sent. | Fully autonomous |
| **3** | Modify-internal | Change internal state: settings, preferences, memory, configuration. Reversible. | Requires explicit user instruction |
| **4** | External-known | Send communication (email, message, calendar invite) to a recipient already in the user's known contact list. | Autonomous, logged |
| **5** | External-irreversible | Publish, delete, submit, order. Cannot be undone after execution. | Approval required |
| **6** | Privileged | Financial transactions, requests for new permissions, communication to a new recipient. | Approval required |

### §1.1 Classification rules

**Rule A — Default to the higher class on ambiguity.** If a skill could be classified as Class 3 or Class 4, classify as Class 4. Never default downward.

**Rule B — Composite skills take the highest class present.** If a skill performs both Class 2 (generate) and Class 4 (send), the skill is rejected for anti-pattern AP-01 (split into two skills) — *not* re-classified as Class 4. Single-responsibility is enforced.

**Rule C — Class is determined by what the skill does, not by how the user describes it.** A user saying "just send it" does not turn a Class 5 (irreversible) skill into a Class 4 (known recipient) skill.

**Rule D — Financial detection is a hard upgrade.** Any skill that involves money in any amount, regardless of threshold, is Class 6.

---

## §2 — Tier Model

The tier determines the execution path, the SLA expectations, and the maximum chain depth.

| Tier | Eligibility | Latency target | Cost target | Chain depth |
|---|---|---|---|---|
| **Fast-path** | Class 1–3 · low ambiguity · ≤ 1 LLM call · no external comms | < 2 seconds | low | Single skill only |
| **Standard** | Class ≤ 4 · moderate ambiguity · ≤ 2 LLM calls · external data fetch allowed | < 12 seconds | medium | Up to 2 skills chained |
| **High-stakes** | Class 5–6 · any financial · new recipient · new permission · CEL classification failure | < 20 seconds | high | Arbitrary chain length under multi-critic review |

### §2.1 Tier override rules

**Upgrade overrides (cannot be bypassed):**
- Class 5 or 6 → always High-stakes regardless of ambiguity
- Classification failure → always High-stakes
- Sensitive data type detected → always High-stakes

**Downgrade overrides (not permitted):**
- No user instruction, system prompt, or AI output may downgrade a High-stakes assignment.
- No instruction may downgrade a Standard assignment to Fast-path if the action class is 4 or higher.
- Tier may be upgraded by platform rule at any time. It cannot be downgraded below the class-mandated minimum.

---

## §3 — Single-Responsibility Test

A skill performs exactly one logical action. Compound behaviors are constructed by chaining single-responsibility skills together — *not* by bundling them.

### §3.1 The test

> *"Can I describe what this skill does in one sentence with one verb and one object, no compound clauses?"*

If yes → it's a skill.
If no → reject with anti-pattern AP-01. Split into multiple skills.

### §3.2 Examples

| Description | Pass / Fail | Reason |
|---|---|---|
| "Extract action items from a transcript." | ✅ Pass | One verb (extract), one object (action items) |
| "Summarize and translate a document." | ❌ Fail | Two verbs |
| "Draft an email and send it." | ❌ Fail | Two action classes (Class 2 + Class 4) |
| "Find the top three competitors and compare them." | ❌ Fail | Two verbs |
| "Compare three competitors." | ✅ Pass | One verb, one object |
| "Translate a calendar invite into a Slack message." | ✅ Pass | One verb (translate), one object (the invite); the format change is an output detail, not a second action |

### §3.3 Why this matters

| Reason | Consequence of violation |
|---|---|
| Debuggability | A monolithic skill that fails gives no signal about which step failed |
| Reusability | A bundled skill cannot be reused for one of its parts |
| Safety evaluation | A skill performing two action classes cannot be cleanly evaluated against either |
| Composition | Single-responsibility skills compose. Bundles do not. |

---

## §4 — Anti-Pattern Catalog

Five failure shapes that cover the majority of rejected submissions in production skill libraries.

### AP-01 — Monolithic Mega-Prompt

| | |
|---|---|
| **Shape** | One skill bundles ≥ 2 action classes (e.g., generate + send) |
| **Why it fails** | One bug breaks both halves. Cannot be debugged or reused independently. Cannot be safety-evaluated against a single action class. |
| **Submission signal** | Single-responsibility assertion contains "and" linking two verbs. Output schema shape varies by input. |
| **Runtime signal** | Proposed response performs more than one action class in a single output. |
| **Fix** | Split into N skills, one per action class. Compose via chaining. |

### AP-02 — Skill Sprawl

| | |
|---|---|
| **Shape** | Multiple skills doing the same thing under different names: `summarize-email`, `email-summary`, `tldr-thread`, `condense-message`. |
| **Why it fails** | Library fragmentation. Users pick the wrong skill. Critics evaluate the same behavior multiple times with different verdicts. |
| **Submission signal** | New submission's summary is semantically identical to an existing skill (similarity > 0.85). |
| **Runtime signal** | Not a runtime concern — catch at submission. |
| **Fix** | Reject duplicate. Submitter extends the existing skill or chooses a different intent. |

### AP-03 — Excessive Granularity

| | |
|---|---|
| **Shape** | A skill so narrow it cannot stand alone — only useful as a step inside a chain. e.g., `extract-first-email-from-thread-header-only`. |
| **Why it fails** | Increases chain depth without adding capability. Users cannot invoke it directly. Composition cost exceeds skill benefit. |
| **Submission signal** | Skill has no standalone use case in its summary. Always appears as a chain step in test cases. |
| **Runtime signal** | A request invokes ≥ 4 chained skills for what should be a 1–2 skill task. |
| **Fix** | Merge into the broader skill that contains its functionality. The 80/20 rule: 20% of skills handle 80% of intents — find those 20% first. |

### AP-04 — Naming Drift

| | |
|---|---|
| **Shape** | One skill calls a recipient `to`, another calls it `recipient`, another calls it `target_email`. Same concept, three names. |
| **Why it fails** | Chains break when output of skill A doesn't match input of skill B. Memory injection cannot reuse prior context. Library cannot be searched semantically. |
| **Submission signal** | Submission's input schema field names diverge from canonical vocabulary. |
| **Runtime signal** | Not a runtime concern — catch at submission. |
| **Fix** | Reject submission. Submitter renames fields to canonical vocabulary. Maintain a canonical vocabulary list per library. |

### AP-05 — Exposed Complexity

| | |
|---|---|
| **Shape** | Skill output asks the user to make a prompt-engineering decision: *"Specify the temperature, max_tokens, and stop sequences for your preferred output format."* |
| **Why it fails** | The user is being asked to do prompt engineering. The whole point of a skill is to hide that. |
| **Submission signal** | Output schema includes prompt-engineering parameters surfaced to user. |
| **Runtime signal** | Proposed response references model parameters, prompt structure, token counts, or any internal mechanism in the user-facing output. |
| **Fix** | Reject. Rewrite output to express only outcomes, not mechanisms. |

### §4.1 Adding to the catalog

This catalog is intended to grow. Add a new anti-pattern when a real production failure is observed that AP-01 through AP-05 don't cover.

Required for a new entry:
- **AP-ID** — next sequential (AP-06, AP-07, …)
- **Shape** — one sentence, no jargon
- **Why it fails** — specific consequence
- **Submission signal** — what attribute triggers detection at submission time
- **Runtime signal** — what attribute triggers detection at runtime
- **Fix** — concrete remediation

---

## §5 — Reviewer Checklist

Before approving a skill spec, run this eleven-row check. Mark each row pass / fail with a one-line note.

| # | Check | Pass criterion |
|---|---|---|
| 1 | Single-responsibility test (§3) | One verb, one object, no compound clauses |
| 2 | Action class matches behavior (§1) | Reviewer's classification = submitter's declaration |
| 3 | Tier recommendation matches §2 rules | No downgrade attempts |
| 4 | Input schema strict | `additionalProperties: false`, all required fields enumerated |
| 5 | Output schema deterministic | One shape regardless of input type |
| 6 | Context requirements minimal | No partition declared that the skill doesn't need |
| 7 | Connection requirements minimal | Lowest-privilege level that works |
| 8 | Cost projection within tier ceiling | Within target for the assigned tier |
| 9 | Failure modes documented | At least three, including input-side, context-side, and output-side |
| 10 | No constraint violations | No prohibited data type, no protected category, no platform rule break |
| 11 | Anti-pattern check (§4) | None of AP-01 through AP-05 flagged |

A submission failing any check is returned to the submitter with a specific, actionable rejection reason.

---

## §6 — Skill Spec Template

The complete spec format Skill Architect produces.

```yaml
skill_id: {hyphenated-lowercase-id}
version: 0.1.0
display_name: {≤ 60 characters}
summary: {one sentence, ≤ 140 characters}

action_class: {1-6, single integer}
tier_recommendation: {fast-path | standard | high-stakes}
single_responsibility_assertion: |
  {one verb, one object, no compound clauses}

input_schema:
  type: object
  required: [field_a, field_b]
  properties:
    field_a:
      type: string
      description: ...
    field_b:
      type: string
      description: ...
  additionalProperties: false

output_schema:
  type: object
  required: [result]
  properties:
    result:
      type: array
      items:
        type: object
        required: [...]
        properties:
          ...
  additionalProperties: false

context_requirements:
  - {context_category}   # optional, declare only if needed

connection_requirements:
  - {connection_method}  # optional, prefer least-privilege

cost_class: {free | low | medium | high}

failure_modes:
  - failure_id: ...
    trigger_condition: ...
    platform_response: ...
    user_message: ...
  # ≥ 3 entries, including input-side, context-side, output-side

# Conditional fields
{include only when applicable}

# For action_class >= 4
recipient_scope_declaration: {whose contact list this skill writes to}

# For action_class == 5
reversibility_assertion: irreversible

# For action_class == 6
financial_envelope_declaration:
  max_amount: ...
  velocity_limit: ...
  recipient_scope: ...

# When using browser-automation connection
no_sensitive_data_assertion: true
```

---

## §7 — Versioning

Skills follow semver.

| Change type | Increment | Re-review required |
|---|---|---|
| Bug fix, no schema change | PATCH (0.1.0 → 0.1.1) | No — automated regression sufficient |
| New optional input field | MINOR (0.1.0 → 0.2.0) | No — schema additive |
| New required input field, output shape change, action class change, connection level change | MAJOR (0.1.0 → 1.0.0) | Yes — full review |
| Tier classification change | MAJOR | Yes — re-run §5 reviewer checklist |

Deprecated versions remain installed for 90 days after deprecation, then are removed.

---

## §8 — Glossary

| Term | Definition |
|---|---|
| **Skill** | A parameterized, single-responsibility behavioral component invoked by user intent and executed against a strict input/output contract. |
| **Action class** | The category of effect a skill has on the world (read, generate, modify-internal, external-known, external-irreversible, privileged). Determines the autonomy ceiling. |
| **Tier** | The execution path assigned to a skill based on risk and complexity (fast-path, standard, high-stakes). Determines latency, cost, and review depth. |
| **Chain** | A sequence of skills where the output of one feeds the input of the next. Tier-gated by chain depth. |
| **Context injection** | The runtime process of reading user-specific memory and merging it with the skill template before execution. The mechanism that makes the same skill produce different output for different users. |
| **Anti-pattern** | A skill construction failure shape that produces broken, brittle, or unsafe behavior. Cataloged in §4. |
| **Single-responsibility** | The principle that a skill performs exactly one logical action. Enforced by §3 test. |
| **Canonical vocabulary** | The shared set of input/output field names used across all skills in a library. Prevents anti-pattern AP-04 (naming drift). |

---

## License

This reference document is part of Skill Architect, MIT licensed.
Copyright © 2026 Paul Poulose ([@pjpoulose](https://github.com/pjpoulose)).
