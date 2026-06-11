# Morning Inbox Triage — Local Setup

True offload: this runs on the OP box each morning using your **local** Ollama.
Claude is not in the daily loop. Outlook is read via win32com (consistent with
the platform's existing email service), digest goes to Telegram `8042233389`.

Files in this folder:
- `slm_triage.py` — triage engine (classify → validate → priority → escalate)
- `run_morning_triage.py` — orchestrator (Outlook → triage → Telegram)
- `sample_emails.json` — fixture for `--dry-run`
- `_runs/` — dated `digest-*.txt` + `escalate-*.json` (created on each run)

---

## 1. One-time install (on the OP box)

```powershell
# local model
ollama pull qwen2.5:7b-instruct          # smaller: llama3.2:3b

# python deps
pip install requests pywin32
```

`requests` → Ollama call. `pywin32` → Outlook (win32com). Telegram uses stdlib only.

Outlook must be **open** when the job runs (same constraint as every other
email-dependent job — see PLATFORM_SERVICES.md §3). `TELEGRAM_BOT_TOKEN` is read
from env, falling back to `1.Projects/PULSE v2 — Sales & Ops Manager/.env`.

---

## 2. Verify before scheduling

```powershell
# logic only — no Outlook, Ollama, or network needed
python slm_triage.py --self-test

# full pipeline with the fixture; prints the Telegram message instead of sending
python run_morning_triage.py --dry-run

# real run, once, by hand (sends to Telegram)
python run_morning_triage.py --limit 20
```

If `--dry-run` shows the digest and the escalation list looks right, you're good.

---

## 3. Register in the platform

Wrap it in `run_job.py` so a failure Telegrams automatically and it appears in
`schedule_manifest.json` (per CLAUDE.md "Add a job"):

```powershell
python scripts/olympic_platform/run_job.py morning-inbox-triage --agent HAVEN -- ^
  python "3.Resources/17. Strategic Intelligence/_slm-triage/run_morning_triage.py" --limit 20
```

Then schedule that wrapped command in Task Scheduler for ~07:30 weekdays, set
importance in `agents/job_criticality.json`, and re-run `export_schtasks.ps1`.
(HAVEN owns inbox/HR-adjacent work — change the agent tag if you'd rather route
it elsewhere.)

Example schtask (adjust path to your run_job wrapper):

```powershell
schtasks /Create /TN "OP\morning-inbox-triage" /SC WEEKLY /D MON,TUE,WED,THU,FRI ^
  /ST 07:30 /TR "python ...run_job.py morning-inbox-triage --agent HAVEN -- python \"...\\run_morning_triage.py\" --limit 20"
```

---

## 4. The escalate loop (where Claude comes back in)

Each run drops `escalate-YYYY-MM-DD.json` — the short list that needs judgment.
That's the natural hand-back: open it in this project and say *"draft replies for
today's escalated emails"*, and Claude works only that list with your strategic-
intelligence context. The 80% the SLM cleared never costs a Claude call.

---

## 5. Tuning

- Too much escalating → raise `ESCALATE_CONFIDENCE` in `slm_triage.py` (e.g. 0.55).
- Junk slipping through → lower it, or sharpen the taxonomy in BOTH
  `slm_triage.py` and `inbox-manager-outlook/SKILL.md` (keep them identical).
- Obvious senders (couriers, newsletters) → short-circuit in Python before the
  SLM runs; cheaper and perfect. See spec §8.
- Run the one-week shadow comparison (spec §7) before trusting it unattended.
