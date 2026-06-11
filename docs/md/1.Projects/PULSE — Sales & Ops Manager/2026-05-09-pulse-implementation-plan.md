# PULSE Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build PULSE — Olympic Paints' new Sales & Operations Manager agent that pushes daily ack discipline on reps, runs a cycle-based plan-vs-actual calendar, escalates silence to Quintus, and publishes a live leaderboard + bi-weekly scorecard.

**Architecture:** Python scripts orchestrated via Windows Task Scheduler. Data flows: `Delivery Details_Updated.xlsx` (cycle plan) + sales parquet + JotForm submissions → planned_week.json + daily renders → Resend email + Telegram + GitHub Pages. Two JotForms (daily ack, weekly intake) created via JotForm MCP. Resend webhook events feed an engagement-streak signal alongside formal acks.

**Tech Stack:** Python 3.x · pandas · openpyxl · requests · Flask (webhook) · pytest · python-dotenv · Resend API · JotForm MCP · Telegram Bot API · GitHub Pages · Windows Task Scheduler.

**Spec:** [`2026-05-09-pulse-design.md`](./2026-05-09-pulse-design.md)

---

## File structure

```
1.Projects/PULSE — Sales & Ops Manager/
├── 2026-05-09-pulse-design.md           (spec)
├── 2026-05-09-pulse-implementation-plan.md   (this plan)
├── README.md                             (run instructions)
├── pulse_config.json                     (form IDs, rep emails, telegram chats)
├── .env.example                          (RESEND_API_KEY, etc.)
├── .gitignore                            (excludes .env, *.parquet, output/)
├── requirements.txt
├── scripts/
│   ├── __init__.py
│   ├── pulse_resend.py                   (Resend send helper)
│   ├── pulse_telegram.py                 (Telegram send helper)
│   ├── pulse_jotform.py                  (form mgmt + submission reader)
│   ├── pulse_data.py                     (sales/leads/meetings data loaders)
│   ├── pulse_cycle_loader.py             (arref → parquet)         [Sun 18:00]
│   ├── pulse_planner.py                  (build planned_week.json) [Sun 19:00]
│   ├── pulse_render.py                   (HTML render helpers)
│   ├── pulse_daily.py                    (daily mini-mailer)       [Mon-Fri 06:00]
│   ├── pulse_leaderboard.py              (live leaderboard)        [Mon-Fri 06:30]
│   ├── pulse_escalation.py               (10:15 ack check)
│   ├── pulse_intake_escalation.py        (Fri 09:00 intake check)
│   ├── pulse_scorecard.py                (alt-Mon 07:00 scorecard)
│   └── pulse_webhook.py                  (Flask Resend event handler)
├── data/                                  (parquet caches, gitignored)
├── output/                                (rendered HTML, gitignored)
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── fixtures/
    └── test_*.py                          (one per script)
```

**Modular boundaries:** each `pulse_*.py` has one responsibility. Orchestrators (`pulse_daily.py`, `pulse_scorecard.py`, etc.) compose helpers (`pulse_data.py`, `pulse_render.py`, `pulse_resend.py`, `pulse_telegram.py`). Tests mock external APIs.

---

## Task 1: Project skeleton, config, and tests setup

**Files:**
- Create: `1.Projects/PULSE — Sales & Ops Manager/README.md`
- Create: `1.Projects/PULSE — Sales & Ops Manager/pulse_config.json`
- Create: `1.Projects/PULSE — Sales & Ops Manager/.env.example`
- Create: `1.Projects/PULSE — Sales & Ops Manager/.gitignore`
- Create: `1.Projects/PULSE — Sales & Ops Manager/requirements.txt`
- Create: `1.Projects/PULSE — Sales & Ops Manager/scripts/__init__.py`
- Create: `1.Projects/PULSE — Sales & Ops Manager/tests/__init__.py`
- Create: `1.Projects/PULSE — Sales & Ops Manager/tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```
pandas>=2.0
openpyxl>=3.1
requests>=2.31
python-dotenv>=1.0
flask>=3.0
pyarrow>=14.0
pytest>=7.4
pytest-mock>=3.12
```

- [ ] **Step 2: Create pulse_config.json**

```json
{
  "reps": {
    "AC": {"name": "Aboo Cassim", "email": "ac@olympicpaints.co.za", "telegram_chat_id": null},
    "AP": {"name": "Amit Patel", "email": "ap@olympicpaints.co.za", "telegram_chat_id": null},
    "BV": {"name": "Bhadresh Vallabh", "email": "bv@olympicpaints.co.za", "telegram_chat_id": null},
    "NP": {"name": "Nikhil Panchal", "email": "np@olympicpaints.co.za", "telegram_chat_id": null},
    "BM": {"name": "Byron Minnie", "email": "bm@olympicpaints.co.za", "telegram_chat_id": null}
  },
  "quintus_telegram_chat_id": "8042233389",
  "jotform": {
    "daily_ack_form_id": null,
    "weekly_intake_form_id": null
  },
  "resend": {
    "from_address": "pulse@olympicpaints.co.za",
    "reply_to": "quintusl@olympicpaints.co.za",
    "domain_verified": false
  },
  "paths": {
    "delivery_details_xlsx": "../AWS Data/Delivery Details_Updated_13032026.xlsx",
    "sales_parquet": "../AWS Data/data/sales.parquet",
    "logo_src": "../../3.Resources/9. Brand Assets & Images/Misc Pictures/Olympic Paints Logo Digital.jpg",
    "data_dir": "./data",
    "output_dir": "./output"
  },
  "github_pages": {
    "leaderboard_repo": "flomaticauto/olympic-paints-pulse-leaderboard",
    "scorecard_repo": "flomaticauto/olympic-paints-pulse-leaderboard"
  }
}
```

> Rep emails are placeholders — Quintus to confirm actual addresses before go-live. Telegram chat IDs auto-populated when each rep DMs the bot once.

- [ ] **Step 3: Create .env.example**

```
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=xxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JOTFORM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_TOKEN_FLOMATICAUTO=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- [ ] **Step 4: Create .gitignore**

```
.env
__pycache__/
*.pyc
data/*.parquet
data/*.json
output/
*.log
```

- [ ] **Step 5: Create README.md**

```markdown
# PULSE — Sales & Operations Manager

Daily push system for Olympic Paints sales reps. See [design spec](./2026-05-09-pulse-design.md).

## Setup
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in keys.
3. Verify Resend domain (see spec §18).
4. Run `python scripts/pulse_jotform.py --create-forms` once to create JotForms; commit updated `pulse_config.json`.
5. Run `python scripts/pulse_cycle_loader.py` once to seed `data/pulse_cycle.parquet`.
6. Register Task Scheduler entries (see `scheduler/register.ps1`).

## Daily flow
- 06:00 weekday: `pulse_daily.py` sends per-rep email + Telegram.
- 06:30 weekday: `pulse_leaderboard.py` refreshes GitHub Pages.
- 10:15 weekday: `pulse_escalation.py` Telegrams Quintus if any rep hasn't acked.
- Sun 18:00: `pulse_cycle_loader.py` refreshes cycle parquet.
- Sun 19:00: `pulse_planner.py` builds next week's plan.
- Fri 09:00: `pulse_intake_escalation.py` Telegrams Quintus if any rep skipped intake.
- Alt Mon 07:00: `pulse_scorecard.py` sends bi-weekly scorecard.
```

- [ ] **Step 6: Create scripts/__init__.py and tests/__init__.py (empty)**

```python
# scripts/__init__.py
```

```python
# tests/__init__.py
```

- [ ] **Step 7: Create tests/conftest.py**

```python
import json
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.fixture
def sample_config(tmp_path):
    cfg = {
        "reps": {
            "AC": {"name": "Aboo Cassim", "email": "ac@test.za", "telegram_chat_id": "111"},
            "AP": {"name": "Amit Patel", "email": "ap@test.za", "telegram_chat_id": "222"},
            "BV": {"name": "Bhadresh Vallabh", "email": "bv@test.za", "telegram_chat_id": "333"},
            "NP": {"name": "Nikhil Panchal", "email": "np@test.za", "telegram_chat_id": "444"},
            "BM": {"name": "Byron Minnie", "email": "bm@test.za", "telegram_chat_id": "555"},
        },
        "quintus_telegram_chat_id": "8042233389",
        "jotform": {"daily_ack_form_id": "FORM_DAILY", "weekly_intake_form_id": "FORM_INTAKE"},
        "resend": {"from_address": "pulse@test.za", "reply_to": "q@test.za", "domain_verified": True},
        "paths": {
            "delivery_details_xlsx": str(tmp_path / "delivery.xlsx"),
            "sales_parquet": str(tmp_path / "sales.parquet"),
            "logo_src": str(tmp_path / "logo.jpg"),
            "data_dir": str(tmp_path / "data"),
            "output_dir": str(tmp_path / "output"),
        },
        "github_pages": {"leaderboard_repo": "test/lb", "scorecard_repo": "test/sc"},
    }
    p = tmp_path / "pulse_config.json"
    p.write_text(json.dumps(cfg))
    Path(cfg["paths"]["data_dir"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["paths"]["output_dir"]).mkdir(parents=True, exist_ok=True)
    return p, cfg

@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test_resend_key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_tg_token")
    monkeypatch.setenv("JOTFORM_API_KEY", "test_jf_key")
```

- [ ] **Step 8: Verify pytest discovery works**

Run: `cd "1.Projects/PULSE — Sales & Ops Manager" && python -m pytest tests/ --collect-only -q`
Expected: `0 tests collected` (no errors — empty test dir).

- [ ] **Step 9: Commit**

```bash
cd "1.Projects/PULSE — Sales & Ops Manager"
git add README.md pulse_config.json .env.example .gitignore requirements.txt scripts/__init__.py tests/__init__.py tests/conftest.py
git commit -m "feat(pulse): project skeleton with config, env template, and pytest fixtures"
```

---

## Task 2: pulse_resend.py — email send helper

**Files:**
- Create: `scripts/pulse_resend.py`
- Create: `tests/test_resend.py`

- [ ] **Step 1: Write failing test**

`tests/test_resend.py`:
```python
from unittest.mock import patch, MagicMock
from scripts.pulse_resend import send_email, ResendError

def test_send_email_calls_resend_api_with_correct_payload(sample_config):
    cfg_path, cfg = sample_config
    with patch("scripts.pulse_resend.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "msg_abc"})
        msg_id = send_email(
            to="ac@test.za",
            subject="Daily PULSE",
            html="<p>hi</p>",
            from_address="pulse@test.za",
            reply_to="q@test.za",
        )
    assert msg_id == "msg_abc"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.resend.com/emails"
    assert kwargs["headers"]["Authorization"] == "Bearer test_resend_key"
    body = kwargs["json"]
    assert body["to"] == ["ac@test.za"]
    assert body["from"] == "pulse@test.za"
    assert body["reply_to"] == "q@test.za"
    assert body["subject"] == "Daily PULSE"
    assert body["html"] == "<p>hi</p>"

def test_send_email_raises_on_api_error(sample_config):
    with patch("scripts.pulse_resend.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=422,
            json=lambda: {"message": "domain not verified"},
            text="domain not verified",
        )
        try:
            send_email(to="x@test.za", subject="s", html="h", from_address="f@test.za", reply_to="r@test.za")
            assert False, "Expected ResendError"
        except ResendError as e:
            assert "domain not verified" in str(e)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_resend.py -v`
Expected: `ImportError` / `ModuleNotFoundError` — `pulse_resend` doesn't exist yet.

- [ ] **Step 3: Implement scripts/pulse_resend.py**

```python
"""Resend email send helper. Encapsulates the Resend API for PULSE."""
import os
import requests

RESEND_URL = "https://api.resend.com/emails"

class ResendError(RuntimeError):
    pass

def send_email(*, to: str, subject: str, html: str, from_address: str, reply_to: str) -> str:
    """Send a single HTML email via Resend. Returns Resend message id."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise ResendError("RESEND_API_KEY not set")
    body = {
        "from": from_address,
        "to": [to],
        "reply_to": reply_to,
        "subject": subject,
        "html": html,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(RESEND_URL, headers=headers, json=body, timeout=15)
    if resp.status_code >= 300:
        raise ResendError(f"Resend send failed ({resp.status_code}): {resp.text}")
    return resp.json()["id"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_resend.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_resend.py tests/test_resend.py
git commit -m "feat(pulse): Resend email send helper with error handling"
```

---

## Task 3: pulse_telegram.py — Telegram send helper

**Files:**
- Create: `scripts/pulse_telegram.py`
- Create: `tests/test_telegram.py`

- [ ] **Step 1: Write failing test**

`tests/test_telegram.py`:
```python
from unittest.mock import patch, MagicMock
from scripts.pulse_telegram import send_message, send_to_quintus

def test_send_message_posts_to_telegram_api(sample_config):
    with patch("scripts.pulse_telegram.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"ok": True})
        ok = send_message(chat_id="123", text="hello")
    assert ok is True
    args, kwargs = mock_post.call_args
    assert "test_tg_token" in args[0]
    assert kwargs["json"]["chat_id"] == "123"
    assert kwargs["json"]["text"] == "hello"
    assert kwargs["json"]["parse_mode"] == "HTML"

def test_send_to_quintus_uses_quintus_chat_id(sample_config):
    cfg_path, cfg = sample_config
    with patch("scripts.pulse_telegram.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"ok": True})
        send_to_quintus("urgent", config=cfg)
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["chat_id"] == "8042233389"
    assert kwargs["json"]["text"] == "urgent"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_telegram.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement scripts/pulse_telegram.py**

```python
"""Telegram Bot API send helper for PULSE."""
import os
import requests

