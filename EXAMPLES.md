# Skill Architect — Worked Examples

Three end-to-end runs showing what Skill Architect produces. Each example shows the user's input, a condensed view of the interview, the generated spec, and the reviewer checklist pre-pass.

---

## Example 1 — Read-only skill (Class 1)

### User input

> *"Design a skill that extracts action items from a meeting transcript."*

### Interview summary

| Step | Skill Architect's classification |
|---|---|
| Single-responsibility test | ✅ Pass — one verb (extract), one object (action items) |
| Action class | Class 1 (Read) — pulls existing data from a transcript, no state change |
| Tier recommendation | Fast-path — Class 1, low ambiguity, single LLM call |
| Connections required | None — operates on input text only |
| Context required | User facts (for owner-name resolution against contact list) |

### Generated spec

```yaml
skill_id: extract-action-items
version: 0.1.0
display_name: Extract Action Items from Meeting
summary: Pull explicit action items, owners, and due dates from a meeting transcript.

action_class: 1
tier_recommendation: fast-path
single_responsibility_assertion: |
  Extract action items from a meeting transcript.

input_schema:
  type: object
  required: [transcript]
  properties:
    transcript:
      type: string
      description: Full meeting transcript text
    meeting_date:
      type: string
      format: date
      description: Date of the meeting (used to resolve relative due dates)
  additionalProperties: false

output_schema:
  type: object
  required: [action_items]
  properties:
    action_items:
      type: array
      items:
        type: object
        required: [action, owner]
        properties:
          action:
            type: string
            description: The action item, as a directive
          owner:
            type: string
            description: Person responsible, or null if unclear
          due_date:
            type: string
            format: date
            nullable: true
            description: Due date if explicitly stated, otherwise null
  additionalProperties: false

context_requirements:
  - user_facts

connection_requirements: []

cost_class: low

failure_modes:
  - failure_id: no_action_items_found
    trigger_condition: Transcript contains no statements with action verbs directed at named individuals
    platform_response: return empty array; do not fabricate
    user_message: "I didn't find any clear action items in this transcript."

  - failure_id: ambiguous_owner
    trigger_condition: Action verb is present but no owner is named or inferable from context
    platform_response: include item with owner = null; flag in audit log
    user_message: "One or more items don't have a clear owner — want me to ask?"

  - failure_id: transcript_too_long
    trigger_condition: Transcript exceeds context budget after compression
    platform_response: process in segments; merge results; flag any merge ambiguity
    user_message: "This transcript is long — I processed it in segments. Double-check items near the segment boundaries."
```

### Reviewer checklist pre-pass

| # | Check | Status | Notes |
|---|---|---|---|
| 1 | Single-responsibility | ✅ | One verb, one object |
| 2 | Action class | ✅ | Class 1 matches behavior (read-only) |
| 3 | Tier | ✅ | Fast-path consistent with Class 1 + low ambiguity |
| 4 | Input schema strict | ✅ | `additionalProperties: false` |
| 5 | Output schema deterministic | ✅ | Single shape |
| 6 | Context minimal | ✅ | Only `user_facts` declared, used for owner resolution |
| 7 | Connections minimal | ✅ | None required |
| 8 | Cost projection | ✅ | Low — single LLM call on text input |
| 9 | Failure modes | ✅ | Three modes covering input, context, output sides |
| 10 | No constraint violations | ✅ | None |
| 11 | Anti-pattern check | ✅ | No flags |

### Honest risks

A transcript containing sensitive data (e.g., medical, legal-privileged) would still surface to the model before a sensitivity-detection layer could fire. If your platform processes such transcripts, gate this skill behind an upstream classifier or restrict context to non-sensitive transcripts.

The owner-resolution heuristic depends on `user_facts` being populated. On first use (cold-start), expect higher rates of `ambiguous_owner`.

---

## Example 2 — Generate skill (Class 2)

### User input

> *"Spec out a skill that drafts a follow-up email after a sales call."*

### Interview summary

