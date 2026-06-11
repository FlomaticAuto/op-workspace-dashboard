# SLM Email Triage — Build Spec

**Purpose:** Hand the *first-pass classification* of the OP Outlook inbox to a small, local model. The SLM tags every email (sender type, topic, priority, action). Claude only ever sees the small slice that genuinely needs judgment — drafting replies, disputes, compliance, anything ambiguous.

**Why this task:** the taxonomy is already fixed (it lives in `inbox-manager-outlook/SKILL.md`), the output is a fixed JSON shape, and the volume is daily. That is the exact profile an SLM handles well. It also keeps employee, client and pricing-adjacent email content on your own machine.

**Status:** draft v0.1 — 2026-06-09. Pairs with `inbox-manager-outlook` skill (payload v1.0).

---

## 1. Architecture

```
Outlook (M365 MCP)
      │  fetch latest N unread  (this stays as-is)
      ▼
  Python harness  ──►  local SLM (Ollama)  ──►  JSON per email
      │                                            │
      │   validate JSON + apply escalation rule    │
      ▼                                            ▼
  digest (LOW/MED + clean items)        ESCALATE list ──► Claude
   printed / WhatsApp / file              (drafting, judgment)
```

The SLM never sends email, never writes replies, never touches Outlook. It reads text and returns labels. Everything stateful stays in the Python harness. This is deliberate — it caps the blast radius of a wrong SLM call to "mislabelled in a digest", never "sent the wrong thing".

---

## 2. Model & runtime

Run locally via **Ollama** (simplest) or LM Studio.

| Need | Pick |
|---|---|
| Lightest, fast on CPU/modest GPU | `llama3.2:3b` or `gemma2:2b` |
| Better edge-case accuracy | `qwen2.5:7b-instruct` or `phi3.5` |

Start with **qwen2.5:7b-instruct** — it follows JSON-output instructions reliably, which matters more here than raw size. Drop to 3B only if latency hurts. (Check for newer small models when you build — this list reflects mid-2025.)

Force structured output with Ollama's `format: json` option so you get parseable JSON every call, not prose.

---

## 3. Taxonomy (mirror of the skill payload — keep in sync)

The SLM must use exactly these enums. Do not let it invent values.

**sender_type:** `Supplier | Client | Internal | Government | Finance | Recruitment | Other`

**category:** `Invoice/Payment | Purchase Order | Delivery/Logistics | Complaint/Dispute | Quote/Tender | HR/Recruitment | Compliance/Legal | Finance/Banking | Internal Comms | Marketing/Spam | Other`

**priority:** `URGENT | HIGH | MEDIUM | LOW` (rules below, first match wins)

**action:** `Action Required | FYI Only`

Priority rules (lifted from the skill so the SLM and Claude agree):
1. Subject contains urgent / overdue / final notice / legal / summons → URGENT
2. category = Complaint/Dispute → URGENT
3. category = Compliance/Legal → URGENT
4. category = Invoice/Payment with an amount → HIGH
5. category = Purchase Order from a Client → HIGH
6. category = Delivery/Logistics due today or overdue → HIGH
7. category in {Quote/Tender, Finance/Banking, HR/Recruitment} → MEDIUM
8. category = Internal Comms → LOW
9. category = Marketing/Spam → LOW
10. anything else → LOW

---

## 4. SLM system prompt (paste verbatim)

