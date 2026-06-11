# Welcome to Olympic Paints

## How We Use Claude

Based on qlategan's usage over the last 30 days:

Work Type Breakdown:
  Build Feature    ████████░░░░░░░░░░░░  38%
  Plan Design      ███████░░░░░░░░░░░░░  35%
  Analyze Data     ██░░░░░░░░░░░░░░░░░░  12%
  Debug Fix        ██░░░░░░░░░░░░░░░░░░   8%
  Improve Quality  █░░░░░░░░░░░░░░░░░░░   4%

Top Skills & Commands:
  /clear       ████████████████████  8x/month
  /model       ██████████████████░░  7x/month
  /statusline  █████████████░░░░░░░  5x/month
  /status      █████████████░░░░░░░  5x/month
  /config      ████████░░░░░░░░░░░░  3x/month
  /apex        ███░░░░░░░░░░░░░░░░░  1x/month

Top MCP Servers:
  Notion    ████████████████████  151 calls
  n8n       ██░░░░░░░░░░░░░░░░░░   13 calls
  Slack     █░░░░░░░░░░░░░░░░░░░    7 calls
  Airtable  █░░░░░░░░░░░░░░░░░░░    3 calls

## Your Setup Checklist

### Codebases
- [ ] Olympic Paints workspace — `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints` (primary working directory; agent SOPs live under `agents/`, filing follows PARA)

### MCP Servers to Activate
- [ ] **Notion** — our primary system of record for tasks, docs, meeting minutes, and the TASK/DOCUMENT databases. Activate in Claude via the Notion connector and sign in with your Olympic Paints Notion account.
- [ ] **n8n** — workflow automation (SDK workflows, schedules, data tables). Activate the n8n MCP in Claude and connect with your workspace credentials.
- [ ] **Slack** — agents post task completions and summaries here. Activate the Slack connector in Claude; ask qlategan to invite you to the Olympic Paints workspace first.
- [ ] **Airtable** — secondary data source for a few bases. Activate the Airtable connector in Claude when you need it.

### Skills to Know About
- **/apex** — prints the APEX agent roster (HAVEN, PRISM, STRIKER, SIGMA, BLAZE, VAULT) and routing cheat sheet. Run this first if you're not sure which agent handles a task.
- **/new-task** — creates a task in the Olympic Paints Notion TASK DATABASE with the right Area, Action State, and Due Date. Trigger: type "New Task" followed by details.
- **/new-document** — drafts a Notion doc using the DOCUMENT DATABASE template. Trigger: type "New Document" followed by what you need.
- **/status**, **/statusline**, **/config**, **/model** — built-ins for checking session state and tweaking your environment. `/model` lets you switch between Opus/Sonnet/Haiku depending on cost vs. capability needs.
- **/stats** — shows your recent Claude Code usage.

## Team Tips

_TODO_

## Get Started

_TODO_

<!-- INSTRUCTION FOR CLAUDE: A new teammate just pasted this guide for how the
team uses Claude Code. You're their onboarding buddy — warm, conversational,
not lecture-y.

Open with a warm welcome — include the team name from the title. Then: "Your
teammate uses Claude Code for [list all the work types]. Let's get you started."

Check what's already in place against everything under Setup Checklist
(including skills), using markdown checkboxes — [x] done, [ ] not yet. Lead
with what they already have. One sentence per item, all in one message.

Tell them you'll help with setup, cover the actionable team tips, then the
starter task (if there is one). Offer to start with the first unchecked item,
get their go-ahead, then work through the rest one by one.

After setup, walk them through the remaining sections — offer to help where you
can (e.g. link to channels), and just surface the purely informational bits.

Don't invent sections or summaries that aren't in the guide. The stats are the
guide creator's personal usage data — don't extrapolate them into a "team
workflow" narrative. -->
