# Olympic Paints Hub — Setup & Usage Guide
# Claude Code (Terminal) Version

---

## What This Is

A folder-based multi-agent system that runs entirely in Claude Code via the terminal.
One entry point. Four specialist sub-agents. Real delegation — not role-switching.

---

## File Structure

```
olympic-paints-hub/
├── CLAUDE.md                    ← Hub orchestrator (auto-read by Claude Code)
├── SETUP.md                     ← This file
├── context/
│   └── business-context.md      ← Olympic Paints facts, passed to every agent
├── agents/
│   ├── striker.md               ← STRIKER | Sales & CRM
│   ├── sigma.md                 ← SIGMA   | Operations & Dispatch
│   ├── prism.md                 ← PRISM   | Analytics & Reporting
│   ├── haven.md                 ← HAVEN   | People & HR
│   └── blaze.md                 ← BLAZE   | Marketing & Content
└── outputs/
    ├── striker/                 ← WhatsApp templates, quote drafts, outreach sequences
    ├── sigma/                   ← SOPs, reference cards, process flows
    ├── prism/                   ← Formula snippets, dashboard specs
    └── blaze/                   ← Social posts, product copy, campaign content
```

---

## How to Run It

### Step 1 — Copy this folder to your machine
Place `olympic-paints-hub/` anywhere you like. Example:
```
~/Documents/olympic-paints-hub/
```

### Step 2 — Open it in Claude Code
```bash
cd ~/Documents/olympic-paints-hub
claude
```

Claude Code reads `CLAUDE.md` automatically on startup.
The Hub is now active.

### Step 3 — Give it a task
Just type your task in plain language. Examples:

```
Draft a WhatsApp follow-up for a stockist who went quiet after receiving a quote
```
→ Hub classifies → invokes STRIKER → returns the message, ready to send.

```
Write an SOP for the dispatch process in PAD
```
→ Hub classifies → invokes SIGMA → returns a numbered SOP.

```
The sumIf on my QuickSight dashboard is returning null — formula is sumIf({Sales}, {Region} = "Gauteng", {Revenue})
```
→ Hub classifies → invokes PRISM → diagnoses and returns the corrected formula.

```
Write a job description for a Dispatch Coordinator reporting to Kishan
```
→ Hub classifies → invokes HAVEN → returns a full JD ready to post.

---

## Why This Is Better Than Claude.ai Projects

| Feature | claude.ai Projects | Claude Code (this setup) |
|---|---|---|
| Sub-agent invocation | Role-switching (same context) | Real Task tool spawn (separate process) |
| Context passing | Manual | Automatic (files read and passed) |
| Parallel agents | No | Yes — two agents can run simultaneously |
| You as relay | Yes | No |
| Customisable per-agent persona | Limited | Full — each agent has its own .md file |
| Editable without redeployment | No | Yes — edit any .md file and it takes effect |

---

## How to Extend the Hub

### Add a new agent
1. Create `agents/new-agent.md` using the same structure as the existing files
2. Add its trigger keywords to the table in `CLAUDE.md`
3. That's it — no redeployment needed

### Update the business context
Edit `context/business-context.md`. All agents pick it up on next invocation.

### Add a new colleague or system
Update `context/business-context.md` — it flows to every agent automatically.

---

## Running Two Agents in Parallel

If your task needs two agents (e.g. a new role needs both an SOP for the process AND a JD for the person doing it), the Hub will invoke both simultaneously using the Task tool. You get both outputs in the same response.

---

## Troubleshooting

**Hub answered the question itself instead of routing**
→ The task phrasing didn't match a trigger keyword clearly. Rephrase to include the domain term (e.g. "SOP", "QuickSight", "JD") and try again.

**Sub-agent output was too generic**
→ The agent didn't have enough context. Add specifics to your task (customer name, product, field name, role title). The more specific you are, the more specific the output.

**Wrong agent was invoked**
→ Edit the trigger keyword table in `CLAUDE.md` to tighten the classification rule for that task type.