| Step | Skill Architect's classification |
|---|---|
| Single-responsibility test | ✅ Pass — one verb (draft), one object (follow-up email). Note: drafting is Class 2; sending would be Class 4. This skill stops at draft. |
| Action class | Class 2 (Generate) — creates content that stays internal until explicitly sent |
| Tier recommendation | Standard — Class 2 with moderate ambiguity (call summary may be unstructured) |
| Connections required | None — operates on input + context only |
| Context required | User facts (sender's name, tone), preferences (formality), usage history (prior emails to this recipient if available) |

### Generated spec

```yaml
skill_id: draft-followup-email
version: 0.1.0
display_name: Draft Follow-up Email
summary: Draft a follow-up email based on a sales call summary, recipient, and desired call-to-action.

action_class: 2
tier_recommendation: standard
single_responsibility_assertion: |
  Draft a follow-up email from a call summary.

input_schema:
  type: object
  required: [call_summary, recipient_name, desired_outcome]
  properties:
    call_summary:
      type: string
      description: Plain-language summary of what was discussed
    recipient_name:
      type: string
      description: Recipient's name, used for salutation and tone calibration
    recipient_email:
      type: string
      format: email
      description: Email address (optional — used for context only, not for sending)
    desired_outcome:
      type: string
      description: One-sentence statement of what the email should accomplish (e.g., "schedule next meeting", "share contract for review", "answer their pricing question")
    deadline:
      type: string
      format: date
      nullable: true
      description: Date by which a response is needed, if any
  additionalProperties: false

output_schema:
  type: object
  required: [subject, body]
  properties:
    subject:
      type: string
      description: Subject line, ≤ 80 characters
    body:
      type: string
      description: Email body, plain text or markdown
    suggested_call_to_action:
      type: string
      description: The CTA the email leads to
  additionalProperties: false

context_requirements:
  - user_facts
  - user_preferences
  - usage_history

connection_requirements: []

cost_class: medium

failure_modes:
  - failure_id: ambiguous_outcome
    trigger_condition: desired_outcome is vague (e.g., "follow up") with no specific action implied
    platform_response: clarify before drafting
    user_message: "What specifically should this email accomplish? (book a meeting / share materials / answer a question / something else)"

  - failure_id: tone_mismatch
    trigger_condition: User preferences indicate formal tone but call summary suggests an informal relationship (or vice versa)
    platform_response: draft using the explicit user preference; flag the mismatch in output for user review
    user_message: "Drafted in the formal tone you've set, though the call sounded informal — feel free to dial it down."

  - failure_id: prior_email_drift
    trigger_condition: Usage history shows multiple prior emails to this recipient with inconsistent voice
    platform_response: draft in the most recent voice; surface the inconsistency
    user_message: "Your prior emails to this person varied in tone — I matched the most recent. Want a different feel?"
```

### Reviewer checklist pre-pass

| # | Check | Status | Notes |
|---|---|---|---|
| 1 | Single-responsibility | ✅ | Drafts only — does not send |
| 2 | Action class | ✅ | Class 2 (Generate) — output stays internal |
| 3 | Tier | ✅ | Standard for Class 2 + moderate ambiguity |
| 4 | Input schema strict | ✅ | `additionalProperties: false` |
| 5 | Output schema deterministic | ✅ | Always `{subject, body, suggested_call_to_action}` |
| 6 | Context minimal | ⚠️ | Three context types declared — confirm `usage_history` is needed; could be a behavioral mode if rarely available |
| 7 | Connections minimal | ✅ | None |
| 8 | Cost projection | ✅ | Medium — context injection adds tokens |
| 9 | Failure modes | ✅ | Three modes, well-targeted |
| 10 | No constraint violations | ✅ | None |
| 11 | Anti-pattern check | ✅ | No flags. Note: stopping at draft (not bundling send) is correct — if user wants send, chain to a separate `send-email` skill. |

### Honest risks

Stopping at draft is correct, but users will sometimes expect "draft and send" in one step. The framework forces them to invoke a second skill to send — which is the right architectural choice but a small UX friction. Document in user-facing copy that drafting is a separate step from sending, by design, for safety.

---

## Example 3 — Privileged skill (Class 6)

### User input

> *"Write a skill that schedules a payment to a vendor."*

### Interview summary

| Step | Skill Architect's classification |
|---|---|
| Single-responsibility test | ✅ Pass — one verb (schedule), one object (payment) |
| Action class | Class 6 (Privileged) — financial transaction, automatic upgrade per Rule D in §1.1 |
| Tier recommendation | High-stakes — Class 6 always High-stakes per §2.1 |
| Connections required | API to a payment system — prefer official API, never browser automation for financial operations |
| Context required | User facts (paying entity), preferences (default approval threshold), safety log (prior flagged vendors or transactions) |

### Generated spec

```yaml
skill_id: schedule-vendor-payment
version: 0.1.0
display_name: Schedule Vendor Payment
summary: Schedule a payment to a known vendor for a specified amount and date.

action_class: 6
tier_recommendation: high-stakes
single_responsibility_assertion: |
  Schedule a payment to a vendor.

input_schema:
  type: object
  required: [vendor_id, amount, currency, scheduled_date]
  properties:
    vendor_id:
      type: string
      description: Vendor identifier from the user's known vendor list
    amount:
      type: number
      minimum: 0.01
      description: Payment amount, positive number
    currency:
      type: string
      pattern: ^[A-Z]{3}$
      description: ISO 4217 currency code (e.g., USD, EUR)
    scheduled_date:
      type: string
      format: date
      description: Date the payment should execute
    reference:
      type: string
      maxLength: 140
      description: Reference text for the payment (invoice number, etc.)
  additionalProperties: false

output_schema:
  type: object
  required: [scheduled, confirmation_id]
  properties:
    scheduled:
      type: boolean
      description: Whether the payment was successfully scheduled
    confirmation_id:
      type: string
      description: Unique ID for the scheduled payment (for cancellation or audit)
    estimated_settlement_date:
      type: string
      format: date
      description: When the payment is expected to settle
  additionalProperties: false

context_requirements:
  - user_facts
  - user_preferences
  - safety_log

connection_requirements:
  - api

cost_class: medium

# Conditional fields (Class 6)
financial_envelope_declaration:
  max_amount: 10000.00
  velocity_limit: 5_per_24h
  recipient_scope: known_vendors_only

failure_modes:
  - failure_id: vendor_not_in_known_list
    trigger_condition: vendor_id does not match an entry in the user's known vendor list
    platform_response: HARD BLOCK — escalate to user approval as a new-recipient case
    user_message: "I don't recognize this vendor. Add them to your approved list before I can schedule a payment."

  - failure_id: amount_exceeds_envelope
    trigger_condition: amount > financial_envelope_declaration.max_amount
    platform_response: HARD BLOCK — require explicit user approval with the specific amount
    user_message: "This payment exceeds your standing limit. I'll need a one-time approval before scheduling."

  - failure_id: velocity_breach
    trigger_condition: Payments scheduled in the last 24h would exceed velocity_limit
    platform_response: HARD BLOCK — require explicit approval and pause velocity for review
    user_message: "Several payments were scheduled recently. Pausing for a quick review — confirm to proceed."

  - failure_id: payment_api_unavailable
    trigger_condition: API connection fails or returns 5xx
    platform_response: do not retry silently; do not fall back to a lower-trust connection method
    user_message: "I couldn't reach the payment system. The payment was not scheduled. Try again or check the system status."

  - failure_id: scheduled_date_in_past
    trigger_condition: scheduled_date is before today
    platform_response: reject input
    user_message: "The date you gave me is in the past. What date should I use?"
```

### Reviewer checklist pre-pass

| # | Check | Status | Notes |
|---|---|---|---|
| 1 | Single-responsibility | ✅ | Schedules only — does not modify vendor records or send notifications |
| 2 | Action class | ✅ | Class 6 (Privileged) — financial, hard upgrade per Rule D |
| 3 | Tier | ✅ | High-stakes mandatory for Class 6 |
| 4 | Input schema strict | ✅ | `additionalProperties: false`, currency pattern enforced |
| 5 | Output schema deterministic | ✅ | Single shape |
| 6 | Context minimal | ✅ | Three context types, all needed for fraud detection and approval routing |
| 7 | Connections minimal | ✅ | API only — never browser automation for financial operations |
| 8 | Cost projection | ✅ | Medium — modest LLM use, real cost is the transaction itself |
| 9 | Failure modes | ✅ | Five modes, covering the most common high-stakes failure paths |
| 10 | No constraint violations | ✅ | Browser-automation excluded; financial envelope declared; velocity limit declared |
| 11 | Anti-pattern check | ✅ | No flags |

### Honest risks

This is the most consequential skill of the three. Three areas to watch:

**Velocity spoofing.** A user could intentionally split one large payment into many smaller ones below the per-transaction threshold. The velocity limit catches this, but the velocity window itself is a tunable parameter — review periodically against actual usage.

**Vendor list drift.** Adding a new vendor (a separate Class 4 or 6 operation) creates the precondition for this skill to run. If the add-vendor flow is too lenient, the safety properties of this skill leak.

**Cancellation path.** This skill schedules payments. A separate skill (`cancel-payment`) should exist for cancellation. Until both exist, users have a one-way street.

**Settlement risk.** `estimated_settlement_date` is best-effort. The actual settlement date depends on the payment system, the destination bank, and timing. Surface this caveat in the user-facing copy of any application that uses this skill.

---

## What these examples have in common

| Property | Why it matters |
|---|---|
| **Single verb, single object** | The single-responsibility rule kept each skill atomic |
| **Output shape is constant** | Same shape regardless of input variations — chains will work |
| **Failure modes are specific** | Each one names a trigger, a response, and a user message — no vague "something went wrong" |
| **Context is declared, not assumed** | Each skill names exactly the memory it reads |
| **Connections are least-privilege** | Skills declare the lowest connection level that works |
| **Risks are honest** | What could fail in production is named, not hidden |

These are the same patterns that prevent skill drift, sprawl, and breakage in any library. The framework is the value — the YAML is just the artifact.

---

## License

Examples are part of Skill Architect, MIT licensed.
Copyright © 2026 Paul Poulose ([@pjpoulose](https://github.com/pjpoulose)).