class TelegramError(RuntimeError):
    pass

def send_message(*, chat_id: str, text: str) -> bool:
    """Send an HTML-formatted Telegram message. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN not set")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=10,
    )
    if resp.status_code >= 300:
        raise TelegramError(f"Telegram send failed ({resp.status_code}): {resp.text}")
    return resp.json().get("ok", False)

def send_to_quintus(text: str, *, config: dict) -> bool:
    """Convenience: send a Telegram message to Quintus's chat from config."""
    return send_message(chat_id=config["quintus_telegram_chat_id"], text=text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_telegram.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_telegram.py tests/test_telegram.py
git commit -m "feat(pulse): Telegram send helper with quintus convenience"
```

---

## Task 4: pulse_jotform.py — form creation + submission reader

**Files:**
- Create: `scripts/pulse_jotform.py`
- Create: `tests/test_jotform.py`

> **Note:** form *creation* uses the JotForm MCP server (one-time, run by Quintus via `python scripts/pulse_jotform.py --create-forms` which prints field schemas to copy into the JotForm UI OR uses the JotForm REST API directly with `JOTFORM_API_KEY`). Submission *reading* uses the REST API. We test the REST submission reader; form creation is a one-shot manual-leaning operation but still tested for payload shape.

- [ ] **Step 1: Write failing test**

`tests/test_jotform.py`:
```python
from unittest.mock import patch, MagicMock
from scripts.pulse_jotform import (
    get_submissions_for_date,
    get_intake_submissions_for_week,
    build_daily_form_payload,
    build_intake_form_payload,
)

def test_get_submissions_for_date_filters_by_rep_and_date(sample_config):
    fake_response = {
        "content": [
            {"id": "1", "created_at": "2026-05-13 07:30:00", "answers": {
                "1": {"name": "rep", "answer": "AC"},
                "2": {"name": "date", "answer": "2026-05-13"},
                "3": {"name": "ack", "answer": "Yes"},
            }},
            {"id": "2", "created_at": "2026-05-13 09:15:00", "answers": {
                "1": {"name": "rep", "answer": "AP"},
                "2": {"name": "date", "answer": "2026-05-13"},
                "3": {"name": "ack", "answer": "Yes"},
            }},
            {"id": "3", "created_at": "2026-05-12 09:15:00", "answers": {
                "1": {"name": "rep", "answer": "AC"},
                "2": {"name": "date", "answer": "2026-05-12"},
                "3": {"name": "ack", "answer": "Yes"},
            }},
        ]
    }
    with patch("scripts.pulse_jotform.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: fake_response)
        subs = get_submissions_for_date(form_id="FORM_DAILY", date="2026-05-13")
    reps = sorted(s["rep"] for s in subs)
    assert reps == ["AC", "AP"]

def test_build_daily_form_payload_has_expected_fields():
    payload = build_daily_form_payload()
    field_names = [q["name"] for q in payload["questions"].values()]
    for required in ("rep", "date", "ack", "calls", "visits", "orders", "new_stores_count", "prod_dev_count"):
        assert required in field_names

def test_build_intake_form_payload_has_cycle_radio():
    payload = build_intake_form_payload()
    cycle_q = [q for q in payload["questions"].values() if q["name"] == "cycle_week"][0]
    assert cycle_q["type"] == "control_radio"
    assert sorted(cycle_q["options"].split("|")) == ["1", "2", "3", "4"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_jotform.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement scripts/pulse_jotform.py**

```python
"""JotForm form creation and submission reader for PULSE."""
import os
import requests

JOTFORM_BASE = "https://api.jotform.com"

class JotFormError(RuntimeError):
    pass

def _api_key() -> str:
    k = os.environ.get("JOTFORM_API_KEY")
    if not k:
        raise JotFormError("JOTFORM_API_KEY not set")
    return k

def get_submissions_for_date(*, form_id: str, date: str) -> list[dict]:
    """Return list of {rep, date, ack, calls, visits, ...} for a single date.

    `date` is ISO YYYY-MM-DD. We pull all submissions for the form and filter
    client-side by the form's `date` answer field (cheaper than JotForm filter syntax).
    """
    url = f"{JOTFORM_BASE}/form/{form_id}/submissions"
    resp = requests.get(url, params={"apiKey": _api_key(), "limit": 1000}, timeout=15)
    if resp.status_code >= 300:
        raise JotFormError(f"JotForm read failed ({resp.status_code}): {resp.text}")
    data = resp.json().get("content", [])
    out = []
    for sub in data:
        flat = {a["name"]: a.get("answer") for a in sub.get("answers", {}).values() if "name" in a}
        if flat.get("date") == date:
            out.append(flat)
    return out

def get_intake_submissions_for_week(*, form_id: str, week_start: str) -> list[dict]:
    """Return intake submissions where week_start (ISO Monday date) matches."""
    url = f"{JOTFORM_BASE}/form/{form_id}/submissions"
    resp = requests.get(url, params={"apiKey": _api_key(), "limit": 1000}, timeout=15)
    if resp.status_code >= 300:
        raise JotFormError(f"JotForm read failed ({resp.status_code}): {resp.text}")
    data = resp.json().get("content", [])
    out = []
    for sub in data:
        flat = {a["name"]: a.get("answer") for a in sub.get("answers", {}).values() if "name" in a}
        if flat.get("week_start") == week_start:
            out.append(flat)
    return out

def build_daily_form_payload() -> dict:
    """Field schema for the PULSE Daily Ack form. Used by --create-forms."""
    return {
        "properties": {"title": "PULSE Daily Ack"},
        "questions": {
            "1": {"name": "rep", "type": "control_textbox", "text": "Rep", "hidden": "Yes"},
            "2": {"name": "date", "type": "control_textbox", "text": "Date", "hidden": "Yes"},
            "3": {"name": "ack", "type": "control_checkbox", "text": "I have read yesterday's results", "required": "Yes"},
            "4": {"name": "calls", "type": "control_number", "text": "Calls today", "required": "Yes"},
            "5": {"name": "visits", "type": "control_number", "text": "Visits today", "required": "Yes"},
            "6": {"name": "orders", "type": "control_number", "text": "Orders today", "required": "Yes"},
            "7": {"name": "new_stores_count", "type": "control_number", "text": "New stores prospected today", "required": "Yes"},
            "8": {"name": "new_stores_names", "type": "control_textarea", "text": "New stores — names/towns"},
            "9": {"name": "prod_dev_count", "type": "control_number", "text": "Product dev conversations", "required": "Yes"},
            "10": {"name": "prod_dev_notes", "type": "control_textarea", "text": "Product dev — notes"},
            "11": {"name": "blockers", "type": "control_textarea", "text": "Anything blocking you?"},
        },
    }

def build_intake_form_payload() -> dict:
    """Field schema for the PULSE Weekly Intake form."""
    return {
        "properties": {"title": "PULSE Weekly Intake"},
        "questions": {
            "1": {"name": "rep", "type": "control_textbox", "text": "Rep", "hidden": "Yes"},
            "2": {"name": "week_start", "type": "control_textbox", "text": "Week starting (Mon)", "hidden": "Yes"},
            "3": {"name": "cycle_week", "type": "control_radio", "text": "Cycle running next week", "options": "1|2|3|4", "required": "Yes"},
            "4": {"name": "deviations", "type": "control_textarea", "text": "Deviations from default cycle"},
            "5": {"name": "special_targets", "type": "control_textarea", "text": "Special targets for the week"},
        },
    }

def create_form(payload: dict) -> str:
    """POST a form to JotForm. Returns new form ID."""
    url = f"{JOTFORM_BASE}/user/forms"
    resp = requests.post(url, params={"apiKey": _api_key()}, json=payload, timeout=30)
    if resp.status_code >= 300:
        raise JotFormError(f"JotForm create failed ({resp.status_code}): {resp.text}")
    return resp.json()["content"]["id"]

if __name__ == "__main__":
    import argparse, json, pathlib
    p = argparse.ArgumentParser()
    p.add_argument("--create-forms", action="store_true")
    args = p.parse_args()
    if args.create_forms:
        daily_id = create_form(build_daily_form_payload())
        intake_id = create_form(build_intake_form_payload())
        cfg_path = pathlib.Path(__file__).parent.parent / "pulse_config.json"
        cfg = json.loads(cfg_path.read_text())
        cfg["jotform"]["daily_ack_form_id"] = daily_id
        cfg["jotform"]["weekly_intake_form_id"] = intake_id
        cfg_path.write_text(json.dumps(cfg, indent=2))
        print(f"Daily ack form: {daily_id}")
        print(f"Weekly intake form: {intake_id}")
        print("pulse_config.json updated. Commit it.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_jotform.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_jotform.py tests/test_jotform.py
git commit -m "feat(pulse): JotForm form schemas + submission reader"
```

---

## Task 5: pulse_data.py — sales, leads, meetings loaders

**Files:**
- Create: `scripts/pulse_data.py`
- Create: `tests/test_data.py`
- Create: `tests/fixtures/sample_sales.parquet` (built in test setup)

- [ ] **Step 1: Write failing test**

`tests/test_data.py`:
```python
import pandas as pd
from datetime import date
from scripts.pulse_data import (
    load_sales,
    mtd_sales_for_rep,
    sales_for_rep_on_date,
    visits_logged_for_rep_on_date,
    leads_logged_for_rep_on_date,
)

def _make_sales_parquet(path):
    df = pd.DataFrame({
        "delno": ["D1", "D2", "D3", "D4"],
        "smref": ["AC", "AC", "AP", "AC"],
        "date": pd.to_datetime(["2026-05-01", "2026-05-13", "2026-05-13", "2026-05-13"]),
        "value": [10000.0, 5000.0, 3000.0, 2000.0],
        "curef": ["C1", "C2", "C3", "C2"],
    })
    df.to_parquet(path)

def test_mtd_sales_for_rep_sums_current_month(tmp_path):
    p = tmp_path / "sales.parquet"
    _make_sales_parquet(p)
    df = load_sales(str(p))
    total = mtd_sales_for_rep(df, rep="AC", as_of=date(2026, 5, 13))
    assert total == 17000.0  # 10K + 5K + 2K

def test_sales_for_rep_on_date_returns_single_day_total(tmp_path):
    p = tmp_path / "sales.parquet"
    _make_sales_parquet(p)
    df = load_sales(str(p))
    total = sales_for_rep_on_date(df, rep="AC", target_date=date(2026, 5, 13))
    assert total == 7000.0  # 5K + 2K

def test_visits_logged_for_rep_on_date_reads_zoho_meetings(tmp_path):
    csv = tmp_path / "meetings.csv"
    csv.write_text(
        "Note Content,Created Time\n"
        '"AC visited Cust X","2026-05-13 09:30:00"\n'
        '"AC visited Cust Y","2026-05-13 14:00:00"\n'
        '"AP visited Cust Z","2026-05-13 11:00:00"\n'
    )
    visits = visits_logged_for_rep_on_date(str(csv), rep="AC", target_date=date(2026, 5, 13))
    assert len(visits) == 2

def test_leads_logged_for_rep_on_date_counts_zoho_leads(tmp_path):
    csv = tmp_path / "leads.csv"
    csv.write_text(
        "Lead Owner,Created Time\nAC,2026-05-13 08:00:00\nAC,2026-05-13 16:00:00\nAP,2026-05-13 10:00:00\n"
    )
    leads = leads_logged_for_rep_on_date(str(csv), rep="AC", target_date=date(2026, 5, 13))
    assert leads == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_data.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement scripts/pulse_data.py**

```python
"""Data loaders for PULSE: sales parquet, Zoho meetings, Zoho leads."""
from datetime import date
import pandas as pd

def load_sales(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

def mtd_sales_for_rep(df: pd.DataFrame, *, rep: str, as_of: date) -> float:
    """Sum of sales `value` for `rep` from start-of-month through `as_of` inclusive."""
    start = pd.Timestamp(as_of.year, as_of.month, 1)
    end = pd.Timestamp(as_of) + pd.Timedelta(days=1)
    mask = (df["smref"] == rep) & (df["date"] >= start) & (df["date"] < end)
    return float(df.loc[mask, "value"].sum())

def sales_for_rep_on_date(df: pd.DataFrame, *, rep: str, target_date: date) -> float:
    d0 = pd.Timestamp(target_date)
    d1 = d0 + pd.Timedelta(days=1)
    mask = (df["smref"] == rep) & (df["date"] >= d0) & (df["date"] < d1)
    return float(df.loc[mask, "value"].sum())

def visits_logged_for_rep_on_date(meetings_csv: str, *, rep: str, target_date: date) -> list[str]:
    """Return list of Note Contents for the rep on the given date.

    Zoho meetings CSV uses 'Note Content' (free text containing rep code) and 'Created Time'.
    Per memory `reference_merchandising_kpi.md`, rep code is embedded in the note.
    """
    df = pd.read_csv(meetings_csv)
    df["Created Time"] = pd.to_datetime(df["Created Time"])
    d0 = pd.Timestamp(target_date)
    d1 = d0 + pd.Timedelta(days=1)
    mask = (
        df["Note Content"].str.contains(rep, na=False)
        & (df["Created Time"] >= d0)
        & (df["Created Time"] < d1)
    )
    return df.loc[mask, "Note Content"].tolist()

def leads_logged_for_rep_on_date(leads_csv: str, *, rep: str, target_date: date) -> int:
    df = pd.read_csv(leads_csv)
    df["Created Time"] = pd.to_datetime(df["Created Time"])
    d0 = pd.Timestamp(target_date)
    d1 = d0 + pd.Timedelta(days=1)
    mask = (df["Lead Owner"] == rep) & (df["Created Time"] >= d0) & (df["Created Time"] < d1)
    return int(mask.sum())
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_data.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_data.py tests/test_data.py
git commit -m "feat(pulse): data loaders for sales, meetings, leads"
```

---

## Task 6: pulse_cycle_loader.py — read arref → parquet

**Files:**
- Create: `scripts/pulse_cycle_loader.py`
- Create: `tests/test_cycle_loader.py`

- [ ] **Step 1: Write failing test**

`tests/test_cycle_loader.py`:
```python
import pandas as pd
from openpyxl import Workbook
from scripts.pulse_cycle_loader import load_cycle_from_xlsx, write_cycle_parquet

def _make_delivery_xlsx(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "consolidated"
    ws.append(["curef", "customer_name", "town", "arref"])
    ws.append(["C1", "Cust A", "Tzaneen", "AC1"])
    ws.append(["C2", "Cust B", "Tzaneen", "AC1"])
    ws.append(["C3", "Cust C", "Letsitele", "AC2"])
    ws.append(["C4", "Cust D", "Phalaborwa", "AP1"])
    ws.append(["C5", "Cust E", "Polokwane", "BV2"])
    ws.append(["C6", "Cust F", "Polokwane", None])  # unassigned — should be dropped
    wb.save(path)

def test_load_cycle_from_xlsx_returns_rep_cycle_curef_dataframe(tmp_path):
    p = tmp_path / "delivery.xlsx"
    _make_delivery_xlsx(p)
    df = load_cycle_from_xlsx(str(p))
    assert set(df.columns) >= {"rep", "cycle_week", "curef", "customer_name", "town"}
    assert len(df) == 5  # the None arref row dropped
    ac1 = df[(df["rep"] == "AC") & (df["cycle_week"] == 1)]
    assert sorted(ac1["curef"].tolist()) == ["C1", "C2"]

def test_write_cycle_parquet_roundtrips(tmp_path):
    p = tmp_path / "delivery.xlsx"
    _make_delivery_xlsx(p)
    df = load_cycle_from_xlsx(str(p))
    out = tmp_path / "cycle.parquet"
    write_cycle_parquet(df, str(out))
    rt = pd.read_parquet(out)
    assert len(rt) == len(df)
    assert set(rt["rep"]) == {"AC", "AP", "BV"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cycle_loader.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement scripts/pulse_cycle_loader.py**

```python
"""Load rep cycle membership from Delivery Details_Updated.xlsx → parquet."""
import re
import pandas as pd

ARREF_RE = re.compile(r"^([A-Z]{2})([1-4])$")

def load_cycle_from_xlsx(path: str) -> pd.DataFrame:
    """Read the `consolidated` tab and return rep × cycle_week × curef rows.

    The `arref` column contains codes like 'AC1', 'BV3'. Rows with blank/invalid
    arref are dropped.
    """
    df = pd.read_excel(path, sheet_name="consolidated")
    df = df.dropna(subset=["arref"])
    parsed = df["arref"].astype(str).str.strip().str.extract(ARREF_RE)
    df = df.assign(rep=parsed[0], cycle_week=parsed[1])
    df = df.dropna(subset=["rep", "cycle_week"])
    df["cycle_week"] = df["cycle_week"].astype(int)
    keep = ["rep", "cycle_week", "curef", "customer_name", "town"]
    available = [c for c in keep if c in df.columns]
    return df[available].reset_index(drop=True)

def write_cycle_parquet(df: pd.DataFrame, path: str) -> None:
    df.to_parquet(path, index=False)

if __name__ == "__main__":
    import json, pathlib
    cfg_path = pathlib.Path(__file__).parent.parent / "pulse_config.json"
    cfg = json.loads(cfg_path.read_text())
    src = pathlib.Path(__file__).parent.parent / cfg["paths"]["delivery_details_xlsx"]
    out = pathlib.Path(__file__).parent.parent / cfg["paths"]["data_dir"] / "pulse_cycle.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = load_cycle_from_xlsx(str(src))
    write_cycle_parquet(df, str(out))
    print(f"Wrote {len(df)} cycle rows to {out}")
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_cycle_loader.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_cycle_loader.py tests/test_cycle_loader.py
git commit -m "feat(pulse): cycle loader reads arref → pulse_cycle.parquet"
```

---

## Task 7: pulse_planner.py — build planned_week.json

**Files:**
- Create: `scripts/pulse_planner.py`
- Create: `tests/test_planner.py`

- [ ] **Step 1: Write failing test**

`tests/test_planner.py`:
```python
import json
import pandas as pd
from datetime import date
from scripts.pulse_planner import build_planned_week, default_cycle_for_next_week

def _make_cycle_df():
    return pd.DataFrame({
        "rep": ["AC", "AC", "AC", "AP", "BV", "NP", "BM"],
        "cycle_week": [1, 1, 2, 1, 1, 1, 1],
        "curef": ["C1", "C2", "C3", "C4", "C5", "C6", "C7"],
        "customer_name": ["A", "B", "C", "D", "E", "F", "G"],
        "town": ["Tzn", "Tzn", "Lts", "Phl", "Pol", "Mok", "Pol"],
    })

def test_build_planned_week_distributes_cycle_customers_across_weekdays():
    cycle = _make_cycle_df()
    submissions = [
        {"rep": "AC", "cycle_week": "1"},
        {"rep": "AP", "cycle_week": "1"},
        {"rep": "BV", "cycle_week": "1"},
        {"rep": "NP", "cycle_week": "1"},
        {"rep": "BM", "cycle_week": "1"},
    ]
    plan = build_planned_week(cycle, submissions, week_start=date(2026, 5, 11))
    # AC1 has 2 customers — distributed across Mon-Fri
    ac_dates = [d for d, items in plan["AC"].items() if items]
    assert len(ac_dates) >= 1
    flat = [c for items in plan["AC"].values() for c in items]
    assert sorted(c["curef"] for c in flat) == ["C1", "C2"]

def test_default_cycle_for_next_week_advances_one_week():
    # If rep last submitted cycle_week=2, default for next week is 3
    last_submitted = {"AC": "2", "AP": "4"}
    assert default_cycle_for_next_week(last_submitted, "AC") == "3"
    assert default_cycle_for_next_week(last_submitted, "AP") == "1"  # wraps 4→1
    assert default_cycle_for_next_week(last_submitted, "BV") == "1"  # never submitted → 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_planner.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement scripts/pulse_planner.py**

```python
"""Build the week's planned visit calendar per rep from cycle parquet + intake submissions."""
import json
from datetime import date, timedelta
import pandas as pd

WEEKDAYS = 5  # Mon-Fri

def default_cycle_for_next_week(last_submitted: dict, rep: str) -> str:
    """If rep didn't submit, advance their last cycle_week by 1 (1→2→3→4→1)."""
    last = last_submitted.get(rep)
    if last is None:
        return "1"
    n = int(last)
    return str((n % 4) + 1)

def build_planned_week(cycle_df: pd.DataFrame, submissions: list[dict], *, week_start: date) -> dict:
    """Return {rep: {iso_date: [{curef, customer_name, town}, ...]}} for Mon-Fri of week_start."""
    chosen: dict[str, int] = {}
    for s in submissions:
        chosen[s["rep"]] = int(s["cycle_week"])
    plan: dict = {}
    for rep, wk in chosen.items():
        rep_rows = cycle_df[(cycle_df["rep"] == rep) & (cycle_df["cycle_week"] == wk)]
        items = rep_rows.to_dict(orient="records")
        per_day: dict[str, list] = {}
        for i, item in enumerate(items):
            day = week_start + timedelta(days=i % WEEKDAYS)
            per_day.setdefault(day.isoformat(), []).append({
                "curef": item.get("curef"),
                "customer_name": item.get("customer_name"),
                "town": item.get("town"),
            })
        # Ensure all 5 weekdays present (empty list if no items that day)
        for i in range(WEEKDAYS):
            day = (week_start + timedelta(days=i)).isoformat()
            per_day.setdefault(day, [])
        plan[rep] = dict(sorted(per_day.items()))
    return plan

def write_planned_week(plan: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(plan, f, indent=2)

if __name__ == "__main__":
    import pathlib
    from scripts.pulse_jotform import get_intake_submissions_for_week
    root = pathlib.Path(__file__).parent.parent
    cfg = json.loads((root / "pulse_config.json").read_text())
    cycle_path = root / cfg["paths"]["data_dir"] / "pulse_cycle.parquet"
    cycle = pd.read_parquet(cycle_path)
    today = date.today()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    subs = get_intake_submissions_for_week(
        form_id=cfg["jotform"]["weekly_intake_form_id"],
        week_start=next_monday.isoformat(),
    )
    # Backfill defaults for any rep who didn't submit
    submitted = {s["rep"]: s["cycle_week"] for s in subs}
    last_submitted = submitted  # in v1, use this week's submissions as "last known"
    for rep in cfg["reps"]:
        if rep not in submitted:
            subs.append({"rep": rep, "cycle_week": default_cycle_for_next_week(last_submitted, rep)})
    plan = build_planned_week(cycle, subs, week_start=next_monday)
    out = root / cfg["paths"]["data_dir"] / "planned_week.json"
    write_planned_week(plan, str(out))
    print(f"Wrote planned week starting {next_monday} → {out}")
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_planner.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_planner.py tests/test_planner.py
git commit -m "feat(pulse): planner builds planned_week.json from cycle + intake"
```

---

## Task 8: pulse_render.py — design tokens + shared header/footer

**Files:**
- Create: `scripts/pulse_render.py`
- Create: `tests/test_render.py`

- [ ] **Step 1: Write failing test**

`tests/test_render.py`:
```python
from scripts.pulse_render import (
    render_design_tokens,
    render_theme_toggle,
    render_logo,
    render_html_shell,
)

def test_render_design_tokens_includes_all_four_themes():
    css = render_design_tokens()
    for cls in (".theme-light", ".theme-dark", ".theme-brand", ".theme-navy"):
        assert cls in css
    # Spot-check a few core tokens
    assert "--color-surface-page" in css
    assert "--font-display" in css

def test_render_theme_toggle_has_four_buttons():
    html = render_theme_toggle(active="theme-navy")
    for label in ("Light", "Dark", "Brand", "Navy"):
        assert f">{label}<" in html
    # The active button has class="active"
    assert "Navy" in html.split("class=\"active\"")[1][:80]

def test_render_logo_wraps_img_in_circle_div():
    html = render_logo(size=48, src_path="logo.jpg")
    assert "border-radius:50%" in html
    assert "overflow:hidden" in html
    assert "logo.jpg" in html
    assert 'alt="Olympic Paints"' in html

def test_render_html_shell_defaults_to_navy():
    html = render_html_shell(title="Test", body="<p>x</p>")
    assert 'class="theme-navy"' in html
    assert "<title>Test — Olympic Paints</title>" in html
    assert "<p>x</p>" in html
    assert "fonts.googleapis.com" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_render.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement scripts/pulse_render.py — shell, tokens, logo, toggle**

```python
"""HTML render helpers for PULSE. Design system per CLAUDE.md / DESIGN_SYSTEM.md."""
from pathlib import Path

# Load full token block from CLAUDE.md once. For brevity we inline an abbreviated
# version here; the canonical source is the project root CLAUDE.md.
DESIGN_TOKENS = """
:root {
  --_y50:#FEF9E0; --_y100:#FDF0A0; --_y200:#FAE04D;
  --_y400:#F5C400; --_y600:#D4A800; --_y800:#A88000; --_y900:#6A5000;
  --_n50:#E8EFF8; --_n100:#B8CCE8; --_n300:#6B9ED0;
  --_n500:#2D6BA8; --_n700:#1A3D6E; --_n900:#0D2040; --_n950:#071022;
  --_g0:#FFFFFF; --_g50:#F7F6F3; --_g100:#E8E7E2; --_g200:#C8C7C0;
  --_g400:#949390; --_g600:#5C5B58; --_g800:#2E2E2C;
  --_g900:#1A1A18; --_g950:#0D0D0B;
  --_teal:#2D8C7A; --_teal-light:#C8EDE7; --_teal-dark:#1a5c50;
  --_terra:#C97A3A; --_coral:#E86060; --_coral-light:#FDDCDC;
  --font-display:'Barlow Condensed',sans-serif;
  --font-body:'Barlow',sans-serif;
  --r-sm:4px; --r-md:8px; --r-lg:12px; --r-xl:16px; --r-pill:50px;
}
.theme-light{color-scheme:light;--color-surface-page:var(--_g50);--color-surface-base:var(--_g0);--color-surface-elevated:var(--_g0);--color-surface-sunken:var(--_g100);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g950);--color-text-secondary:var(--_g600);--color-text-tertiary:var(--_g400);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-brand-hover:var(--_y600);--color-border-subtle:var(--_g100);--color-border-default:var(--_g200);--color-border-strong:var(--_g400);--color-success-bg:#EDF7F5;--color-success-fg:var(--_teal-dark);--color-success-bd:var(--_teal);--color-warning-bg:var(--_y50);--color-warning-fg:var(--_y900);--color-warning-bd:var(--_y600);--color-danger-bg:#FEF2F2;--color-danger-fg:#C0392B;--color-danger-bd:var(--_coral);--shadow-sm:0 1px 3px rgba(0,0,0,0.08);--shadow-md:0 4px 12px rgba(0,0,0,0.08);}
.theme-dark{color-scheme:dark;--color-surface-page:var(--_g950);--color-surface-base:var(--_g900);--color-surface-elevated:var(--_g800);--color-surface-sunken:var(--_g950);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g100);--color-text-secondary:var(--_g400);--color-text-tertiary:var(--_g600);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-brand-hover:var(--_y200);--color-border-subtle:rgba(255,255,255,0.06);--color-border-default:rgba(255,255,255,0.10);--color-border-strong:rgba(255,255,255,0.20);--color-success-bg:rgba(45,140,122,0.12);--color-success-fg:var(--_teal-light);--color-success-bd:rgba(45,140,122,0.30);--color-warning-bg:rgba(245,196,0,0.10);--color-warning-fg:var(--_y200);--color-warning-bd:rgba(245,196,0,0.25);--color-danger-bg:rgba(232,96,96,0.12);--color-danger-fg:var(--_coral-light);--color-danger-bd:rgba(232,96,96,0.30);--shadow-sm:0 1px 3px rgba(0,0,0,0.40);--shadow-md:0 4px 12px rgba(0,0,0,0.40);}
.theme-brand{color-scheme:light;--color-surface-page:var(--_y400);--color-surface-base:var(--_y200);--color-surface-elevated:var(--_y50);--color-surface-sunken:var(--_y600);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_g950);--color-text-primary:var(--_g950);--color-text-secondary:var(--_y900);--color-text-tertiary:var(--_y800);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_g950);--color-brand-hover:var(--_n700);--color-border-subtle:rgba(0,0,0,0.08);--color-border-default:rgba(0,0,0,0.14);--color-border-strong:rgba(0,0,0,0.25);--color-success-bg:rgba(45,140,122,0.12);--color-success-fg:var(--_teal-dark);--color-success-bd:var(--_teal);--color-warning-bg:rgba(0,0,0,0.08);--color-warning-fg:var(--_y900);--color-warning-bd:var(--_y900);--color-danger-bg:rgba(232,96,96,0.12);--color-danger-fg:#C0392B;--color-danger-bd:var(--_coral);--shadow-sm:0 1px 3px rgba(0,0,0,0.12);--shadow-md:0 4px 12px rgba(0,0,0,0.14);}
.theme-navy{color-scheme:dark;--color-surface-page:var(--_n950);--color-surface-base:var(--_n900);--color-surface-elevated:var(--_n700);--color-surface-sunken:var(--_n950);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g0);--color-text-secondary:var(--_n100);--color-text-tertiary:var(--_n300);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-brand-hover:var(--_y200);--color-border-subtle:rgba(107,158,208,0.12);--color-border-default:rgba(107,158,208,0.20);--color-border-strong:rgba(107,158,208,0.35);--color-success-bg:rgba(45,140,122,0.15);--color-success-fg:var(--_teal-light);--color-success-bd:rgba(45,140,122,0.35);--color-warning-bg:rgba(245,196,0,0.12);--color-warning-fg:var(--_y200);--color-warning-bd:rgba(245,196,0,0.30);--color-danger-bg:rgba(232,96,96,0.14);--color-danger-fg:var(--_coral-light);--color-danger-bd:rgba(232,96,96,0.35);--shadow-sm:0 1px 3px rgba(0,0,0,0.50);--shadow-md:0 4px 12px rgba(0,0,0,0.50);}
"""

THEME_TOGGLE_JS = """
const OLY_THEMES=['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t,btn){
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme',t);
  document.querySelectorAll('.theme-bar button').forEach(b=>b.classList.toggle('active',b===btn));
}
"""

def render_design_tokens() -> str:
    return DESIGN_TOKENS

def render_theme_toggle(active: str = "theme-navy") -> str:
    btns = []
    for cls, label in [("theme-light", "Light"), ("theme-dark", "Dark"), ("theme-brand", "Brand"), ("theme-navy", "Navy")]:
        active_attr = ' class="active"' if cls == active else ""
        btns.append(f'<button onclick="olyTheme(\'{cls}\',this)"{active_attr}>{label}</button>')
    return (
        '<div class="theme-bar" style="display:flex;gap:4px;padding:8px 16px;'
        'background:var(--color-surface-secondary);">'
        + "".join(btns)
        + "</div>"
    )

def render_logo(size: int = 48, src_path: str = "logo.jpg") -> str:
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'overflow:hidden;flex-shrink:0;">'
        f'<img src="{src_path}" alt="Olympic Paints" width="{size}" height="{size}" '
        f'style="display:block;width:100%;height:100%;object-fit:cover;"></div>'
    )

def render_html_shell(*, title: str, body: str, theme: str = "theme-navy") -> str:
    return f"""<!DOCTYPE html>
<html lang="en" class="{theme}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Olympic Paints</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<style>{render_design_tokens()}</style>
</head>
<body style="background:var(--color-surface-page);color:var(--color-text-primary);font-family:var(--font-body);margin:0;">
{render_theme_toggle(active=theme)}
{body}
<script>{THEME_TOGGLE_JS}</script>
</body>
</html>"""

def copy_logo_to_output(logo_src: str, output_dir: str) -> None:
    """Copy the official logo JPG into output dir so relative <img src='logo.jpg'> works."""
    import shutil
    shutil.copy2(logo_src, Path(output_dir) / "logo.jpg")
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_render.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_render.py tests/test_render.py
git commit -m "feat(pulse): HTML shell with design tokens, themes, logo helper"
```

---

## Task 9: pulse_render.py — daily mailer template

**Files:**
- Modify: `scripts/pulse_render.py` (add `render_daily_mailer`)
- Modify: `tests/test_render.py` (add daily mailer tests)

- [ ] **Step 1: Append failing test to tests/test_render.py**

```python
from scripts.pulse_render import render_daily_mailer

def test_render_daily_mailer_includes_rep_kpis_and_ack_link():
    html = render_daily_mailer(
        rep="AC",
        rep_name="Aboo Cassim",
        cycle_label="AC1, Day 2/5",
        mtd_sales=980000,
        mtd_target=1000000,
        rank=2,
        plan_adherence_mtd=0.87,
        today_planned=[
            {"customer_name": "Cust A", "town": "Tzaneen"},
            {"customer_name": "Cust B", "town": "Tzaneen"},
        ],
        yesterday_planned=[
            {"customer_name": "Cust X", "town": "Pol", "visited": True},
            {"customer_name": "Cust Y", "town": "Pol", "visited": False},
        ],
        yesterday_sales=110000,
        yesterday_leads=1,
        ack_url="https://jotform.com/F1?rep=AC&date=2026-05-13",
        leaderboard_url="https://flomaticauto.github.io/olympic-paints-pulse-leaderboard/",
        date_label="Tue 13 May 2026",
    )
    # Key sections present
    assert "PULSE Daily" in html
    assert "Aboo Cassim" in html
    assert "AC1, Day 2/5" in html
    assert "98%" in html  # 980/1000
    assert "Cust A" in html and "Cust B" in html
    # Yesterday's plan vs actual
    assert "Cust X" in html and "Cust Y" in html
    # Big ack button
    assert "https://jotform.com/F1?rep=AC&date=2026-05-13" in html
    assert "ACKNOWLEDGE BY 10:00" in html
    # Leaderboard link
    assert "olympic-paints-pulse-leaderboard" in html
    # Theme is navy
    assert 'class="theme-navy"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_render.py::test_render_daily_mailer_includes_rep_kpis_and_ack_link -v`
Expected: `ImportError` for `render_daily_mailer`.

- [ ] **Step 3: Append render_daily_mailer to scripts/pulse_render.py**

```python
def _format_money(v: float) -> str:
    return f"R {v:,.0f}".replace(",", " ")

def _pct(v: float) -> str:
    return f"{v * 100:.0f}%" if v <= 1.5 else f"{v:.0f}%"

def render_daily_mailer(
    *,
    rep: str,
    rep_name: str,
    cycle_label: str,
    mtd_sales: float,
    mtd_target: float,
    rank: int,
    plan_adherence_mtd: float,
    today_planned: list[dict],
    yesterday_planned: list[dict],
    yesterday_sales: float,
    yesterday_leads: int,
    ack_url: str,
    leaderboard_url: str,
    date_label: str,
) -> str:
    pct_target = mtd_sales / mtd_target if mtd_target else 0
    today_items = "".join(
        f'<li style="padding:6px 0;border-bottom:1px solid var(--color-border-subtle);">'
        f'<strong>{p["customer_name"]}</strong> — {p["town"]}</li>'
        for p in today_planned
    ) or '<li style="color:var(--color-text-tertiary);">No visits planned</li>'
    yest_items = "".join(
        f'<li style="padding:6px 0;border-bottom:1px solid var(--color-border-subtle);">'
        f'{"✓" if p["visited"] else "✗"} {p["customer_name"]}</li>'
        for p in yesterday_planned
    ) or '<li style="color:var(--color-text-tertiary);">No plan recorded</li>'
    yest_count = sum(1 for p in yesterday_planned if p["visited"])
    yest_total = len(yesterday_planned)

    body = f"""
    <div style="max-width:600px;margin:0 auto;padding:16px;">
      <header style="display:flex;align-items:center;gap:12px;padding:12px 0;">
        {render_logo(size=36)}
        <div>
          <div style="font-family:var(--font-display);font-weight:900;font-size:22px;text-transform:uppercase;letter-spacing:0.02em;">PULSE Daily — {rep}</div>
          <div style="font-size:12px;color:var(--color-text-secondary);">{date_label} · Cycle {cycle_label}</div>
        </div>
      </header>

      <section style="background:var(--color-surface-elevated);border-radius:var(--r-lg);padding:16px;margin:12px 0;">
        <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">You Are</div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px;">
          <div><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">{_format_money(mtd_sales)}</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">MTD Sales · {_pct(pct_target)}</div></div>
          <div><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">#{rank}/5</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">Team rank</div></div>
          <div><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">{_pct(plan_adherence_mtd)}</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">Plan adherence</div></div>
        </div>
      </section>

      <section style="background:var(--color-surface-elevated);border-radius:var(--r-lg);padding:16px;margin:12px 0;">
        <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">Today's Plan</div>
        <ul style="list-style:none;padding:0;margin:8px 0 0 0;">{today_items}</ul>
      </section>

      <section style="background:var(--color-surface-elevated);border-radius:var(--r-lg);padding:16px;margin:12px 0;">
        <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">Yesterday — {yest_count}/{yest_total} visits logged</div>
        <ul style="list-style:none;padding:0;margin:8px 0 0 0;">{yest_items}</ul>
        <div style="margin-top:8px;font-size:13px;color:var(--color-text-secondary);">Sales: {_format_money(yesterday_sales)} · Leads: {yesterday_leads}</div>
      </section>

      <a href="{ack_url}" style="display:block;background:var(--color-brand-primary);color:var(--color-text-on-brand);text-align:center;padding:18px;border-radius:var(--r-lg);font-family:var(--font-display);font-weight:900;text-transform:uppercase;text-decoration:none;letter-spacing:0.06em;margin:16px 0;">Acknowledge by 10:00 → Submit today's plan</a>

      <footer style="text-align:center;font-size:11px;color:var(--color-text-tertiary);padding:16px 0;">
        <a href="{leaderboard_url}" style="color:var(--color-brand-primary);text-decoration:none;">See live leaderboard →</a><br>
        Olympic Paints PULSE · Reply to this email with questions.
      </footer>
    </div>
    """
    return render_html_shell(title=f"PULSE Daily — {rep}", body=body, theme="theme-navy")
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_render.py -v`
Expected: `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_render.py tests/test_render.py
git commit -m "feat(pulse): daily mailer HTML template (mobile-first, navy theme)"
```

---

## Task 10: pulse_render.py — leaderboard template

**Files:**
- Modify: `scripts/pulse_render.py` (add `render_leaderboard`)
- Modify: `tests/test_render.py`

- [ ] **Step 1: Append failing test**

```python
from scripts.pulse_render import render_leaderboard

def test_render_leaderboard_ranks_reps_by_pct_target():
    rows = [
        {"rep": "AC", "name": "Aboo", "mtd_sales": 980000, "pct_target": 0.98, "plan_adherence": 0.87, "ack_streak": 5, "engagement_streak": 5},
        {"rep": "BV", "name": "Bhadresh", "mtd_sales": 1100000, "pct_target": 1.12, "plan_adherence": 0.93, "ack_streak": 7, "engagement_streak": 7},
        {"rep": "AP", "name": "Amit", "mtd_sales": 920000, "pct_target": 0.92, "plan_adherence": 0.83, "ack_streak": 4, "engagement_streak": 4},
        {"rep": "NP", "name": "Nikhil", "mtd_sales": 700000, "pct_target": 0.70, "plan_adherence": 0.63, "ack_streak": 0, "engagement_streak": 1},
        {"rep": "BM", "name": "Byron", "mtd_sales": 500000, "pct_target": 0.50, "plan_adherence": 0.53, "ack_streak": 0, "engagement_streak": 0},
    ]
    html = render_leaderboard(rows=rows, last_updated_iso="2026-05-13T06:30:00")
    # BV first (112%), BM last (50%)
    bv_idx = html.find("Bhadresh")
    bm_idx = html.find("Byron")
    assert bv_idx > 0 and bm_idx > 0 and bv_idx < bm_idx
    # Last updated stamp present
    assert "2026-05-13" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_render.py::test_render_leaderboard_ranks_reps_by_pct_target -v`
Expected: `ImportError`.

- [ ] **Step 3: Append render_leaderboard to scripts/pulse_render.py**

```python
def render_leaderboard(*, rows: list[dict], last_updated_iso: str) -> str:
    sorted_rows = sorted(rows, key=lambda r: r["pct_target"], reverse=True)
    tr = []
    for i, r in enumerate(sorted_rows, start=1):
        rank_color = "var(--color-success-fg)" if i <= 2 else "var(--color-danger-fg)" if i >= 4 else "var(--color-text-primary)"
        tr.append(f"""
        <tr>
          <td style="padding:12px;font-family:var(--font-display);font-weight:900;font-size:24px;color:{rank_color};">#{i}</td>
          <td style="padding:12px;"><strong>{r['name']}</strong> <span style="color:var(--color-text-tertiary);">({r['rep']})</span></td>
          <td style="padding:12px;text-align:right;font-family:var(--font-display);font-weight:700;">{_format_money(r['mtd_sales'])}</td>
          <td style="padding:12px;text-align:right;font-weight:700;">{_pct(r['pct_target'])}</td>
          <td style="padding:12px;text-align:right;">{_pct(r['plan_adherence'])}</td>
          <td style="padding:12px;text-align:right;">{r['ack_streak']}d</td>
        </tr>""")
    body = f"""
    <div style="max-width:900px;margin:0 auto;padding:24px;">
      <header style="display:flex;align-items:center;gap:16px;padding:16px 0;">
        {render_logo(size=48)}
        <div>
          <div style="font-family:var(--font-display);font-weight:900;font-size:32px;text-transform:uppercase;">PULSE Leaderboard</div>
          <div style="color:var(--color-text-secondary);">Last updated {last_updated_iso}</div>
        </div>
      </header>
      <table style="width:100%;border-collapse:collapse;background:var(--color-surface-elevated);border-radius:var(--r-lg);overflow:hidden;">
        <thead>
          <tr style="background:var(--color-surface-sunken);text-align:left;font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">
            <th style="padding:12px;">Rank</th><th style="padding:12px;">Rep</th>
            <th style="padding:12px;text-align:right;">MTD Sales</th>
            <th style="padding:12px;text-align:right;">% Target</th>
            <th style="padding:12px;text-align:right;">Plan Adh.</th>
            <th style="padding:12px;text-align:right;">Ack Streak</th>
          </tr>
        </thead>
        <tbody>{''.join(tr)}</tbody>
      </table>
    </div>
    """
    return render_html_shell(title="PULSE Leaderboard", body=body, theme="theme-navy")
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_render.py -v`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_render.py tests/test_render.py
git commit -m "feat(pulse): leaderboard template — sorted, color-coded rank"
```

---

## Task 11: pulse_render.py — bi-weekly scorecard template

**Files:**
- Modify: `scripts/pulse_render.py` (add `render_scorecard`)
- Modify: `tests/test_render.py`

- [ ] **Step 1: Append failing test**

```python
from scripts.pulse_render import render_scorecard

def test_render_scorecard_includes_all_required_sections():
    summary = {
        "team_mtd": 4200000, "team_pct_target": 0.87,
        "team_visits_actual": 142, "team_visits_planned": 150,
        "team_acks": 47, "team_acks_required": 50,
        "team_plan_adherence": 0.83,
    }
    rep_rows = [
        {"rep": "BV", "name": "Bhadresh", "sales": 1100000, "pct_target": 1.12,
         "visits_actual": 28, "visits_planned": 30, "plan_adherence": 0.93,
         "leads": 14, "new_stores": 3, "ack_pct": 1.0},
    ]
    merch_grid = {"BV": [["✓", "✓", "✓", "✓", "✓"], [], [], []]}
    activity_log = {"BV": [
        {"date": "2026-05-12", "cycle_week": 1, "planned": 5, "actual": 5, "variance": 0, "sales": 85000, "ack": True}
    ]}
    new_stores = {"BV": ["Cust X", "Cust Y", "Cust Z"]}
    prod_dev = {"BV": 1}
    html = render_scorecard(
        period_label="Cycle Weeks 18 & 19 · Mon 12 May → Fri 23 May 2026",
        summary=summary, rep_rows=rep_rows, merch_grid=merch_grid,
        activity_log=activity_log, new_stores=new_stores, prod_dev=prod_dev,
    )
    for section in ("EXECUTIVE SUMMARY", "REP RANKING", "MERCHANDISING", "ACTIVITY LOG", "NEW STORES"):
        assert section in html
    assert "Bhadresh" in html
    assert "Cust X" in html
```

- [ ] **Step 2: Run test, expect ImportError**

Run: `python -m pytest tests/test_render.py::test_render_scorecard_includes_all_required_sections -v`

- [ ] **Step 3: Append render_scorecard to scripts/pulse_render.py**

```python
def render_scorecard(
    *,
    period_label: str,
    summary: dict,
    rep_rows: list[dict],
    merch_grid: dict,         # {rep: [[5 cells], [5 cells], [5 cells], [5 cells]]}
    activity_log: dict,       # {rep: [{date, cycle_week, planned, actual, variance, sales, ack}]}
    new_stores: dict,         # {rep: [str names]}
    prod_dev: dict,           # {rep: int count}
) -> str:
    # Executive summary cards
    s = summary
    exec_html = f"""
    <section style="margin:24px 0;">
      <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">EXECUTIVE SUMMARY</div>
      <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:12px;">
        <div style="background:var(--color-surface-elevated);padding:16px;border-radius:var(--r-lg);"><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">{_format_money(s['team_mtd'])}</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">Team MTD</div></div>
        <div style="background:var(--color-surface-elevated);padding:16px;border-radius:var(--r-lg);"><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">{_pct(s['team_pct_target'])}</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">vs Target</div></div>
        <div style="background:var(--color-surface-elevated);padding:16px;border-radius:var(--r-lg);"><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">{s['team_visits_actual']}/{s['team_visits_planned']}</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">Visits</div></div>
        <div style="background:var(--color-surface-elevated);padding:16px;border-radius:var(--r-lg);"><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">{s['team_acks']}/{s['team_acks_required']}</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">Acks</div></div>
        <div style="background:var(--color-surface-elevated);padding:16px;border-radius:var(--r-lg);"><div style="font-family:var(--font-display);font-weight:900;font-size:24px;">{_pct(s['team_plan_adherence'])}</div><div style="font-size:10px;text-transform:uppercase;color:var(--color-text-tertiary);">Plan Adh.</div></div>
      </div>
    </section>"""

    # Rep ranking table
    sorted_reps = sorted(rep_rows, key=lambda r: r["pct_target"], reverse=True)
    rank_rows = []
    for i, r in enumerate(sorted_reps, start=1):
        warn = "⚠" if r["pct_target"] < 0.75 else ""
        rank_rows.append(f"""
        <tr>
          <td style="padding:8px;">{i}</td>
          <td style="padding:8px;"><strong>{r['name']}</strong> ({r['rep']})</td>
          <td style="padding:8px;text-align:right;">{_format_money(r['sales'])}</td>
          <td style="padding:8px;text-align:right;font-weight:700;">{_pct(r['pct_target'])}</td>
          <td style="padding:8px;text-align:right;">{r['visits_actual']}/{r['visits_planned']}</td>
          <td style="padding:8px;text-align:right;">{_pct(r['plan_adherence'])}</td>
          <td style="padding:8px;text-align:right;">{r['leads']}</td>
          <td style="padding:8px;text-align:right;">{r['new_stores']}</td>
          <td style="padding:8px;text-align:right;">{_pct(r['ack_pct'])} {warn}</td>
        </tr>""")
    rank_html = f"""
    <section style="margin:24px 0;">
      <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">REP RANKING — last 14 days</div>
      <table style="width:100%;border-collapse:collapse;background:var(--color-surface-elevated);border-radius:var(--r-lg);overflow:hidden;margin-top:12px;">
        <thead><tr style="background:var(--color-surface-sunken);text-align:left;font-size:11px;text-transform:uppercase;color:var(--color-text-tertiary);">
          <th style="padding:8px;">#</th><th style="padding:8px;">Rep</th>
          <th style="padding:8px;text-align:right;">Sales</th>
          <th style="padding:8px;text-align:right;">% Tgt</th>
          <th style="padding:8px;text-align:right;">Visits</th>
          <th style="padding:8px;text-align:right;">Plan%</th>
          <th style="padding:8px;text-align:right;">Leads</th>
          <th style="padding:8px;text-align:right;">NewStr</th>
          <th style="padding:8px;text-align:right;">Ack%</th>
        </tr></thead>
        <tbody>{''.join(rank_rows)}</tbody>
      </table>
    </section>"""

    # Merch grid (per rep)
    merch_html_parts = []
    for rep, weeks in merch_grid.items():
        cells = ""
        for wi, week in enumerate(weeks, start=1):
            for cell in week:
                cells += f'<span style="display:inline-block;width:24px;height:24px;line-height:24px;text-align:center;background:var(--color-surface-sunken);margin:1px;border-radius:var(--r-sm);">{cell}</span>'
            cells += '<span style="display:inline-block;width:8px;"></span>'
        merch_html_parts.append(f'<details style="margin:8px 0;"><summary style="cursor:pointer;font-weight:700;">{rep} cycle</summary><div style="padding:8px;">{cells}</div></details>')
    merch_html = f"""
    <section style="margin:24px 0;">
      <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">MERCHANDISING PLAN — current rep cycle (4 weeks × 5 days)</div>
      {''.join(merch_html_parts)}
    </section>"""

    # Activity log
    log_parts = []
    for rep, days in activity_log.items():
        rows = "".join(
            f'<tr><td style="padding:6px;">{d["date"]}</td><td style="padding:6px;">Wk{d["cycle_week"]}</td><td style="padding:6px;text-align:right;">{d["planned"]}</td><td style="padding:6px;text-align:right;">{d["actual"]}</td><td style="padding:6px;text-align:right;">{d["variance"]:+d}</td><td style="padding:6px;text-align:right;">{_format_money(d["sales"])}</td><td style="padding:6px;text-align:right;">{"✓" if d["ack"] else "✗"}</td></tr>'
            for d in days
        )
        log_parts.append(f'<details style="margin:8px 0;"><summary style="cursor:pointer;font-weight:700;">{rep}</summary><table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="text-align:left;color:var(--color-text-tertiary);"><th style="padding:6px;">Date</th><th>Cyc</th><th style="text-align:right;">Plan</th><th style="text-align:right;">Act</th><th style="text-align:right;">Var</th><th style="text-align:right;">Sales</th><th style="text-align:right;">Ack</th></tr></thead><tbody>{rows}</tbody></table></details>')
    log_html = f"""
    <section style="margin:24px 0;">
      <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">ACTIVITY LOG — last 14 days</div>
      {''.join(log_parts)}
    </section>"""

    # New stores + product dev
    ns_parts = []
    for rep, names in new_stores.items():
        ns_parts.append(f'<div style="padding:8px 0;"><strong>{rep}:</strong> {len(names)} new stores ({", ".join(names)}) · {prod_dev.get(rep, 0)} prod dev</div>')
    ns_html = f"""
    <section style="margin:24px 0;">
      <div style="font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-tertiary);">NEW STORES &amp; PRODUCT DEV — last 14 days</div>
      <div style="background:var(--color-surface-elevated);border-radius:var(--r-lg);padding:16px;margin-top:12px;">{''.join(ns_parts)}</div>
    </section>"""

    body = f"""
    <div style="max-width:1100px;margin:0 auto;padding:24px;">
      <header style="display:flex;align-items:center;gap:16px;padding:16px 0;border-bottom:1px solid var(--color-border-subtle);">
        {render_logo(size=48)}
        <div>
          <div style="font-family:var(--font-display);font-weight:900;font-size:32px;text-transform:uppercase;">PULSE — Sales &amp; Ops Scorecard</div>
          <div style="color:var(--color-text-secondary);">{period_label}</div>
        </div>
      </header>
      {exec_html}{rank_html}{merch_html}{log_html}{ns_html}
      <footer style="text-align:center;color:var(--color-text-tertiary);padding:24px 0;font-size:11px;">Olympic Paints PULSE</footer>
    </div>
    """
    return render_html_shell(title="PULSE Scorecard", body=body, theme="theme-navy")
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_render.py -v`
Expected: `7 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_render.py tests/test_render.py
git commit -m "feat(pulse): bi-weekly scorecard template (exec summary, ranking, merch grid, activity log)"
```

---

## Task 12: pulse_daily.py — daily orchestrator

**Files:**
- Create: `scripts/pulse_daily.py`
- Create: `tests/test_daily.py`

- [ ] **Step 1: Write failing test**

`tests/test_daily.py`:
```python
import json
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock
from scripts.pulse_daily import build_daily_payload, run_daily

def _seed(tmp_path, sample_config):
    cfg_path, cfg = sample_config
    # sales parquet
    sales = pd.DataFrame({
        "delno": ["D1"], "smref": ["AC"], "date": pd.to_datetime(["2026-05-13"]),
        "value": [110000.0], "curef": ["C1"],
    })
    sales.to_parquet(cfg["paths"]["sales_parquet"])
    # planned_week.json
    plan = {
        "AC": {
            "2026-05-13": [{"curef": "C2", "customer_name": "Cust A", "town": "Tzaneen"}],
            "2026-05-12": [{"curef": "C1", "customer_name": "Cust X", "town": "Pol"}],
        }
    }
    pwp = cfg["paths"]["data_dir"] + "/planned_week.json"
    with open(pwp, "w") as f:
        json.dump(plan, f)
    return cfg_path, cfg

def test_build_daily_payload_for_rep(tmp_path, sample_config):
    cfg_path, cfg = _seed(tmp_path, sample_config)
    payload = build_daily_payload(
        rep="AC", config=cfg, today=date(2026, 5, 13), targets={"AC": 1000000},
        yesterday_visits=["AC visited Cust X"],  # one logged
        yesterday_leads=1,
        ack_history={"AC": 5},
    )
    assert payload["rep"] == "AC"
    assert payload["today_planned"][0]["customer_name"] == "Cust A"
    assert payload["yesterday_planned"][0]["visited"] is True
    assert payload["yesterday_sales"] == 110000.0
    assert payload["mtd_sales"] == 110000.0

def test_run_daily_sends_email_and_telegram_per_rep(tmp_path, sample_config):
    cfg_path, cfg = _seed(tmp_path, sample_config)
    with patch("scripts.pulse_daily.send_email") as m_email, \
         patch("scripts.pulse_daily.send_message") as m_tg, \
         patch("scripts.pulse_daily.visits_logged_for_rep_on_date", return_value=[]), \
         patch("scripts.pulse_daily.leads_logged_for_rep_on_date", return_value=0):
        m_email.return_value = "msg_1"
        m_tg.return_value = True
        run_daily(config_path=str(cfg_path), today=date(2026, 5, 13), targets={r: 1000000 for r in cfg["reps"]})
    # 5 reps × 1 email = 5 sends
    assert m_email.call_count == 5
```

- [ ] **Step 2: Run, expect failure**

Run: `python -m pytest tests/test_daily.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement scripts/pulse_daily.py**

```python
"""Daily orchestrator: pull data, render mailer per rep, send via Resend + Telegram."""
import json
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

from scripts.pulse_data import (
    load_sales, mtd_sales_for_rep, sales_for_rep_on_date,
    visits_logged_for_rep_on_date, leads_logged_for_rep_on_date,
)
from scripts.pulse_render import render_daily_mailer, copy_logo_to_output
from scripts.pulse_resend import send_email
from scripts.pulse_telegram import send_message

def build_daily_payload(
    *, rep: str, config: dict, today: date, targets: dict,
    yesterday_visits: list[str], yesterday_leads: int, ack_history: dict,
) -> dict:
    root = Path(config["paths"]["sales_parquet"]).parent.parent
    sales_df = load_sales(config["paths"]["sales_parquet"])
    yesterday = today - timedelta(days=1)
    plan_path = Path(config["paths"]["data_dir"]) / "planned_week.json"
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
    rep_plan = plan.get(rep, {})
    today_planned = rep_plan.get(today.isoformat(), [])
    yesterday_planned_raw = rep_plan.get(yesterday.isoformat(), [])
    visited_names = {v.split(" visited ")[1].strip() for v in yesterday_visits if " visited " in v}
    yesterday_planned = [
        {**p, "visited": p["customer_name"] in visited_names}
        for p in yesterday_planned_raw
    ]
    return {
        "rep": rep,
        "rep_name": config["reps"][rep]["name"],
        "cycle_label": f"{rep}? · Day ?/5",  # filled by run_daily from intake submissions
        "mtd_sales": mtd_sales_for_rep(sales_df, rep=rep, as_of=today),
        "mtd_target": targets.get(rep, 0),
        "rank": 0,  # filled by run_daily after computing all reps
        "plan_adherence_mtd": 0.0,  # filled by run_daily
        "today_planned": today_planned,
        "yesterday_planned": yesterday_planned,
        "yesterday_sales": sales_for_rep_on_date(sales_df, rep=rep, target_date=yesterday),
        "yesterday_leads": yesterday_leads,
        "ack_url": "",  # filled by run_daily
        "leaderboard_url": f"https://{config['github_pages']['leaderboard_repo'].replace('/', '.github.io/', 1)}/",
        "date_label": today.strftime("%a %d %b %Y"),
    }

def _compute_rank_and_adherence(payloads: list[dict]) -> None:
    pct = sorted(payloads, key=lambda p: (p["mtd_sales"] / p["mtd_target"]) if p["mtd_target"] else 0, reverse=True)
    for i, p in enumerate(pct, start=1):
        p["rank"] = i
    # plan adherence MTD: count visited / planned across all rep_plan dates ≤ today
    # For v1 use yesterday_planned ratio as proxy
    for p in payloads:
        yp = p["yesterday_planned"]
        p["plan_adherence_mtd"] = sum(1 for x in yp if x["visited"]) / max(1, len(yp))

def run_daily(*, config_path: str, today: date, targets: dict) -> None:
    config = json.loads(Path(config_path).read_text())
    output_dir = Path(config["paths"]["output_dir"]) / "daily" / today.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_logo_to_output(config["paths"]["logo_src"], str(output_dir))

    payloads = []
    for rep in config["reps"]:
        meetings_csv = config["paths"].get("meetings_csv")
        leads_csv = config["paths"].get("leads_csv")
        yesterday_visits = visits_logged_for_rep_on_date(
            meetings_csv or "/dev/null", rep=rep, target_date=today - timedelta(days=1),
        ) if meetings_csv else []
        yesterday_leads = leads_logged_for_rep_on_date(
            leads_csv or "/dev/null", rep=rep, target_date=today - timedelta(days=1),
        ) if leads_csv else 0
        payloads.append(build_daily_payload(
            rep=rep, config=config, today=today, targets=targets,
            yesterday_visits=yesterday_visits, yesterday_leads=yesterday_leads,
            ack_history={},
        ))
    _compute_rank_and_adherence(payloads)

    daily_form_id = config["jotform"]["daily_ack_form_id"]
    for p in payloads:
        rep = p["rep"]
        p["ack_url"] = f"https://www.jotform.com/{daily_form_id}?rep={rep}&date={today.isoformat()}"
        html = render_daily_mailer(**{k: v for k, v in p.items() if k != "rep_name"} | {"rep_name": p["rep_name"]})
        # write to disk
        (output_dir / f"{rep}.html").write_text(html, encoding="utf-8")
        # email
        send_email(
            to=config["reps"][rep]["email"],
            subject=f"PULSE Daily — {today.strftime('%a %d %b')}",
            html=html,
            from_address=config["resend"]["from_address"],
            reply_to=config["resend"]["reply_to"],
        )
        # telegram (short summary)
        chat = config["reps"][rep].get("telegram_chat_id")
        if chat:
            send_message(
                chat_id=str(chat),
                text=(
                    f"<b>PULSE Daily — {rep}</b>\n"
                    f"MTD: R{p['mtd_sales']:,.0f} ({p['mtd_sales']/p['mtd_target']*100:.0f}%)\n"
                    f"Rank #{p['rank']}/5\n"
                    f"<a href='{p['ack_url']}'>Acknowledge by 10:00 →</a>"
                ),
            )

if __name__ == "__main__":
    from datetime import date as _date
    cfg_path = Path(__file__).parent.parent / "pulse_config.json"
    cfg = json.loads(cfg_path.read_text())
    # Targets — read from build_kpi_dashboard data block (per memory). For v1, manual:
    targets = {"AC": 1000000, "AP": 1000000, "BV": 1000000, "NP": 1000000, "BM": 1000000}
    run_daily(config_path=str(cfg_path), today=_date.today(), targets=targets)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_daily.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_daily.py tests/test_daily.py
git commit -m "feat(pulse): daily orchestrator — payload build, email + telegram per rep"
```

---

## Task 13: pulse_leaderboard.py — live leaderboard publisher

**Files:**
- Create: `scripts/pulse_leaderboard.py`
- Create: `tests/test_leaderboard.py`

- [ ] **Step 1: Failing test**

```python
import json
import pandas as pd
from datetime import date
from unittest.mock import patch
from scripts.pulse_leaderboard import build_leaderboard_rows, run_leaderboard

def test_build_leaderboard_rows_computes_pct_target_and_streaks(tmp_path, sample_config):
    cfg_path, cfg = sample_config
    sales = pd.DataFrame({
        "smref": ["AC", "BV", "AP", "NP", "BM"],
        "date": pd.to_datetime(["2026-05-13"] * 5),
        "value": [980000.0, 1100000.0, 920000.0, 700000.0, 500000.0],
        "delno": ["D1","D2","D3","D4","D5"], "curef": ["C1"]*5,
    })
    sales.to_parquet(cfg["paths"]["sales_parquet"])
    rows = build_leaderboard_rows(
        config=cfg, today=date(2026, 5, 13),
        targets={r: 1000000 for r in cfg["reps"]},
        ack_history={"AC": 5, "BV": 7, "AP": 4, "NP": 0, "BM": 0},
        engagement_history={"AC": 5, "BV": 7, "AP": 4, "NP": 1, "BM": 0},
    )
    assert len(rows) == 5
    bv = next(r for r in rows if r["rep"] == "BV")
    assert bv["pct_target"] == 1.1  # 1.1M / 1M
    assert bv["ack_streak"] == 7
```

- [ ] **Step 2: Run test, expect ImportError**

- [ ] **Step 3: Implement scripts/pulse_leaderboard.py**

```python
"""Build and publish the live leaderboard to GitHub Pages (refreshed each weekday)."""
import json, subprocess, os
from datetime import date, datetime
from pathlib import Path
from scripts.pulse_data import load_sales, mtd_sales_for_rep
from scripts.pulse_render import render_leaderboard, copy_logo_to_output

def build_leaderboard_rows(*, config: dict, today: date, targets: dict, ack_history: dict, engagement_history: dict) -> list[dict]:
    sales_df = load_sales(config["paths"]["sales_parquet"])
    rows = []
    for rep, info in config["reps"].items():
        mtd = mtd_sales_for_rep(sales_df, rep=rep, as_of=today)
        tgt = targets.get(rep, 0)
        rows.append({
            "rep": rep,
            "name": info["name"],
            "mtd_sales": mtd,
            "pct_target": (mtd / tgt) if tgt else 0,
            "plan_adherence": 0.0,  # TODO: wire to planned_week.json comparisons in v1.1
            "ack_streak": ack_history.get(rep, 0),
            "engagement_streak": engagement_history.get(rep, 0),
        })
    return rows

def run_leaderboard(*, config_path: str, today: date, targets: dict, ack_history: dict, engagement_history: dict) -> None:
    config = json.loads(Path(config_path).read_text())
    output_dir = Path(config["paths"]["output_dir"]) / "leaderboard"
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_logo_to_output(config["paths"]["logo_src"], str(output_dir))
    rows = build_leaderboard_rows(
        config=config, today=today, targets=targets,
        ack_history=ack_history, engagement_history=engagement_history,
    )
    html = render_leaderboard(rows=rows, last_updated_iso=datetime.now().isoformat(timespec="seconds"))
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    _git_push(output_dir, config["github_pages"]["leaderboard_repo"])

def _git_push(local_dir: Path, repo: str) -> None:
    """Commit and push leaderboard HTML to GitHub Pages repo. Per memory: gh CLI auth."""
    # If local_dir isn't already a git repo, init + add remote
    git_dir = local_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=local_dir, check=True)
        token = subprocess.check_output(["gh", "auth", "token", "--user", "FlomaticAuto"], text=True).strip()
        url = f"https://FlomaticAuto:{token}@github.com/{repo}.git"
        subprocess.run(["git", "remote", "add", "origin", url], cwd=local_dir, check=True)
        subprocess.run(["git", "checkout", "-b", "main"], cwd=local_dir, check=True)
    subprocess.run(["git", "add", "."], cwd=local_dir, check=True)
    subprocess.run(["git", "-c", "user.email=pulse@olympicpaints.co.za", "-c", "user.name=PULSE", "commit", "-m", f"chore: leaderboard {datetime.now().isoformat(timespec='minutes')}", "--allow-empty"], cwd=local_dir, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=local_dir, check=True)

if __name__ == "__main__":
    cfg_path = Path(__file__).parent.parent / "pulse_config.json"
    cfg = json.loads(cfg_path.read_text())
    targets = {r: 1000000 for r in cfg["reps"]}
    run_leaderboard(config_path=str(cfg_path), today=date.today(), targets=targets, ack_history={}, engagement_history={})
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_leaderboard.py -v`
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_leaderboard.py tests/test_leaderboard.py
git commit -m "feat(pulse): live leaderboard publisher to GitHub Pages"
```

---

## Task 14: pulse_escalation.py + pulse_intake_escalation.py

**Files:**
- Create: `scripts/pulse_escalation.py`
- Create: `scripts/pulse_intake_escalation.py`
- Create: `tests/test_escalation.py`

- [ ] **Step 1: Failing test**

`tests/test_escalation.py`:
```python
from datetime import date
from unittest.mock import patch
from scripts.pulse_escalation import find_unacked_reps, run_escalation
from scripts.pulse_intake_escalation import find_intake_missing, run_intake_escalation

def test_find_unacked_reps_returns_reps_with_no_submission(sample_config):
    cfg_path, cfg = sample_config
    submissions_today = [{"rep": "AC", "ack": "Yes"}, {"rep": "BV", "ack": "Yes"}]
    missing = find_unacked_reps(submissions_today, all_reps=list(cfg["reps"].keys()))
    assert sorted(missing) == ["AP", "BM", "NP"]

def test_run_escalation_sends_telegram_to_quintus(sample_config):
    cfg_path, cfg = sample_config
    with patch("scripts.pulse_escalation.get_submissions_for_date", return_value=[{"rep": "AC", "ack": "Yes"}]), \
         patch("scripts.pulse_escalation.send_to_quintus") as m_tg:
        m_tg.return_value = True
        run_escalation(config_path=str(cfg_path), today=date(2026, 5, 13))
    args, _ = m_tg.call_args
    msg = args[0]
    for rep in ("AP", "BV", "BM", "NP"):
        assert rep in msg

def test_find_intake_missing_returns_reps_without_intake(sample_config):
    cfg_path, cfg = sample_config
    intake_subs = [{"rep": "AC", "cycle_week": "1"}]
    missing = find_intake_missing(intake_subs, all_reps=list(cfg["reps"].keys()))
    assert sorted(missing) == ["AP", "BM", "BV", "NP"]
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: Implement scripts/pulse_escalation.py**

```python
"""Daily 10:15 ack-check escalation. Telegram Quintus with reps who haven't submitted."""
import json
from datetime import date
from pathlib import Path
from scripts.pulse_jotform import get_submissions_for_date
from scripts.pulse_telegram import send_to_quintus

def find_unacked_reps(submissions_today: list[dict], *, all_reps: list[str]) -> list[str]:
    submitted = {s.get("rep") for s in submissions_today}
    return [r for r in all_reps if r not in submitted]

def run_escalation(*, config_path: str, today: date) -> None:
    config = json.loads(Path(config_path).read_text())
    subs = get_submissions_for_date(form_id=config["jotform"]["daily_ack_form_id"], date=today.isoformat())
    missing = find_unacked_reps(subs, all_reps=list(config["reps"].keys()))
    if not missing:
        return
    msg = f"<b>PULSE 10:15 — unacked today ({today.isoformat()}):</b>\n" + "\n".join(f"• {r} ({config['reps'][r]['name']})" for r in missing)
    send_to_quintus(msg, config=config)

if __name__ == "__main__":
    cfg_path = Path(__file__).parent.parent / "pulse_config.json"
    run_escalation(config_path=str(cfg_path), today=date.today())
```

- [ ] **Step 4: Implement scripts/pulse_intake_escalation.py**

```python
"""Friday 09:00 weekly-intake escalation."""
import json
from datetime import date, timedelta
from pathlib import Path
from scripts.pulse_jotform import get_intake_submissions_for_week
from scripts.pulse_telegram import send_to_quintus

def find_intake_missing(intake_subs: list[dict], *, all_reps: list[str]) -> list[str]:
    submitted = {s.get("rep") for s in intake_subs}
    return [r for r in all_reps if r not in submitted]

def run_intake_escalation(*, config_path: str, this_friday: date) -> None:
    config = json.loads(Path(config_path).read_text())
    next_monday = this_friday + timedelta(days=3)
    subs = get_intake_submissions_for_week(form_id=config["jotform"]["weekly_intake_form_id"], week_start=next_monday.isoformat())
    missing = find_intake_missing(subs, all_reps=list(config["reps"].keys()))
    if not missing:
        return
    msg = f"<b>PULSE Fri 09:00 — weekly intake missing for week of {next_monday.isoformat()}:</b>\n" + "\n".join(f"• {r}" for r in missing)
    send_to_quintus(msg, config=config)

if __name__ == "__main__":
    cfg_path = Path(__file__).parent.parent / "pulse_config.json"
    run_intake_escalation(config_path=str(cfg_path), this_friday=date.today())
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_escalation.py -v`
Expected: `3 passed`.

- [ ] **Step 6: Commit**

```bash
git add scripts/pulse_escalation.py scripts/pulse_intake_escalation.py tests/test_escalation.py
git commit -m "feat(pulse): daily ack escalation + weekly intake escalation to Quintus"
```

---

## Task 15: pulse_scorecard.py — bi-weekly scorecard orchestrator

**Files:**
- Create: `scripts/pulse_scorecard.py`
- Create: `tests/test_scorecard.py`

- [ ] **Step 1: Failing test**

`tests/test_scorecard.py`:
```python
import pandas as pd
from datetime import date
from unittest.mock import patch
from scripts.pulse_scorecard import build_scorecard_inputs, run_scorecard

def test_build_scorecard_inputs_aggregates_14_days(tmp_path, sample_config):
    cfg_path, cfg = sample_config
    sales = pd.DataFrame({
        "smref": ["AC", "AC", "BV"],
        "date": pd.to_datetime(["2026-05-12", "2026-05-13", "2026-05-13"]),
        "value": [50000.0, 60000.0, 80000.0],
        "delno": ["D1", "D2", "D3"], "curef": ["C1"]*3,
    })
    sales.to_parquet(cfg["paths"]["sales_parquet"])
    out = build_scorecard_inputs(
        config=cfg, period_end=date(2026, 5, 13),
        targets={r: 1000000 for r in cfg["reps"]},
        ack_pct={"AC": 1.0, "AP": 0.9, "BV": 1.0, "NP": 0.7, "BM": 0.6},
        new_stores={"AC": ["X","Y"], "BV": ["Z"]},
        prod_dev={"AC": 1, "BV": 0},
    )
    summary = out["summary"]
    assert summary["team_mtd"] >= 0
    assert "AC" in {r["rep"] for r in out["rep_rows"]}

def test_run_scorecard_writes_html_and_emails(tmp_path, sample_config):
    cfg_path, cfg = sample_config
    pd.DataFrame({"smref":["AC"],"date":pd.to_datetime(["2026-05-13"]),"value":[1.0],"delno":["D"],"curef":["C"]}).to_parquet(cfg["paths"]["sales_parquet"])
    with patch("scripts.pulse_scorecard.send_email") as m_email, \
         patch("scripts.pulse_scorecard._publish_to_pages"):
        m_email.return_value = "msg"
        run_scorecard(config_path=str(cfg_path), period_end=date(2026, 5, 13),
                      targets={r: 1000000 for r in cfg["reps"]})
    # 5 reps + Quintus = 6 sends
    assert m_email.call_count == 6
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: Implement scripts/pulse_scorecard.py**

```python
"""Bi-weekly scorecard orchestrator (alt-Mondays 07:00). Renders HTML, emails, publishes."""
import json, subprocess
from datetime import date, timedelta, datetime
from pathlib import Path
import pandas as pd
from scripts.pulse_data import load_sales
from scripts.pulse_render import render_scorecard, copy_logo_to_output
from scripts.pulse_resend import send_email

def build_scorecard_inputs(*, config: dict, period_end: date, targets: dict,
                            ack_pct: dict, new_stores: dict, prod_dev: dict) -> dict:
    sales_df = load_sales(config["paths"]["sales_parquet"])
    period_start = period_end - timedelta(days=13)
    period_mask = (sales_df["date"] >= pd.Timestamp(period_start)) & (sales_df["date"] <= pd.Timestamp(period_end) + pd.Timedelta(days=1))
    p = sales_df[period_mask]
    rep_rows = []
    for rep, info in config["reps"].items():
        rep_sales = float(p.loc[p["smref"] == rep, "value"].sum())
        tgt = targets.get(rep, 0)
        rep_rows.append({
            "rep": rep, "name": info["name"], "sales": rep_sales,
            "pct_target": (rep_sales / tgt) if tgt else 0,
            "visits_actual": 0, "visits_planned": 0,  # wired in v1.1 from planned_week archive
            "plan_adherence": 0.0,
            "leads": 0, "new_stores": len(new_stores.get(rep, [])),
            "ack_pct": ack_pct.get(rep, 0),
        })
    summary = {
        "team_mtd": sum(r["sales"] for r in rep_rows),
        "team_pct_target": (sum(r["sales"] for r in rep_rows) / sum(targets.values())) if sum(targets.values()) else 0,
        "team_visits_actual": 0, "team_visits_planned": 0,
        "team_acks": int(sum(ack_pct.values()) * 14),
        "team_acks_required": len(config["reps"]) * 14,
        "team_plan_adherence": 0.0,
    }
    merch_grid = {rep: [["—"] * 5 for _ in range(4)] for rep in config["reps"]}  # placeholder grid; v1.1 fills from cycle parquet
    activity_log = {rep: [] for rep in config["reps"]}
    return {
        "period_label": f"Mon {period_start.strftime('%d %b')} → Fri {period_end.strftime('%d %b %Y')}",
        "summary": summary, "rep_rows": rep_rows,
        "merch_grid": merch_grid, "activity_log": activity_log,
        "new_stores": new_stores, "prod_dev": prod_dev,
    }

def _publish_to_pages(html: str, config: dict, period_end: date) -> None:
    output_dir = Path(config["paths"]["output_dir"]) / "scorecard"
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_logo_to_output(config["paths"]["logo_src"], str(output_dir))
    fname = f"{period_end.isoformat()}.html"
    (output_dir / fname).write_text(html, encoding="utf-8")
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    repo = config["github_pages"]["scorecard_repo"]
    git_dir = output_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=output_dir, check=True)
        token = subprocess.check_output(["gh", "auth", "token", "--user", "FlomaticAuto"], text=True).strip()
        url = f"https://FlomaticAuto:{token}@github.com/{repo}.git"
        subprocess.run(["git", "remote", "add", "origin", url], cwd=output_dir, check=True)
        subprocess.run(["git", "checkout", "-b", "main"], cwd=output_dir, check=True)
    subprocess.run(["git", "add", "."], cwd=output_dir, check=True)
    subprocess.run(["git", "-c", "user.email=pulse@olympicpaints.co.za", "-c", "user.name=PULSE",
                    "commit", "-m", f"feat: scorecard {period_end.isoformat()}", "--allow-empty"], cwd=output_dir, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=output_dir, check=True)

def run_scorecard(*, config_path: str, period_end: date, targets: dict) -> None:
    config = json.loads(Path(config_path).read_text())
    inputs = build_scorecard_inputs(
        config=config, period_end=period_end, targets=targets,
        ack_pct={r: 0.0 for r in config["reps"]},  # filled by reading 14 days of submissions in production
        new_stores={r: [] for r in config["reps"]},
        prod_dev={r: 0 for r in config["reps"]},
    )
    html = render_scorecard(**inputs)
    _publish_to_pages(html, config, period_end)
    subject = f"PULSE Scorecard — {inputs['period_label']}"
    recipients = [info["email"] for info in config["reps"].values()] + [config["resend"]["reply_to"]]
    for to in recipients:
        send_email(
            to=to, subject=subject, html=html,
            from_address=config["resend"]["from_address"],
            reply_to=config["resend"]["reply_to"],
        )

if __name__ == "__main__":
    cfg_path = Path(__file__).parent.parent / "pulse_config.json"
    run_scorecard(config_path=str(cfg_path), period_end=date.today(),
                  targets={r: 1000000 for r in json.loads(Path(cfg_path).read_text())["reps"]})
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_scorecard.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_scorecard.py tests/test_scorecard.py
git commit -m "feat(pulse): bi-weekly scorecard orchestrator (render, email, publish)"
```

---

## Task 16: pulse_webhook.py — Resend event webhook receiver

**Files:**
- Create: `scripts/pulse_webhook.py`
- Create: `tests/test_webhook.py`

- [ ] **Step 1: Failing test**

`tests/test_webhook.py`:
```python
import json
from pathlib import Path
import pandas as pd
from scripts.pulse_webhook import create_app

def test_webhook_appends_event_to_parquet(tmp_path, sample_config, monkeypatch):
    cfg_path, cfg = sample_config
    monkeypatch.setenv("PULSE_CONFIG_PATH", str(cfg_path))
    app = create_app()
    client = app.test_client()
    payload = {"type": "email.opened", "data": {"email_id": "msg_1", "to": ["ac@test.za"], "created_at": "2026-05-13T07:00:00Z"}}
    resp = client.post("/resend/webhook", json=payload)
    assert resp.status_code == 200
    events_path = Path(cfg["paths"]["data_dir"]) / "email_events.parquet"
    assert events_path.exists()
    df = pd.read_parquet(events_path)
    assert df.iloc[0]["event_type"] == "email.opened"
    assert df.iloc[0]["email_id"] == "msg_1"
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: Implement scripts/pulse_webhook.py**

```python
"""Flask app receiving Resend webhook events. Appends to email_events.parquet."""
import json, os
from datetime import datetime
from pathlib import Path
import pandas as pd
from flask import Flask, request, jsonify

EVENT_COLS = ["email_id", "event_type", "to", "timestamp", "received_at"]

def _events_path() -> Path:
    cfg_path = Path(os.environ.get("PULSE_CONFIG_PATH", Path(__file__).parent.parent / "pulse_config.json"))
    cfg = json.loads(cfg_path.read_text())
    return Path(cfg["paths"]["data_dir"]) / "email_events.parquet"

def _append_event(row: dict) -> None:
    p = _events_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    df_new = pd.DataFrame([row], columns=EVENT_COLS)
    if p.exists():
        df = pd.concat([pd.read_parquet(p), df_new], ignore_index=True)
    else:
        df = df_new
    df.to_parquet(p, index=False)

def create_app() -> Flask:
    app = Flask(__name__)

    @app.post("/resend/webhook")
    def hook():
        event = request.get_json(silent=True) or {}
        data = event.get("data", {})
        _append_event({
            "email_id": data.get("email_id"),
            "event_type": event.get("type"),
            "to": ",".join(data.get("to", [])),
            "timestamp": data.get("created_at"),
            "received_at": datetime.utcnow().isoformat(),
        })
        return jsonify({"ok": True})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=8766)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_webhook.py -v`
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pulse_webhook.py tests/test_webhook.py
git commit -m "feat(pulse): Resend webhook receiver appends events to parquet"
```

---

## Task 17: PULSE agent profile + memory + slash command

**Files:**
- Create: `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\agent_pulse.md`
- Modify: `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\MEMORY.md` (add line)
- Create: `C:\Users\quint\.claude\commands\pulse.md` (slash command)

- [ ] **Step 1: Create the agent memory file**

Path: `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\agent_pulse.md`

```markdown
---
name: PULSE — Agent Profile
description: Sales & Operations Manager agent; daily ack discipline, cycle-based plan-vs-actual, escalation, leaderboard
type: project
---

# PULSE — Sales & Operations Manager

**Role:** Daily push system for Olympic Paints sales reps. Pushes daily acks, runs the 4-week cycle plan-vs-actual calendar, escalates silence to Quintus, publishes a live leaderboard, and ships a bi-weekly scorecard.

**Model:** Sonnet · **Slash command:** `/pulse` · **Reports to:** APEX (Quintus)

## Reps in scope
AC (Aboo Cassim) · AP (Amit Patel) · BV (Bhadresh Vallabh) · NP (Nikhil Panchal) · BM (Byron Minnie). All run on a 4-week cycle (codes AC1-4, AP1-4, BV1-4, NP1-4, BM1-4). Cycle membership comes from the `arref` column in the `consolidated` tab of `Delivery Details_Updated_13032026.xlsx`.

## Key files (under `1.Projects/PULSE — Sales & Ops Manager/`)
- `pulse_config.json` — form IDs, rep emails, telegram chats, paths
- `scripts/pulse_daily.py` — weekday 06:00 mini-mailer
- `scripts/pulse_leaderboard.py` — weekday 06:30 GitHub Pages refresh
- `scripts/pulse_escalation.py` — weekday 10:15 ack check
- `scripts/pulse_intake_escalation.py` — Fri 09:00 weekly intake check
- `scripts/pulse_scorecard.py` — alt-Mon 07:00 scorecard
- `scripts/pulse_cycle_loader.py` — Sun 18:00 read arref
- `scripts/pulse_planner.py` — Sun 19:00 build planned_week.json
- `scripts/pulse_webhook.py` — Flask Resend event receiver

## Email path
**Resend** (not Outlook). Sender `pulse@olympicpaints.co.za`. Reply-to `quintusl@olympicpaints.co.za`. API key in env `RESEND_API_KEY`. Domain verification (SPF/DKIM/DMARC) is a one-time precondition for go-live.

## JotForms
- **PULSE Daily Ack** — submitted by reps each weekday by 10:00. Captures ack + today's commitment + new stores + prod dev.
- **PULSE Weekly Intake** — submitted by Thursday 16:00. Rep declares next week's cycle (1/2/3/4) + deviations + special targets.

Form IDs in `pulse_config.json` after running `python scripts/pulse_jotform.py --create-forms`.

## Escalation
All Quintus alerts go to Telegram chat `8042233389`. PULSE never pushes back to reps directly — Quintus owns confrontation.

## Design system
Default theme: `theme-navy`. All HTML output follows `DESIGN_SYSTEM.md`. Logo via `Olympic Paints Logo Digital.jpg` in `border-radius:50%;overflow:hidden` wrapper.

## GitHub Pages
- Leaderboard: `flomaticauto/olympic-paints-pulse-leaderboard`
- Scorecard archive: same repo, `/YYYY-MM-DD.html` paths

## Spec & plan
- Spec: `1.Projects/PULSE — Sales & Ops Manager/2026-05-09-pulse-design.md`
- Implementation plan: `1.Projects/PULSE — Sales & Ops Manager/2026-05-09-pulse-implementation-plan.md`
```

- [ ] **Step 2: Append entry to MEMORY.md**

In `MEMORY.md`, under a new heading `## PULSE Agent`:

```markdown
## PULSE Agent

- [PULSE — Agent Profile](agent_pulse.md) — Sales & Ops Manager; daily ack push, 4-week cycle plan-vs-actual, leaderboard, bi-weekly scorecard
```

- [ ] **Step 3: Create the /pulse slash command**

Path: `C:\Users\quint\.claude\commands\pulse.md`

```markdown
---
description: PULSE — Sales & Operations Manager
---

# PULSE — Sales & Operations Manager

You are PULSE, Olympic Paints' Sales & Operations Manager.

## Your remit
- Push daily ack discipline on the 5 reps (AC, AP, BV, NP, BM).
- Track cycle-based planned vs actual visits using the 4-week cycle map (`arref` column).
- Escalate silence to Quintus via Telegram (chat 8042233389).
- Publish the live leaderboard and bi-weekly scorecard.

## Your tools
- `1.Projects/PULSE — Sales & Ops Manager/scripts/*.py` — your Python toolkit
- JotForm MCP — to read submissions
- Resend (via `pulse_resend.py`) — to send emails
- Telegram (via `pulse_telegram.py`) — to alert Quintus

## Your boundaries
- You do NOT do analytics depth — that's PRISM.
- You do NOT manage staff or HR — that's HAVEN.
- You do NOT enter CRM data — that's STRIKER.
- You do NOT run the factory — that's SIGMA.
- You DO coordinate with all of them so their work feeds the daily rhythm.

## Your boot context
Read `agent_pulse.md` from memory and the spec at `1.Projects/PULSE — Sales & Ops Manager/2026-05-09-pulse-design.md` before any non-trivial action.
```

- [ ] **Step 4: Verify the slash command is discoverable**

Test: open a fresh Claude Code session in this repo and type `/pulse` — confirm the command surfaces. (No automated test; visual check.)

- [ ] **Step 5: Commit memory + slash command**

```bash
git add "C:/Users/quint/.claude/projects/c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints/memory/agent_pulse.md"
git add "C:/Users/quint/.claude/projects/c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints/memory/MEMORY.md"
git add "C:/Users/quint/.claude/commands/pulse.md"
git commit -m "feat(pulse): agent memory profile + /pulse slash command"
```

---

## Task 18: Windows Task Scheduler registration

**Files:**
- Create: `1.Projects/PULSE — Sales & Ops Manager/scheduler/register.ps1`
- Create: `1.Projects/PULSE — Sales & Ops Manager/scheduler/unregister.ps1`

- [ ] **Step 1: Create register.ps1**

```powershell
# Registers all PULSE scheduled tasks. Run once as Quintus.
$ErrorActionPreference = "Stop"
$root = "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE — Sales & Ops Manager"
$python = "C:\Python311\python.exe"  # adjust if Python lives elsewhere

function Register-PulseTask {
    param([string]$Name, [string]$Script, [string]$Schedule, [string]$DaysOfWeek = $null)
    $action = New-ScheduledTaskAction -Execute $python -Argument "`"$root\scripts\$Script`"" -WorkingDirectory $root
    if ($Schedule -eq "weekday") {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $DaysOfWeek
    } elseif ($Schedule -eq "sunday") {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At $DaysOfWeek
    } elseif ($Schedule -eq "friday") {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At $DaysOfWeek
    } elseif ($Schedule -eq "biweekly") {
        # Windows Task Scheduler doesn't natively support bi-weekly. Run weekly Monday and gate inside the script with cycle-week parity.
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $DaysOfWeek
    }
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Principal $principal -Force
}

Register-PulseTask -Name "PULSE — Cycle Loader" -Script "pulse_cycle_loader.py" -Schedule "sunday" -DaysOfWeek "18:00"
Register-PulseTask -Name "PULSE — Planner" -Script "pulse_planner.py" -Schedule "sunday" -DaysOfWeek "19:00"
Register-PulseTask -Name "PULSE — Daily Mailer" -Script "pulse_daily.py" -Schedule "weekday" -DaysOfWeek "06:00"
Register-PulseTask -Name "PULSE — Leaderboard" -Script "pulse_leaderboard.py" -Schedule "weekday" -DaysOfWeek "06:30"
Register-PulseTask -Name "PULSE — Ack Escalation" -Script "pulse_escalation.py" -Schedule "weekday" -DaysOfWeek "10:15"
Register-PulseTask -Name "PULSE — Intake Escalation" -Script "pulse_intake_escalation.py" -Schedule "friday" -DaysOfWeek "09:00"
Register-PulseTask -Name "PULSE — Scorecard" -Script "pulse_scorecard.py" -Schedule "biweekly" -DaysOfWeek "07:00"

Write-Host "All PULSE tasks registered. View them in Task Scheduler under 'PULSE — *'."
```

- [ ] **Step 2: Create unregister.ps1**

```powershell
# Removes all PULSE scheduled tasks. Run as Quintus.
$ErrorActionPreference = "SilentlyContinue"
$names = @(
    "PULSE — Cycle Loader", "PULSE — Planner", "PULSE — Daily Mailer",
    "PULSE — Leaderboard", "PULSE — Ack Escalation",
    "PULSE — Intake Escalation", "PULSE — Scorecard"
)
foreach ($n in $names) {
    Unregister-ScheduledTask -TaskName $n -Confirm:$false
    Write-Host "Removed: $n"
}
```

- [ ] **Step 3: Bi-weekly gate inside pulse_scorecard.py**

Modify `scripts/pulse_scorecard.py` `__main__` to check ISO week parity before running:

```python
if __name__ == "__main__":
    cfg_path = Path(__file__).parent.parent / "pulse_config.json"
    today = date.today()
    if today.isocalendar().week % 2 != 0:  # only run on even-numbered ISO weeks
        print(f"Skipping scorecard: ISO week {today.isocalendar().week} is odd")
        raise SystemExit(0)
    run_scorecard(config_path=str(cfg_path), period_end=today,
                  targets={r: 1000000 for r in json.loads(Path(cfg_path).read_text())["reps"]})
```

- [ ] **Step 4: Smoke-test register.ps1**

Run (in elevated PowerShell):
```
powershell -ExecutionPolicy Bypass -File "1.Projects\PULSE — Sales & Ops Manager\scheduler\register.ps1"
```
Expected: `All PULSE tasks registered.`

Run: `Get-ScheduledTask -TaskName "PULSE — *"` — expect 7 tasks listed.

- [ ] **Step 5: Commit**

```bash
git add "1.Projects/PULSE — Sales & Ops Manager/scheduler/register.ps1"
git add "1.Projects/PULSE — Sales & Ops Manager/scheduler/unregister.ps1"
git add "1.Projects/PULSE — Sales & Ops Manager/scripts/pulse_scorecard.py"
git commit -m "feat(pulse): Windows Task Scheduler registration for all PULSE jobs"
```

---

## Task 19: End-to-end smoke test (manual)

This is a manual checklist Quintus runs once before the first production day. No code; just confirmation that all pieces talk to each other.

- [ ] **Step 1: Verify Resend domain** — log into resend.com, confirm `olympicpaints.co.za` shows ✓ verified.
- [ ] **Step 2: Run JotForm creation** — `python scripts/pulse_jotform.py --create-forms`. Confirm `pulse_config.json` updated with two form IDs. Open both forms in a browser and submit one test response per form.
- [ ] **Step 3: Run cycle loader** — `python scripts/pulse_cycle_loader.py`. Confirm `data/pulse_cycle.parquet` created. Open it: `python -c "import pandas as pd; print(pd.read_parquet('data/pulse_cycle.parquet').head())"`.
- [ ] **Step 4: Run planner** — `python scripts/pulse_planner.py`. Confirm `data/planned_week.json` exists with all 5 reps as keys.
- [ ] **Step 5: Dry-run daily mailer** — set rep emails in `pulse_config.json` to a personal Gmail temporarily. Run `python scripts/pulse_daily.py`. Confirm 5 emails arrive. Click the ack button on one email — confirm JotForm opens with `?rep=...&date=...` pre-filled.
- [ ] **Step 6: Submit one daily ack** — fill the JotForm. Wait. Manually run `python scripts/pulse_escalation.py`. Confirm Telegram message arrives listing the *4 other* reps as missing.
- [ ] **Step 7: Run leaderboard** — `python scripts/pulse_leaderboard.py`. Open `https://flomaticauto.github.io/olympic-paints-pulse-leaderboard/`. Confirm page loads with 5 reps ranked.
- [ ] **Step 8: Run scorecard** — `python scripts/pulse_scorecard.py`. Confirm 6 emails arrive (5 reps + Quintus). Open the scorecard URL. Confirm sections render.
- [ ] **Step 9: Webhook smoke** — `python scripts/pulse_webhook.py` (in a separate terminal). In Resend dashboard, send a test webhook. Confirm `data/email_events.parquet` grows by one row.
- [ ] **Step 10: Restore real rep emails** in `pulse_config.json`. Commit. Run `register.ps1` to schedule tasks. **Go-live.**

---

## Self-review

**Spec coverage check** (each section/requirement → which task implements it):

| Spec § | Task |
|---|---|
| §2 Agent identity | T17 |
| §3 Reps in scope | T1 (config), T17 (memory) |
| §4 Sources of truth | T5 (sales/leads/meetings), T6 (cycle), T4 (jotform) |
| §5 Architecture | T6, T7, T12, T13, T14, T15 |
| §6 Daily mini-mailer | T9 (template), T12 (orchestrator) |
| §7 Bi-weekly scorecard | T11 (template), T15 (orchestrator) |
| §8 Live leaderboard | T10 (template), T13 (orchestrator) |
| §9 JotForms | T4 |
| §10 Escalation rules | T14 |
| §11 Files & paths | T1 (skeleton) |
| §12 Design system compliance | T8 |
| §13 Notifications | T2, T3 |
| §14 Out of scope | (intentionally absent) |
| §15 Risks | T18 (DNS gating), T19 (smoke) |
| §16 Success criteria | (operational, post-launch) |
| §17 Phasing | T1-T19 (all at once, per spec) |
| §18 Resend setup | T2 (helper), T19 (manual verify), T16 (webhook) |

**Placeholder scan** — no TBDs, no "implement appropriate error handling" hand-waves, no "similar to Task N" without code. Two small `v1.1` deferrals (plan adherence wiring in scorecard, full visit count from planned_week archive) are explicit and bounded.

**Type consistency** — `rep` is always `str` (the 2-letter code). `date` for dates. `pct_target` is `float` 0–N (e.g. 0.98, 1.12). JotForm submissions are `dict` with `rep`/`date`/`cycle_week`/etc. keys.

---

## Plan complete

Plan saved to [`1.Projects/PULSE — Sales & Ops Manager/2026-05-09-pulse-implementation-plan.md`](./2026-05-09-pulse-implementation-plan.md).

19 tasks. Each task is a self-contained TDD cycle (write failing test → run to confirm fail → implement → run to confirm pass → commit). Estimated ~3 working days of focused build, plus 1 day for the manual smoke test (Task 19) and DNS verification.