```
You are an email-classification engine for Olympic Paints. You do not write
replies. You do not take actions. You only read one email and return labels.

Return ONLY a JSON object, no prose, with exactly these keys:
{
  "sender_type": one of ["Supplier","Client","Internal","Government","Finance","Recruitment","Other"],
  "category":    one of ["Invoice/Payment","Purchase Order","Delivery/Logistics","Complaint/Dispute","Quote/Tender","HR/Recruitment","Compliance/Legal","Finance/Banking","Internal Comms","Marketing/Spam","Other"],
  "priority":    one of ["URGENT","HIGH","MEDIUM","LOW"],
  "action":      one of ["Action Required","FYI Only"],
  "confidence":  a number from 0.0 to 1.0,
  "reason":      one short sentence (max 15 words)
}

PRIORITY RULES — apply top to bottom, first match wins:
1. Subject has "urgent","overdue","final notice","legal","summons" -> URGENT
2. category == "Complaint/Dispute" -> URGENT
3. category == "Compliance/Legal" -> URGENT
4. category == "Invoice/Payment" with a money amount present -> HIGH
5. category == "Purchase Order" and sender_type == "Client" -> HIGH
6. category == "Delivery/Logistics" due today or overdue -> HIGH
7. category in {"Quote/Tender","Finance/Banking","HR/Recruitment"} -> MEDIUM
8. category == "Internal Comms" -> LOW
9. category == "Marketing/Spam" -> LOW
10. otherwise -> LOW

RULES:
- Internal = sender address ends in @olympicpaint.
- Government = any @sars.gov.za, municipality, labour dept, regulator.
- If you are unsure of category or sender_type, use "Other" and set confidence below 0.6.
- Never output a value outside the allowed lists. Never add keys. Never explain outside the JSON.
```

User message per email = a compact block:
```
FROM: {from_address}
SUBJECT: {subject}
DATE: {received}
BODY (first 1500 chars): {body_text}
```

Truncate the body to ~1500 chars — the labels rarely need more, and it keeps the SLM fast.

---

## 5. Escalate-to-Claude rule

An email goes to the Claude pile if **any** of these is true:

1. `action == "Action Required"` **and** `priority` in {URGENT, HIGH} — needs a real reply.
2. `category` in {Complaint/Dispute, Compliance/Legal} — always, regardless of confidence. These carry legal/relationship risk; Claude reads them in full with the strategic-intelligence context.
3. `confidence < 0.65` — the SLM isn't sure; don't trust a low-confidence label.
4. JSON failed to parse, or any field is outside its enum (see §6).

Everything else (MEDIUM/LOW, FYI, clean high-confidence labels) stays in the SLM-only digest. No Claude call. That is where the cost saving comes from — on a typical day most mail is invoices, deliveries, newsletters and internal notices that never need escalating.

Rough expected split: SLM handles ~80%, Claude sees ~20%. Tune the confidence threshold up if too much escalates, down if junk slips through.

---

## 6. Validation & fallback (in the harness, not the model)

Never trust the SLM blindly — this is the safety net the task needs.

- Parse the JSON. If it fails → escalate that email to Claude, log it.
- Check every field is in its allowed enum. Any stray value → force `category="Other"`, `confidence=0.0` → escalates via rule 3.
- Re-derive `priority` in Python from the rules in §3 rather than trusting the model's priority field. The SLM picks `category`/`sender_type`/`action`; **Python computes priority deterministically.** This removes the single most error-prone judgment from the model.
- Log every classification (input + output) for a week so you can spot drift before trusting it unattended.

---

## 7. Rollout

1. **Shadow run.** For one week, let the SLM classify but have Claude also classify the same batch. Diff them. Anywhere they disagree is a rule to sharpen or a case to escalate.
2. **Cut over.** Once agreement is comfortable (say >90% on category, ~100% on the escalate/don't-escalate decision), make the SLM the default first pass and Claude handle only the escalate pile.
3. **Maintain.** When the taxonomy changes, edit it in **one** place — keep this spec and the skill payload identical. Drift between them is the main failure mode.

---

## 8. Honest caveats

- `priority` is deterministic — compute it in code, not the model. Half of "classification" here is really just rules.
- SLMs drift on edge cases (a complaint phrased politely, an invoice with no number). The validation net and the shadow week exist for exactly this.
- If a category turns out to be almost always rule-decidable from the sender address (e.g. a courier noreply), short-circuit it in Python before the SLM ever runs. Cheaper and perfect.
```
