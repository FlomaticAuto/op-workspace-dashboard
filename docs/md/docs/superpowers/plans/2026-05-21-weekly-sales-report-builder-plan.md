# Weekly Sales Report Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-user, week-scoped qualitative sales notebook that ingests free-form notes (Telegram + folder watcher) into ISO-week JSON buckets, mirrors them to a Notion database, and continuously rebuilds an Olympic-themed HTML report served behind portal auth on Vercel — with a Friday 07:00 SAST email snapshot to Quintus.

**Architecture:** Disk is the source of truth. `note_intake.py` is the single entry point called by both Telegram (long-poll listener) and a watchdog folder watcher. Intake writes a JSON note file + copies media into the current ISO week's bucket, mirrors to Notion (best-effort), and schedules a 5-second-debounced rebuild via `compile_report.py`. Compile classifies each note via Claude (by intent: rep_feedback / quality_ops / other), clusters the "other" pile into emergent themes, and renders `report.html` into both the week folder and the Vercel portal repo at `/public/weekly/current/`. Sunday 23:59 locks the week; Monday 00:01 initialises the next.

**Tech Stack:** Python 3.11+ · `requests` · `watchdog` · `notion-client` · `anthropic` · `jinja2` · `pywin32` (Outlook) · Windows Task Scheduler · pytest + pytest-mock · Vercel (existing portal app) · Notion (existing "Olympic Paints Automations" integration).

---

## Pre-flight context

**Spec:** `docs/superpowers/specs/2026-05-21-weekly-sales-report-builder-design.md`. Read it before starting. Every design decision is locked.

**Existing assets we re-use:**
- Telegram bot `olympic_pulse_bot`, token in `1.Projects/PULSE — Sales & Ops Manager/.env` as `TELEGRAM_BOT_TOKEN`. Quintus's chat ID is `8042233389`.
- Notion integration "Olympic Paints Automations", token in same `.env` as `NOTION_API_TOKEN`. We'll create a new Notion database manually and share it with this integration.
- Vercel project `olympic-paints-portal` (Next.js, repo path: see existing memory `reference_olympic_portal_v1.md`).
- Outlook + win32com pattern from existing scripts — always force-flush the Outbox after `.Send()`.
- Olympic design system: `DESIGN_SYSTEM.md`. Navy theme default. Real logo.jpg (not SVG).

**New project root:** `1.Projects/Weekly Sales Report/`

**Repository convention:** `0.Inbox/weekly/` is the folder watcher's input directory (Quintus drops files here from his laptop). Create it as part of Task 1.

**TLS quirk on this machine:** Always include `import truststore; truststore.inject_into_ssl()` at the top of any script that makes HTTPS calls (per existing memory `feedback_python_truststore_for_https.md`).

**Logging convention:** Scheduled tasks log to `C:\Users\quint\.claude\logs\weekly-report\` (NEVER OneDrive paths from schtasks — per memory `feedback_schtasks_logs_outside_onedrive.md`).

**Telegram-token rule:** read from PULSE `.env`, never hardcode (per memory `feedback_telegram_token_source.md`).

**Email rule:** sender = Outlook (win32com), never Gmail; recipient = `quintusl@olympicpaints.co.za` only, no CC (per memories `feedback_email_always_outlook.md`, `feedback_rep_email_cc.md`).

**Logo rule:** copy `Olympic Paints Logo Digital.jpg` into the portal `/public/weekly/current/` directory as `logo.jpg`; wrap in `border-radius:50%;overflow:hidden` (per CLAUDE.md section "Logo — official Clickpaint digital badge").

---

## File structure

### New project tree (`1.Projects/Weekly Sales Report/`)

```
1.Projects/Weekly Sales Report/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── weekly/                          # Python package
│   ├── __init__.py
│   ├── config.py                    # loads env + paths
│   ├── week_paths.py                # ISO week → folder paths
│   ├── note_intake.py               # the single entry point
│   ├── note_model.py                # dataclasses + JSON schema
│   ├── folder_watcher.py            # watchdog daemon
│   ├── telegram_listener.py         # long-poll inbound bot
│   ├── notion_mirror.py             # one note → one Notion row
│   ├── notion_retry.py              # sweep _notion_state==pending
│   ├── classifier.py                # Claude calls (mockable)
│   ├── compile_report.py            # walk notes → render HTML
│   ├── render.py                    # Jinja2 wrapper
│   ├── portal_deploy.py             # copy HTML+media into portal repo
│   ├── debounce.py                  # 5-second rebuild scheduler
│   ├── send_weekly_email.py         # Friday 07:00 Outlook send
│   ├── archive_week.py              # Sunday 23:59 lock
│   ├── init_new_week.py             # Monday 00:01 init
│   └── templates/
│       └── report.html.j2           # Jinja2 master template
├── scheduler/
│   ├── register.ps1                 # registers all schtasks jobs
│   └── unregister.ps1
└── tests/
    ├── __init__.py
    ├── conftest.py                  # tmp_path fixtures + frozen time
    ├── fixtures/
    │   ├── _test_W00/               # fixture week with 5 sample notes
    │   │   ├── notes/note1.json …
    │   │   └── media/sample.jpg
    │   └── classifier_responses.json # canned LLM outputs
    ├── test_week_paths.py
    ├── test_note_model.py
    ├── test_note_intake.py
    ├── test_notion_mirror.py
    ├── test_classifier.py
    ├── test_compile_report.py
    ├── test_render.py
    ├── test_debounce.py
    └── test_archive_week.py
```

### Touch points outside the project

- **Create `0.Inbox/weekly/`** — empty folder watched by `folder_watcher.py`.
- **Vercel portal repo** (separate git checkout at `C:\Users\quint\<portal-repo-name>\` — confirm exact path in Task 13): add `/public/weekly/current/` and `/public/weekly/<ISO-week>/` directories; add a new Next.js route `app/weekly/page.tsx` (App Router) that serves the static HTML behind the existing portal auth middleware.
- **PULSE `.env`** — `weekly/config.py` reads `TELEGRAM_BOT_TOKEN` and `NOTION_API_TOKEN` from there via `python-dotenv`. No new env vars introduced.
- **Notion** — manually create the "Weekly Sales Notes" database with the 12 columns from spec §5; share with "Olympic Paints Automations" integration. Capture the database ID in `weekly/config.py`.

### Responsibilities (one purpose per file)

- `config.py` — central env/path/constants. Importable by everything; imports nothing from the package.
- `week_paths.py` — pure function `paths_for(dt)` returning a dataclass of paths for that ISO week. No I/O.
- `note_model.py` — `Note` dataclass + `to_dict()` / `from_dict()` + JSON validation.
- `note_intake.py` — orchestrator: takes raw inputs, writes JSON, copies media, calls Notion mirror, calls debounce.
- `folder_watcher.py` — watchdog `Observer` long-running process; routes events to `note_intake.ingest_file()`.
- `telegram_listener.py` — long-poll `getUpdates` loop; routes Quintus's messages to `note_intake.ingest_telegram()`.
- `notion_mirror.py` — single function `mirror_note(note)` → returns updated note with `_notion_state`.
- `notion_retry.py` — script entry point: walk all weeks, find `_notion_state==pending`, retry.
- `classifier.py` — two functions: `classify_batch(notes)` and `cluster_other(notes)`. Both swappable via a `ClaudeClient` protocol so tests can inject a fake.
- `compile_report.py` — top-level: load → classify-if-needed → render → write to disk → deploy.
- `render.py` — Jinja2 environment setup + the single `render_report(context)` function.
- `portal_deploy.py` — `deploy_current(week_dir, portal_repo)`: copies HTML + media into portal `/public/weekly/current/` and `/public/weekly/<ISO-week>/`, commits + pushes.
- `debounce.py` — `schedule_rebuild()`: thread-safe 5-second debouncer that calls `compile_report.run_for_current_week()`.
- `send_weekly_email.py` — builds HTML body summary + attaches `report.html`, sends via win32com.
- `archive_week.py` — Sunday job: builds the locked HTML, leaves the bucket where it is (already dated), updates `_archive_index.json`.
- `init_new_week.py` — Monday job: creates the next week's empty `notes/` + `media/` + writes `week_meta.json`.

---

## Tasks

### Task 1: Project scaffolding

**Files:**
- Create: `1.Projects/Weekly Sales Report/README.md`
- Create: `1.Projects/Weekly Sales Report/requirements.txt`
- Create: `1.Projects/Weekly Sales Report/pyproject.toml`
- Create: `1.Projects/Weekly Sales Report/.env.example`
- Create: `1.Projects/Weekly Sales Report/weekly/__init__.py`
- Create: `1.Projects/Weekly Sales Report/tests/__init__.py`
- Create: `1.Projects/Weekly Sales Report/tests/conftest.py`
- Create: `0.Inbox/weekly/.gitkeep` (empty marker so the watch dir exists)

- [ ] **Step 1: Write `requirements.txt`**

```
requests>=2.31
watchdog>=4.0
notion-client>=2.2
anthropic>=0.34
jinja2>=3.1
python-dotenv>=1.0
pywin32>=306; sys_platform == "win32"
truststore>=0.9
pytest>=7.4
pytest-mock>=3.12
freezegun>=1.4
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "weekly-sales-report"
version = "0.1.0"
description = "Single-user weekly qualitative sales notebook for Olympic Paints"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q"
```

- [ ] **Step 3: Write `.env.example`**

```
# Reuses PULSE bot token and Notion integration
TELEGRAM_BOT_TOKEN=<from PULSE .env>
NOTION_API_TOKEN=<from PULSE .env>
ANTHROPIC_API_KEY=<your Claude API key>
NOTION_WEEKLY_DB_ID=<created manually in Notion>
QUINTUS_TELEGRAM_CHAT_ID=8042233389
QUINTUS_EMAIL=quintusl@olympicpaints.co.za
PORTAL_REPO_PATH=C:\Users\quint\olympic-paints-portal
WEEKLY_PROJECT_ROOT=c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Weekly Sales Report
WEEKLY_INBOX_DIR=c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\weekly
```

- [ ] **Step 4: Write `README.md`**

```markdown
# Weekly Sales Report Builder

Single-user, week-scoped qualitative notebook for Olympic Paints sales.

See `docs/superpowers/specs/2026-05-21-weekly-sales-report-builder-design.md` for full design.

## Quick start
1. Copy `.env.example` to `.env` and fill in values.
2. `pip install -r requirements.txt`
3. Run tests: `pytest -v`
4. Register scheduled jobs: `powershell -File scheduler/register.ps1`
```

- [ ] **Step 5: Write `weekly/__init__.py`**

```python
"""Weekly Sales Report — qualitative notebook for Olympic Paints sales."""
__version__ = "0.1.0"
```

- [ ] **Step 6: Write `tests/__init__.py` (empty) and `tests/conftest.py`**

```python
# tests/conftest.py
import os
from datetime import datetime, timezone
from pathlib import Path
import pytest


@pytest.fixture
def fixed_now():
    """A deterministic moment: Wed 2026-05-20 10:00 SAST = ISO 2026-W21."""
    return datetime(2026, 5, 20, 8, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def project_root(tmp_path, monkeypatch):
    """A tmp project root with notes/media skeleton ready."""
    root = tmp_path / "weekly_project"
    root.mkdir()
    monkeypatch.setenv("WEEKLY_PROJECT_ROOT", str(root))
    monkeypatch.setenv("WEEKLY_INBOX_DIR", str(tmp_path / "inbox_weekly"))
    (tmp_path / "inbox_weekly").mkdir()
    return root


@pytest.fixture
def fake_env(monkeypatch):
    """Stub all required env vars with safe test values."""
    env = {
        "TELEGRAM_BOT_TOKEN": "test-tg-token",
        "NOTION_API_TOKEN": "test-notion-token",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "NOTION_WEEKLY_DB_ID": "test-db-id",
        "QUINTUS_TELEGRAM_CHAT_ID": "8042233389",
        "QUINTUS_EMAIL": "test@example.com",
        "PORTAL_REPO_PATH": "/tmp/portal_repo",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return env
```

- [ ] **Step 7: Create the inbox folder**

```bash
mkdir -p "0.Inbox/weekly"
touch "0.Inbox/weekly/.gitkeep"
```

- [ ] **Step 8: Verify scaffold**

Run: `cd "1.Projects/Weekly Sales Report" && python -c "import weekly; print(weekly.__version__)"`
Expected: `0.1.0`

Run: `cd "1.Projects/Weekly Sales Report" && pytest -v`
Expected: `no tests ran` (no tests yet — that's OK)

- [ ] **Step 9: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/" "0.Inbox/weekly/.gitkeep"
git commit -m "feat(weekly): project scaffolding (package, tests, env, requirements)"
```

---

### Task 2: `week_paths.py` — ISO week → folder paths

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/week_paths.py`
- Create: `1.Projects/Weekly Sales Report/tests/test_week_paths.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_week_paths.py
from datetime import datetime, timezone
from pathlib import Path
from weekly.week_paths import paths_for, WeekPaths


def test_paths_for_returns_iso_week_string(project_root, fixed_now):
    p = paths_for(fixed_now, root=project_root)
    assert p.iso_week == "2026-W21"


def test_paths_for_constructs_week_directory(project_root, fixed_now):
    p = paths_for(fixed_now, root=project_root)
    assert p.week_dir == project_root / "2026-W21"


def test_paths_for_has_notes_and_media_subdirs(project_root, fixed_now):
    p = paths_for(fixed_now, root=project_root)
    assert p.notes_dir == project_root / "2026-W21" / "notes"
    assert p.media_dir == project_root / "2026-W21" / "media"


def test_paths_for_report_html(project_root, fixed_now):
    p = paths_for(fixed_now, root=project_root)
    assert p.report_html == project_root / "2026-W21" / "report.html"
    assert p.report_locked_html == project_root / "2026-W21" / "report_locked.html"


def test_paths_for_week_meta(project_root, fixed_now):
    p = paths_for(fixed_now, root=project_root)
    assert p.week_meta == project_root / "2026-W21" / "week_meta.json"


def test_ensure_dirs_creates_skeleton(project_root, fixed_now):
    p = paths_for(fixed_now, root=project_root)
    p.ensure_dirs()
    assert p.notes_dir.is_dir()
    assert p.media_dir.is_dir()


def test_sunday_late_belongs_to_current_week(project_root):
    # Sun 2026-05-24 23:58 SAST = 21:58 UTC. ISO week = 2026-W21.
    ts = datetime(2026, 5, 24, 21, 58, tzinfo=timezone.utc)
    p = paths_for(ts, root=project_root)
    assert p.iso_week == "2026-W21"


def test_monday_just_after_midnight_belongs_to_next_week(project_root):
    # Mon 2026-05-25 00:01 SAST = Sun 2026-05-24 22:01 UTC.
    # Beware: we want SAST clock, not UTC clock, to decide week.
    # paths_for should accept tz-aware datetimes and use SAST internally.
    ts = datetime(2026, 5, 24, 22, 1, tzinfo=timezone.utc)
    p = paths_for(ts, root=project_root)
    assert p.iso_week == "2026-W22"
```

- [ ] **Step 2: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_week_paths.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'weekly.week_paths'`

- [ ] **Step 3: Write implementation**

```python
# weekly/week_paths.py
"""Map a moment in time to the folder layout for that ISO week.

Pure path math. No I/O except `ensure_dirs()`.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path

SAST = timezone(timedelta(hours=2))


@dataclass(frozen=True)
class WeekPaths:
    root: Path
    iso_week: str          # e.g. "2026-W21"
    week_dir: Path
    notes_dir: Path
    media_dir: Path
    report_html: Path
    report_locked_html: Path
    week_meta: Path
    friday_email_log: Path
    archive_index: Path

    def ensure_dirs(self) -> None:
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)


def paths_for(dt: datetime, *, root: Path) -> WeekPaths:
    """Return canonical paths for the ISO week containing `dt` (interpreted in SAST)."""
    if dt.tzinfo is None:
        raise ValueError("paths_for requires a timezone-aware datetime")
    local = dt.astimezone(SAST)
    year, week, _ = local.isocalendar()
    iso_week = f"{year}-W{week:02d}"
    root = Path(root)
    week_dir = root / iso_week
    return WeekPaths(
        root=root,
        iso_week=iso_week,
        week_dir=week_dir,
        notes_dir=week_dir / "notes",
        media_dir=week_dir / "media",
        report_html=week_dir / "report.html",
        report_locked_html=week_dir / "report_locked.html",
        week_meta=week_dir / "week_meta.json",
        friday_email_log=week_dir / "friday_email_sent.json",
        archive_index=root / "_archive_index.json",
    )
```

- [ ] **Step 4: Run tests, verify all pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_week_paths.py -v`
Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/week_paths.py" "1.Projects/Weekly Sales Report/tests/test_week_paths.py"
git commit -m "feat(weekly): week_paths.py — ISO-week → folder mapping (SAST aware)"
```

---

### Task 3: `note_model.py` — JSON note dataclass

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/note_model.py`
- Create: `1.Projects/Weekly Sales Report/tests/test_note_model.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_note_model.py
import json
from datetime import datetime, timezone
from weekly.note_model import Note, MediaItem


def test_note_serializes_to_expected_json_shape():
    note = Note(
        id="2026-05-21T14-32-08_a3f9",
        ts_utc=datetime(2026, 5, 21, 12, 32, 8, tzinfo=timezone.utc),
        iso_week="2026-W21",
        source="telegram",
        source_meta={"chat_id": "8042233389", "message_id": 18472, "forwarded_from": None},
        text="BV says the new Polokwane Build It is asking about tinting",
        hashtags=["#rep:BV", "#opportunity"],
        media=[],
    )
    d = note.to_dict()
    assert d["id"] == "2026-05-21T14-32-08_a3f9"
    assert d["ts_utc"] == "2026-05-21T12:32:08+00:00"
    assert d["ts_sast"] == "2026-05-21T14:32:08+02:00"
    assert d["iso_week"] == "2026-W21"
    assert d["source"] == "telegram"
    assert d["text"].startswith("BV says")
    assert d["hashtags"] == ["#rep:BV", "#opportunity"]
    assert d["media"] == []
    assert d["classification"] is None
    assert d["_compile_state"] == "pending"
    assert d["_notion_state"] == "pending"


def test_note_round_trip():
    note = Note(
        id="2026-05-21T14-32-08_a3f9",
        ts_utc=datetime(2026, 5, 21, 12, 32, 8, tzinfo=timezone.utc),
        iso_week="2026-W21",
        source="folder",
        source_meta={"path": "test.pdf"},
        text="hello",
        hashtags=[],
        media=[MediaItem(filename="x.jpg", kind="image", bytes_=1234,
                          portal_url="https://example.com/x.jpg")],
    )
    serialized = json.dumps(note.to_dict())
    restored = Note.from_dict(json.loads(serialized))
    assert restored == note


def test_make_id_is_deterministic_for_same_inputs():
    ts = datetime(2026, 5, 21, 14, 32, 8, tzinfo=timezone.utc)
    id1 = Note.make_id(ts, "hello world")
    id2 = Note.make_id(ts, "hello world")
    assert id1 == id2
    assert id1.startswith("2026-05-21T")


def test_make_id_differs_for_different_text():
    ts = datetime(2026, 5, 21, 14, 32, 8, tzinfo=timezone.utc)
    id1 = Note.make_id(ts, "hello")
    id2 = Note.make_id(ts, "world")
    assert id1 != id2
```

- [ ] **Step 2: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_note_model.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation**

```python
# weekly/note_model.py
"""Dataclass + JSON shape for a single captured note."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any

SAST = timezone(timedelta(hours=2))


@dataclass
class MediaItem:
    filename: str
    kind: str          # "image" | "video" | "audio" | "pdf" | "other"
    bytes_: int
    portal_url: str

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "kind": self.kind,
            "bytes": self.bytes_,
            "portal_url": self.portal_url,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MediaItem":
        return cls(
            filename=d["filename"],
            kind=d["kind"],
            bytes_=d["bytes"],
            portal_url=d["portal_url"],
        )


@dataclass
class Note:
    id: str
    ts_utc: datetime
    iso_week: str
    source: str                              # "telegram" | "folder"
    source_meta: dict[str, Any]
    text: str
    hashtags: list[str]
    media: list[MediaItem] = field(default_factory=list)
    classification: dict | None = None
    _compile_state: str = "pending"          # "pending" | "classified"
    _notion_state: str = "pending"           # "pending" | "synced" | "failed"

    @staticmethod
    def make_id(ts_utc: datetime, text: str) -> str:
        ts_str = ts_utc.astimezone(SAST).strftime("%Y-%m-%dT%H-%M-%S")
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:4]
        return f"{ts_str}_{h}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ts_utc": self.ts_utc.isoformat(),
            "ts_sast": self.ts_utc.astimezone(SAST).isoformat(),
            "iso_week": self.iso_week,
            "source": self.source,
            "source_meta": self.source_meta,
            "text": self.text,
            "hashtags": list(self.hashtags),
            "media": [m.to_dict() for m in self.media],
            "classification": self.classification,
            "_compile_state": self._compile_state,
            "_notion_state": self._notion_state,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Note":
        return cls(
            id=d["id"],
            ts_utc=datetime.fromisoformat(d["ts_utc"]),
            iso_week=d["iso_week"],
            source=d["source"],
            source_meta=d.get("source_meta", {}),
            text=d["text"],
            hashtags=list(d.get("hashtags", [])),
            media=[MediaItem.from_dict(m) for m in d.get("media", [])],
            classification=d.get("classification"),
            _compile_state=d.get("_compile_state", "pending"),
            _notion_state=d.get("_notion_state", "pending"),
        )
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_note_model.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/note_model.py" "1.Projects/Weekly Sales Report/tests/test_note_model.py"
git commit -m "feat(weekly): Note + MediaItem dataclasses with deterministic IDs"
```

---

### Task 4: `config.py` — env + paths

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/config.py`

- [ ] **Step 1: Write `config.py`**

```python
# weekly/config.py
"""Central config: reads env, computes paths. No business logic."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root if present
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def _required(key: str) -> str:
    v = os.environ.get(key)
    if not v:
        raise RuntimeError(f"Missing required env var: {key}")
    return v


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    notion_api_token: str
    anthropic_api_key: str
    notion_weekly_db_id: str
    quintus_chat_id: str
    quintus_email: str
    portal_repo_path: Path
    project_root: Path
    inbox_dir: Path

    @classmethod
    def from_env(cls) -> "Config":
        # Tolerate PULSE .env for the two shared secrets
        pulse_env = _PROJECT_ROOT.parent / "PULSE — Sales & Ops Manager" / ".env"
        if pulse_env.exists():
            load_dotenv(pulse_env, override=False)
        return cls(
            telegram_bot_token=_required("TELEGRAM_BOT_TOKEN"),
            notion_api_token=_required("NOTION_API_TOKEN"),
            anthropic_api_key=_required("ANTHROPIC_API_KEY"),
            notion_weekly_db_id=_required("NOTION_WEEKLY_DB_ID"),
            quintus_chat_id=os.environ.get("QUINTUS_TELEGRAM_CHAT_ID", "8042233389"),
            quintus_email=os.environ.get("QUINTUS_EMAIL", "quintusl@olympicpaints.co.za"),
            portal_repo_path=Path(_required("PORTAL_REPO_PATH")),
            project_root=Path(os.environ.get("WEEKLY_PROJECT_ROOT", str(_PROJECT_ROOT))),
            inbox_dir=Path(_required("WEEKLY_INBOX_DIR")),
        )
```

- [ ] **Step 2: Smoke-test config loads with fake env**

Run:
```bash
cd "1.Projects/Weekly Sales Report"
TELEGRAM_BOT_TOKEN=x NOTION_API_TOKEN=x ANTHROPIC_API_KEY=x NOTION_WEEKLY_DB_ID=x \
  PORTAL_REPO_PATH=/tmp WEEKLY_INBOX_DIR=/tmp python -c "from weekly.config import Config; print(Config.from_env())"
```
Expected: prints a Config dataclass with all values populated.

- [ ] **Step 3: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/config.py"
git commit -m "feat(weekly): config.py central env loader (reads PULSE .env fallback)"
```

---

### Task 5: `note_intake.py` — the single entry point

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/note_intake.py`
- Create: `1.Projects/Weekly Sales Report/tests/test_note_intake.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_note_intake.py
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from weekly.note_intake import ingest_text, ingest_file
from weekly.note_model import Note


def test_ingest_text_writes_json_to_correct_week(project_root, fixed_now, monkeypatch):
    # Stub debounce + notion so we test intake in isolation
    monkeypatch.setattr("weekly.note_intake.schedule_rebuild", lambda: None)
    monkeypatch.setattr("weekly.note_intake.mirror_note", lambda n, **_: n)

    note = ingest_text(
        text="BV mentioned Polokwane Build It tinting opportunity",
        hashtags=["#rep:BV"],
        source="telegram",
        source_meta={"chat_id": "8042233389", "message_id": 1},
        now=fixed_now,
        root=project_root,
    )
    assert note.iso_week == "2026-W21"
    json_path = project_root / "2026-W21" / "notes" / f"{note.id}.json"
    assert json_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["text"].startswith("BV mentioned")
    assert payload["hashtags"] == ["#rep:BV"]
    assert payload["source"] == "telegram"


def test_ingest_text_fires_notion_and_rebuild(project_root, fixed_now, monkeypatch):
    notion_calls = []
    rebuild_calls = []
    monkeypatch.setattr("weekly.note_intake.schedule_rebuild",
                        lambda: rebuild_calls.append(1))
    monkeypatch.setattr("weekly.note_intake.mirror_note",
                        lambda n, **_: notion_calls.append(n) or n)

    ingest_text(
        text="hello", hashtags=[], source="telegram", source_meta={},
        now=fixed_now, root=project_root,
    )
    assert len(notion_calls) == 1
    assert len(rebuild_calls) == 1


def test_ingest_text_extracts_hashtags_from_body(project_root, fixed_now, monkeypatch):
    monkeypatch.setattr("weekly.note_intake.schedule_rebuild", lambda: None)
    monkeypatch.setattr("weekly.note_intake.mirror_note", lambda n, **_: n)

    note = ingest_text(
        text="customer complaint about #quality on batch 117 #rep:AC",
        hashtags=None, source="telegram", source_meta={},
        now=fixed_now, root=project_root,
    )
    assert "#quality" in note.hashtags
    assert "#rep:AC" in note.hashtags


def test_ingest_file_copies_media_and_creates_note(project_root, fixed_now, monkeypatch, tmp_path):
    monkeypatch.setattr("weekly.note_intake.schedule_rebuild", lambda: None)
    monkeypatch.setattr("weekly.note_intake.mirror_note", lambda n, **_: n)

    src = tmp_path / "drop.pdf"
    src.write_bytes(b"%PDF-1.4 fake")

    note = ingest_file(
        file_path=src,
        caption=None,
        source="folder",
        source_meta={"path": str(src)},
        now=fixed_now,
        root=project_root,
    )
    assert len(note.media) == 1
    media_dir = project_root / "2026-W21" / "media"
    assert (media_dir / note.media[0].filename).exists()
    assert note.media[0].kind == "pdf"


def test_intake_is_resilient_to_notion_failure(project_root, fixed_now, monkeypatch):
    """A Notion API error must not prevent the note from being written to disk."""
    monkeypatch.setattr("weekly.note_intake.schedule_rebuild", lambda: None)

    def boom(note, **_):
        raise RuntimeError("Notion 429")
    monkeypatch.setattr("weekly.note_intake.mirror_note", boom)

    note = ingest_text(
        text="critical observation", hashtags=[], source="telegram",
        source_meta={}, now=fixed_now, root=project_root,
    )
    # Note still on disk despite Notion failure
    assert (project_root / "2026-W21" / "notes" / f"{note.id}.json").exists()
    assert note._notion_state == "failed"
```

- [ ] **Step 2: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_note_intake.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation**

```python
# weekly/note_intake.py
"""The single entry point used by both Telegram and folder watcher.

Disk write is the only operation that MUST succeed. Notion + rebuild are
best-effort and never block the note from being captured.
"""
from __future__ import annotations
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from weekly.note_model import Note, MediaItem
from weekly.week_paths import paths_for
from weekly.debounce import schedule_rebuild
from weekly.notion_mirror import mirror_note

HASHTAG_RE = re.compile(r"#[A-Za-z][\w:_-]*")

PORTAL_URL_TEMPLATE = (
    "https://olympic-paints-portal.vercel.app/weekly/{iso_week}/media/{filename}"
)


def _classify_kind(suffix: str) -> str:
    suffix = suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg", "png", "gif", "webp", "heic"}:
        return "image"
    if suffix in {"mp4", "mov", "webm", "mkv"}:
        return "video"
    if suffix in {"m4a", "mp3", "ogg", "wav", "opus"}:
        return "audio"
    if suffix == "pdf":
        return "pdf"
    return "other"


def ingest_text(
    *,
    text: str,
    hashtags: list[str] | None,
    source: str,
    source_meta: dict[str, Any],
    now: datetime,
    root: Path,
) -> Note:
    """Capture a text-only note. Returns the saved Note (post-mirror)."""
    paths = paths_for(now, root=root)
    paths.ensure_dirs()

    if hashtags is None:
        hashtags = HASHTAG_RE.findall(text)

    note = Note(
        id=Note.make_id(now, text),
        ts_utc=now,
        iso_week=paths.iso_week,
        source=source,
        source_meta=source_meta,
        text=text,
        hashtags=hashtags,
    )
    return _persist(note, paths)


def ingest_file(
    *,
    file_path: Path,
    caption: str | None,
    source: str,
    source_meta: dict[str, Any],
    now: datetime,
    root: Path,
) -> Note:
    """Capture a file-based note (folder drop or Telegram attachment)."""
    paths = paths_for(now, root=root)
    paths.ensure_dirs()

    text = caption or f"[file dropped] {file_path.name}"
    note = Note(
        id=Note.make_id(now, text + file_path.name),
        ts_utc=now,
        iso_week=paths.iso_week,
        source=source,
        source_meta=source_meta,
        text=text,
        hashtags=HASHTAG_RE.findall(text),
    )

    target_name = f"{note.id}_{file_path.name}"
    target = paths.media_dir / target_name
    shutil.copy2(file_path, target)
    note.media.append(MediaItem(
        filename=target_name,
        kind=_classify_kind(file_path.suffix),
        bytes_=target.stat().st_size,
        portal_url=PORTAL_URL_TEMPLATE.format(iso_week=paths.iso_week, filename=target_name),
    ))
    return _persist(note, paths)


def _persist(note: Note, paths) -> Note:
    """Write JSON → fire Notion mirror → schedule rebuild. Disk write is the only must-succeed step."""
    out = paths.notes_dir / f"{note.id}.json"
    out.write_text(json.dumps(note.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    # Best-effort Notion mirror
    try:
        note = mirror_note(note)
    except Exception:
        note._notion_state = "failed"
        out.write_text(json.dumps(note.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    # Best-effort rebuild
    try:
        schedule_rebuild()
    except Exception:
        pass

    return note
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_note_intake.py -v`
Expected: all 5 tests PASS.

Note: tests stub `mirror_note` and `schedule_rebuild` via monkeypatch — we haven't written those modules with real bodies yet, but the import paths must exist. Add minimal stubs:

```python
# weekly/notion_mirror.py (placeholder body — filled in Task 7)
def mirror_note(note, **kwargs):
    note._notion_state = "synced"
    return note
```

```python
# weekly/debounce.py (placeholder body — filled in Task 10)
def schedule_rebuild() -> None:
    pass
```

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/note_intake.py" \
            "1.Projects/Weekly Sales Report/weekly/notion_mirror.py" \
            "1.Projects/Weekly Sales Report/weekly/debounce.py" \
            "1.Projects/Weekly Sales Report/tests/test_note_intake.py"
git commit -m "feat(weekly): note_intake.py — single ingest path (disk-first, Notion best-effort)"
```

---

### Task 6: `classifier.py` — Claude calls (with mockable client)

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/classifier.py`
- Create: `1.Projects/Weekly Sales Report/tests/test_classifier.py`
- Create: `1.Projects/Weekly Sales Report/tests/fixtures/classifier_responses.json`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_classifier.py
from datetime import datetime, timezone
from weekly.classifier import classify_batch, cluster_other, FakeClaudeClient
from weekly.note_model import Note


def _note(text, nid="n1"):
    return Note(
        id=nid,
        ts_utc=datetime(2026, 5, 21, 12, tzinfo=timezone.utc),
        iso_week="2026-W21",
        source="telegram",
        source_meta={},
        text=text,
        hashtags=[],
    )


def test_classify_batch_assigns_section_per_note():
    notes = [
        _note("AC says customer wants bigger discount on Pick & Save", "n1"),
        _note("Batch 2026-PVA-117 viscosity too high — site complaint", "n2"),
        _note("Idea: open a depot in Tzaneen", "n3"),
    ]
    fake = FakeClaudeClient(classify_response=[
        {"id": "n1", "section": "rep_feedback", "subject": "AC / Pick & Save discount",
         "summary_one_line": "AC reports discount pressure on Pick & Save", "tags_inferred": ["discount", "pick_save"]},
        {"id": "n2", "section": "quality_ops", "subject": "Batch 2026-PVA-117 viscosity",
         "summary_one_line": "Viscosity complaint on batch 117", "tags_inferred": ["pva", "viscosity", "batch"]},
        {"id": "n3", "section": "other", "subject": "Tzaneen depot idea",
         "summary_one_line": "Idea: Tzaneen depot", "tags_inferred": ["depot", "tzaneen"]},
    ])
    out = classify_batch(notes, client=fake)
    assert out[0].classification["section"] == "rep_feedback"
    assert out[1].classification["section"] == "quality_ops"
    assert out[2].classification["section"] == "other"
    assert all(n._compile_state == "classified" for n in out)


def test_cluster_other_assigns_theme_labels():
    notes = [
        _note("Competitor X dropped prices in Mokopane", "n1"),
        _note("Competitor Y running 2-for-1 in Polokwane", "n2"),
        _note("Idea: launch tinting service Q3", "n3"),
    ]
    # Mark them all as "other" first (mimicking post-classify_batch)
    for n in notes:
        n.classification = {"section": "other", "subject": "x",
                            "summary_one_line": "x", "tags_inferred": [],
                            "theme_label": None}

    fake = FakeClaudeClient(cluster_response=[
        {"id": "n1", "theme_label": "Competitor activity"},
        {"id": "n2", "theme_label": "Competitor activity"},
        {"id": "n3", "theme_label": "Product ideas"},
    ])
    out = cluster_other(notes, client=fake)
    assert out[0].classification["theme_label"] == "Competitor activity"
    assert out[1].classification["theme_label"] == "Competitor activity"
    assert out[2].classification["theme_label"] == "Product ideas"


def test_classify_batch_is_idempotent_for_already_classified_notes():
    n = _note("hi", "n1")
    n.classification = {"section": "rep_feedback", "subject": "x",
                        "summary_one_line": "y", "tags_inferred": [], "theme_label": None}
    n._compile_state = "classified"
    fake = FakeClaudeClient(classify_response=[])  # should not be called
    out = classify_batch([n], client=fake)
    assert out[0].classification["section"] == "rep_feedback"
    assert fake.classify_calls == 0
```

Fixture file content (used by tests later):

```json
// tests/fixtures/classifier_responses.json
{
  "default_classify": [
    {"id": "n1", "section": "rep_feedback", "subject": "AC / Pick & Save",
     "summary_one_line": "AC discount pressure", "tags_inferred": ["discount"]}
  ],
  "default_cluster": [
    {"id": "n1", "theme_label": "Competitor activity"}
  ]
}
```

- [ ] **Step 2: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation**

```python
# weekly/classifier.py
"""Claude calls for note classification + theme clustering.

The real client uses the Anthropic SDK. Tests inject `FakeClaudeClient`.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from weekly.note_model import Note


SYSTEM_PROMPT = """You are classifying short qualitative notes from a single sales executive (Quintus, Olympic Paints).

For EACH input note, decide which section it belongs to using the INTENT rule:

- "rep_feedback": anything you'd discuss in a 1-on-1 with a sales rep — rep wins, rep blockers, rep-customer interactions, rep behaviour, customer quotes a rep relayed.
- "quality_ops": anything affecting WHAT we ship or HOW — paint quality, batch issues, dispatch, factory floor, returns, viscosity, drying time, tinting machine, delivery.
- "other": everything else — ideas, competitor sightings, market trends, customer wins not tied to a single rep, brainstorms, internal observations.

Hashtags in the note are HINTS but you may override them when the intent rule says otherwise.
A rep reporting a quality issue is "quality_ops" (the subject is the batch, not the rep).

Return JSON ONLY in this exact shape — one object per input note:
[
  {"id": "...", "section": "rep_feedback|quality_ops|other",
   "subject": "1-6 word subject line",
   "summary_one_line": "<=120 char summary",
   "tags_inferred": ["lowercase_snake_tags"]}
]
"""

CLUSTER_PROMPT = """You are clustering 'other' sales notes into 2-4 emergent themes for the week.

Return JSON ONLY:
[
  {"id": "...", "theme_label": "Short Title Case Label"}
]

Use no more than 4 distinct theme labels. If a note doesn't fit a coherent theme, label it "Misc".
"""


class ClaudeClient(Protocol):
    def classify(self, notes: list[Note]) -> list[dict]: ...
    def cluster(self, notes: list[Note]) -> list[dict]: ...


@dataclass
class FakeClaudeClient:
    classify_response: list[dict] = field(default_factory=list)
    cluster_response: list[dict] = field(default_factory=list)
    classify_calls: int = 0
    cluster_calls: int = 0

    def classify(self, notes):
        self.classify_calls += 1
        return self.classify_response

    def cluster(self, notes):
        self.cluster_calls += 1
        return self.cluster_response


@dataclass
class AnthropicClaudeClient:
    api_key: str
    model: str = "claude-sonnet-4-6"

    def _call(self, system: str, user: str) -> list[dict]:
        # Lazy import so tests don't need anthropic installed for unit tests
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = msg.content[0].text.strip()
        # Strip ```json fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)

    def classify(self, notes):
        payload = [{"id": n.id, "text": n.text, "hashtags": n.hashtags} for n in notes]
        return self._call(SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False))

    def cluster(self, notes):
        payload = [{"id": n.id, "text": n.text} for n in notes]
        return self._call(CLUSTER_PROMPT, json.dumps(payload, ensure_ascii=False))


def classify_batch(notes: list[Note], *, client: ClaudeClient) -> list[Note]:
    """Classify all notes whose _compile_state is 'pending'. Idempotent."""
    pending = [n for n in notes if n._compile_state == "pending"]
    if not pending:
        return notes
    responses = client.classify(pending)
    by_id = {r["id"]: r for r in responses}
    now = datetime.now(timezone.utc).isoformat()
    for n in pending:
        r = by_id.get(n.id)
        if r is None:
            continue
        n.classification = {
            "section": r["section"],
            "subject": r["subject"],
            "summary_one_line": r["summary_one_line"],
            "tags_inferred": r["tags_inferred"],
            "theme_label": None,
            "classified_at": now,
            "classifier_version": "v1",
        }
        n._compile_state = "classified"
    return notes


def cluster_other(notes: list[Note], *, client: ClaudeClient) -> list[Note]:
    """For notes already classified as 'other', assign theme_label. Idempotent."""
    others = [n for n in notes
              if n.classification and n.classification.get("section") == "other"
              and not n.classification.get("theme_label")]
    if len(others) < 2:
        # 0 or 1 'other' notes — no clustering needed
        for n in others:
            n.classification["theme_label"] = "Misc"
        return notes
    responses = client.cluster(others)
    by_id = {r["id"]: r for r in responses}
    for n in others:
        r = by_id.get(n.id)
        n.classification["theme_label"] = r["theme_label"] if r else "Misc"
    return notes
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_classifier.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/classifier.py" \
            "1.Projects/Weekly Sales Report/tests/test_classifier.py" \
            "1.Projects/Weekly Sales Report/tests/fixtures/classifier_responses.json"
git commit -m "feat(weekly): classifier.py — Claude intent classification + theme clustering"
```

---

### Task 7: `notion_mirror.py` — push one note → Notion row

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/notion_mirror.py` (overwrites placeholder)
- Create: `1.Projects/Weekly Sales Report/tests/test_notion_mirror.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_notion_mirror.py
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock
from weekly.note_model import Note, MediaItem
from weekly.notion_mirror import mirror_note, _properties_payload


def _note(**overrides):
    base = dict(
        id="2026-05-21T14-32-08_a3f9",
        ts_utc=datetime(2026, 5, 21, 12, 32, 8, tzinfo=timezone.utc),
        iso_week="2026-W21",
        source="telegram",
        source_meta={"chat_id": "8042233389"},
        text="BV mentioned Polokwane tinting opportunity",
        hashtags=["#rep:BV"],
        media=[],
    )
    base.update(overrides)
    return Note(**base)


def test_properties_payload_minimum_fields():
    note = _note()
    note.classification = None
    props = _properties_payload(note)
    assert props["Title"]["title"][0]["text"]["content"].startswith("BV mentioned")
    assert props["Week"]["select"]["name"] == "2026-W21"
    assert props["Section"]["select"]["name"] == "unclassified"
    assert props["Note ID"]["rich_text"][0]["text"]["content"] == note.id
    assert "Full text" in props


def test_properties_payload_uses_summary_when_classified():
    note = _note()
    note.classification = {
        "section": "rep_feedback",
        "subject": "BV / Polokwane",
        "summary_one_line": "BV exploring tinting service",
        "tags_inferred": ["opportunity", "tinting"],
        "theme_label": None,
    }
    props = _properties_payload(note)
    assert props["Title"]["title"][0]["text"]["content"] == "BV exploring tinting service"
    assert props["Section"]["select"]["name"] == "rep_feedback"
    assert props["Subject"]["rich_text"][0]["text"]["content"] == "BV / Polokwane"


def test_properties_payload_includes_media_url_when_present():
    note = _note(media=[MediaItem(filename="x.jpg", kind="image", bytes_=1,
                                    portal_url="https://example.com/x.jpg")])
    props = _properties_payload(note)
    assert props["Media"]["url"] == "https://example.com/x.jpg"


def test_mirror_note_success_sets_state_synced(monkeypatch):
    client = MagicMock()
    client.pages.create.return_value = {"id": "fake-page-id"}
    monkeypatch.setattr("weekly.notion_mirror._client", lambda: client)
    monkeypatch.setenv("NOTION_WEEKLY_DB_ID", "test-db-id")
    monkeypatch.setenv("NOTION_API_TOKEN", "test-token")

    note = _note()
    out = mirror_note(note)
    assert out._notion_state == "synced"
    client.pages.create.assert_called_once()


def test_mirror_note_failure_sets_state_failed(monkeypatch):
    client = MagicMock()
    client.pages.create.side_effect = RuntimeError("429 rate-limited")
    monkeypatch.setattr("weekly.notion_mirror._client", lambda: client)
    monkeypatch.setenv("NOTION_WEEKLY_DB_ID", "test-db-id")
    monkeypatch.setenv("NOTION_API_TOKEN", "test-token")

    note = _note()
    with pytest.raises(RuntimeError):
        mirror_note(note)
    # State is mutated on the input note even when the exception propagates
    assert note._notion_state == "failed"
```

- [ ] **Step 2: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_notion_mirror.py -v`
Expected: FAIL — module doesn't have `_properties_payload` yet.

- [ ] **Step 3: Write implementation**

```python
# weekly/notion_mirror.py
"""Mirror a single note into the Notion 'Weekly Sales Notes' database.

Best-effort: callers handle exceptions. Sets `note._notion_state` to 'synced' or 'failed'.
"""
from __future__ import annotations
import os
from weekly.note_model import Note


def _client():
    """Lazy import so tests can monkeypatch without notion-client installed."""
    from notion_client import Client
    return Client(auth=os.environ["NOTION_API_TOKEN"])


def _rich_text(s: str) -> list[dict]:
    # Notion rich_text values cap at 2000 chars per text block
    chunks = [s[i:i + 1900] for i in range(0, len(s) or 1, 1900)] or [""]
    return [{"text": {"content": c}} for c in chunks]


def _properties_payload(note: Note) -> dict:
    """Translate a Note into the Notion DB property payload."""
    classified = note.classification or {}
    title_text = classified.get("summary_one_line") or note.text[:60] or "(no text)"
    section = classified.get("section", "unclassified")
    subject = classified.get("subject", "")
    theme = classified.get("theme_label", "") or ""
    tags = classified.get("tags_inferred", [])

    props: dict = {
        "Title": {"title": [{"text": {"content": title_text}}]},
        "Week": {"select": {"name": note.iso_week}},
        "Section": {"select": {"name": section}},
        "Theme": {"rich_text": _rich_text(theme)},
        "Subject": {"rich_text": _rich_text(subject)},
        "Source": {"select": {"name": note.source}},
        "Captured": {"date": {"start": note.to_dict()["ts_sast"]}},
        "Hashtags": {"multi_select": [{"name": h.lstrip("#")[:99]} for h in note.hashtags]},
        "Tags (inferred)": {"multi_select": [{"name": t[:99]} for t in tags]},
        "Note ID": {"rich_text": _rich_text(note.id)},
        "Full text": {"rich_text": _rich_text(note.text)},
    }
    if note.media:
        props["Media"] = {"url": note.media[0].portal_url}
    return props


def mirror_note(note: Note) -> Note:
    """Create a row in the Weekly Sales Notes DB. Raises on API failure."""
    db_id = os.environ["NOTION_WEEKLY_DB_ID"]
    client = _client()
    try:
        client.pages.create(
            parent={"database_id": db_id},
            properties=_properties_payload(note),
        )
        note._notion_state = "synced"
        return note
    except Exception:
        note._notion_state = "failed"
        raise
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_notion_mirror.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/notion_mirror.py" \
            "1.Projects/Weekly Sales Report/tests/test_notion_mirror.py"
git commit -m "feat(weekly): notion_mirror.py — push note → Weekly Sales Notes DB"
```

---

### Task 8: `notion_retry.py` — sweep pending mirrors

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/notion_retry.py`

- [ ] **Step 1: Write `notion_retry.py`**

```python
# weekly/notion_retry.py
"""Walk all weekly buckets and retry Notion mirror for notes with _notion_state=='pending'|'failed'.

Designed to be run every 5 minutes by Task Scheduler.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import truststore
truststore.inject_into_ssl()

from weekly.config import Config
from weekly.note_model import Note
from weekly.notion_mirror import mirror_note


def sweep(root: Path) -> tuple[int, int]:
    """Return (succeeded, failed) counts."""
    succeeded = failed = 0
    for week_dir in sorted(root.glob("20*-W*")):
        notes_dir = week_dir / "notes"
        if not notes_dir.is_dir():
            continue
        for jpath in notes_dir.glob("*.json"):
            data = json.loads(jpath.read_text(encoding="utf-8"))
            if data.get("_notion_state") == "synced":
                continue
            note = Note.from_dict(data)
            try:
                mirror_note(note)
                succeeded += 1
            except Exception as e:
                print(f"  retry failed: {jpath.name}: {e}", file=sys.stderr)
                failed += 1
            jpath.write_text(json.dumps(note.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return succeeded, failed


def main() -> int:
    cfg = Config.from_env()
    succeeded, failed = sweep(cfg.project_root)
    print(f"notion_retry: {succeeded} synced, {failed} still failing")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Smoke test — empty root**

Run:
```bash
cd "1.Projects/Weekly Sales Report"
python -c "from pathlib import Path; from weekly.notion_retry import sweep; print(sweep(Path('/tmp/empty')))"
```
Expected: `(0, 0)`

- [ ] **Step 3: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/notion_retry.py"
git commit -m "feat(weekly): notion_retry.py — sweep pending mirrors every 5 min"
```

---

### Task 9: `render.py` + `templates/report.html.j2` — Jinja2 template

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/render.py`
- Create: `1.Projects/Weekly Sales Report/weekly/templates/report.html.j2`
- Create: `1.Projects/Weekly Sales Report/tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_render.py
from datetime import datetime, timezone
from weekly.render import render_report
from weekly.note_model import Note


def _classified(text, section, subject, summary, nid):
    n = Note(
        id=nid,
        ts_utc=datetime(2026, 5, 21, 12, tzinfo=timezone.utc),
        iso_week="2026-W21",
        source="telegram",
        source_meta={},
        text=text,
        hashtags=[],
    )
    n.classification = {
        "section": section,
        "subject": subject,
        "summary_one_line": summary,
        "tags_inferred": [],
        "theme_label": None,
    }
    n._compile_state = "classified"
    return n


def test_render_includes_iso_week_in_header():
    notes = [_classified("hi", "rep_feedback", "AC", "hello", "n1")]
    html = render_report(
        iso_week="2026-W21",
        period_label="18 May – 24 May 2026",
        notes=notes,
        exec_summary_bullets=["1 note logged"],
        locked=False,
    )
    assert "2026-W21" in html or "2026 WEEK 21" in html
    assert "18 May – 24 May 2026" in html


def test_render_groups_rep_feedback_by_subject():
    notes = [
        _classified("note 1", "rep_feedback", "AC", "summary 1", "n1"),
        _classified("note 2", "rep_feedback", "BV", "summary 2", "n2"),
    ]
    html = render_report(
        iso_week="2026-W21", period_label="x", notes=notes,
        exec_summary_bullets=[], locked=False,
    )
    assert "REP FEEDBACK" in html.upper()
    assert "summary 1" in html
    assert "summary 2" in html


def test_render_empty_section_shows_placeholder():
    html = render_report(
        iso_week="2026-W21", period_label="x", notes=[],
        exec_summary_bullets=[], locked=False,
    )
    assert "No rep feedback logged this week." in html
    assert "No quality or operations notes logged this week." in html


def test_render_marks_locked_in_header():
    html_live = render_report(iso_week="2026-W21", period_label="x", notes=[],
                              exec_summary_bullets=[], locked=False)
    html_locked = render_report(iso_week="2026-W21", period_label="x", notes=[],
                                exec_summary_bullets=[], locked=True)
    assert "LIVE" in html_live
    assert "LOCKED" in html_locked


def test_render_themes_grouped_in_other_section():
    notes = [
        _classified("competitor X dropped prices", "other", "x", "comp drop", "n1"),
        _classified("competitor Y bundling", "other", "y", "comp bundle", "n2"),
        _classified("idea: tinting service", "other", "z", "tint idea", "n3"),
    ]
    notes[0].classification["theme_label"] = "Competitor activity"
    notes[1].classification["theme_label"] = "Competitor activity"
    notes[2].classification["theme_label"] = "Product ideas"
    html = render_report(iso_week="2026-W21", period_label="x", notes=notes,
                         exec_summary_bullets=[], locked=False)
    assert "Competitor activity" in html
    assert "Product ideas" in html
    # Both Competitor entries appear under the same theme block
    idx = html.find("Competitor activity")
    assert "comp drop" in html[idx:] and "comp bundle" in html[idx:]


def test_render_html_includes_navy_theme_class_default():
    html = render_report(iso_week="2026-W21", period_label="x", notes=[],
                         exec_summary_bullets=[], locked=False)
    assert 'class="theme-navy"' in html
```

- [ ] **Step 2: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_render.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Write `render.py`**

```python
# weekly/render.py
"""Jinja2 wrapper. One public function: render_report()."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weekly.note_model import Note

_TPL_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TPL_DIR)),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _group_rep_feedback(notes: list[Note]) -> dict[str, list[Note]]:
    out: dict[str, list[Note]] = defaultdict(list)
    for n in notes:
        if n.classification and n.classification["section"] == "rep_feedback":
            key = n.classification.get("subject") or "Unattributed"
            out[key].append(n)
    return dict(out)


def _group_quality(notes: list[Note]) -> dict[str, list[Note]]:
    out: dict[str, list[Note]] = defaultdict(list)
    for n in notes:
        if n.classification and n.classification["section"] == "quality_ops":
            key = n.classification.get("subject") or "Unattributed"
            out[key].append(n)
    return dict(out)


def _group_themes(notes: list[Note]) -> dict[str, list[Note]]:
    out: dict[str, list[Note]] = defaultdict(list)
    for n in notes:
        if n.classification and n.classification["section"] == "other":
            key = n.classification.get("theme_label") or "Misc"
            out[key].append(n)
    return dict(out)


def render_report(
    *,
    iso_week: str,
    period_label: str,
    notes: list[Note],
    exec_summary_bullets: list[str],
    locked: bool,
) -> str:
    tpl = _env.get_template("report.html.j2")
    return tpl.render(
        iso_week=iso_week,
        period_label=period_label,
        note_count=len(notes),
        photo_count=sum(1 for n in notes for m in n.media if m.kind == "image"),
        exec_summary_bullets=exec_summary_bullets,
        rep_groups=_group_rep_feedback(notes),
        quality_groups=_group_quality(notes),
        theme_groups=_group_themes(notes),
        locked=locked,
    )
```

- [ ] **Step 4: Write `templates/report.html.j2`**

```jinja
{# weekly/templates/report.html.j2 — Olympic navy theme by default. #}
<!DOCTYPE html>
<html lang="en" class="theme-navy">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Weekly Sales Report — {{ iso_week }} — Olympic Paints</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<style>
/* TOKENS — full block from DESIGN_SYSTEM.md (abbreviated for brevity in the plan; copy the full block from CLAUDE.md when implementing) */
:root {
  --_y50:#FEF9E0;--_y100:#FDF0A0;--_y200:#FAE04D;--_y400:#F5C400;--_y600:#D4A800;--_y800:#A88000;--_y900:#6A5000;
  --_n50:#E8EFF8;--_n100:#B8CCE8;--_n300:#6B9ED0;--_n500:#2D6BA8;--_n700:#1A3D6E;--_n900:#0D2040;--_n950:#071022;
  --_g0:#FFFFFF;--_g50:#F7F6F3;--_g100:#E8E7E2;--_g200:#C8C7C0;--_g400:#949390;--_g600:#5C5B58;--_g800:#2E2E2C;--_g900:#1A1A18;--_g950:#0D0D0B;
  --font-display:'Barlow Condensed',sans-serif;--font-body:'Barlow',sans-serif;
  --r-sm:4px;--r-md:8px;--r-lg:12px;--r-xl:16px;--r-pill:50px;
}
/* When implementing, paste in the FULL .theme-light/.theme-dark/.theme-brand/.theme-navy blocks
   from CLAUDE.md verbatim. Abbreviated here to keep the plan readable. */
.theme-navy {
  color-scheme:dark;
  --color-surface-page:var(--_n950); --color-surface-base:var(--_n900);
  --color-surface-elevated:var(--_n700); --color-surface-sunken:var(--_n950);
  --color-text-primary:var(--_g0); --color-text-secondary:var(--_n100);
  --color-text-tertiary:var(--_n300);
  --color-brand-primary:var(--_y400); --color-border-default:rgba(107,158,208,0.20);
}
body { background:var(--color-surface-page); color:var(--color-text-primary); font-family:var(--font-body); margin:0; }
.hero { padding:24px; background:var(--color-surface-base); border-bottom:1px solid var(--color-border-default); display:flex; align-items:center; gap:16px; }
.hero-logo { width:48px; height:48px; border-radius:50%; overflow:hidden; flex-shrink:0; }
.hero-logo img { display:block; width:100%; height:100%; object-fit:cover; }
.hero-title { font-family:var(--font-display); font-weight:900; font-size:32px; text-transform:uppercase; letter-spacing:0.02em; }
.hero-meta { color:var(--color-text-secondary); font-size:13px; margin-top:4px; }
.live-badge { background:var(--color-brand-primary); color:#000; padding:2px 10px; border-radius:var(--r-pill); font-family:var(--font-display); font-weight:800; font-size:11px; letter-spacing:0.08em; }
.locked-badge { background:var(--color-text-tertiary); color:#000; padding:2px 10px; border-radius:var(--r-pill); font-family:var(--font-display); font-weight:800; font-size:11px; letter-spacing:0.08em; }
.section { padding:24px; border-bottom:1px solid var(--color-border-default); }
.section h2 { font-family:var(--font-display); font-weight:800; font-size:22px; text-transform:uppercase; letter-spacing:0.04em; margin:0 0 12px; }
.empty { color:var(--color-text-tertiary); font-style:italic; }
.group { margin-bottom:20px; }
.group-title { font-family:var(--font-display); font-weight:700; font-size:14px; text-transform:uppercase; letter-spacing:0.08em; color:var(--color-text-secondary); margin-bottom:8px; }
.card { background:var(--color-surface-elevated); border:1px solid var(--color-border-default); border-radius:var(--r-md); padding:14px; margin-bottom:10px; }
.card-summary { font-weight:600; margin-bottom:6px; }
.card-text { color:var(--color-text-secondary); font-size:14px; }
.card-meta { color:var(--color-text-tertiary); font-size:11px; margin-top:8px; }
.media-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:6px; margin-top:8px; }
.media-grid img { width:100%; height:90px; object-fit:cover; border-radius:var(--r-sm); cursor:pointer; }
.exec ul { margin:0; padding-left:20px; }
.exec li { margin-bottom:6px; }
.theme-bar { display:flex; gap:4px; padding:8px 16px; background:var(--color-surface-elevated); border-bottom:1px solid var(--color-border-default); }
.theme-bar button { background:transparent; color:var(--color-text-secondary); border:1px solid var(--color-border-default); border-radius:var(--r-sm); padding:4px 10px; font-family:var(--font-body); font-size:12px; cursor:pointer; }
.theme-bar button.active { background:var(--color-brand-primary); color:#000; border-color:var(--color-brand-primary); }
.footer { padding:16px 24px; color:var(--color-text-tertiary); font-size:12px; }
</style>
</head>
<body>

<div class="theme-bar">
  <button onclick="olyTheme('theme-light',this)">Light</button>
  <button onclick="olyTheme('theme-dark',this)">Dark</button>
  <button onclick="olyTheme('theme-brand',this)">Brand</button>
  <button onclick="olyTheme('theme-navy',this)" class="active">Navy</button>
</div>

<div class="hero">
  <div class="hero-logo"><img src="logo.jpg" alt="Olympic Paints" width="48" height="48"></div>
  <div>
    <div class="hero-title">Weekly Sales Report — {{ iso_week }}</div>
    <div class="hero-meta">
      {{ period_label }} · {{ note_count }} notes · {{ photo_count }} photos ·
      {% if locked %}<span class="locked-badge">LOCKED</span>{% else %}<span class="live-badge">LIVE</span>{% endif %}
    </div>
  </div>
</div>

<div class="section exec">
  <h2>Executive Summary</h2>
  {% if exec_summary_bullets %}
    <ul>{% for b in exec_summary_bullets %}<li>{{ b }}</li>{% endfor %}</ul>
  {% else %}
    <p class="empty">Nothing summarised yet.</p>
  {% endif %}
</div>

<div class="section">
  <h2>Rep Feedback ({{ rep_groups.values()|map('length')|sum }})</h2>
  {% if rep_groups %}
    {% for subject, group in rep_groups.items() %}
      <div class="group">
        <div class="group-title">{{ subject }} — {{ group|length }} note{{ '' if group|length == 1 else 's' }}</div>
        {% for n in group %}
          {% include "_card.html.j2" ignore missing %}
          <div class="card">
            <div class="card-summary">{{ n.classification.summary_one_line }}</div>
            <div class="card-text">{{ n.text }}</div>
            {% if n.media %}
              <div class="media-grid">
                {% for m in n.media %}
                  {% if m.kind == 'image' %}<img src="media/{{ m.filename }}" alt="" onclick="window.open(this.src)">{% endif %}
                {% endfor %}
              </div>
            {% endif %}
            <div class="card-meta">{{ n.to_dict()['ts_sast'] }}</div>
          </div>
        {% endfor %}
      </div>
    {% endfor %}
  {% else %}
    <p class="empty">No rep feedback logged this week.</p>
  {% endif %}
</div>

<div class="section">
  <h2>Quality &amp; Operations ({{ quality_groups.values()|map('length')|sum }})</h2>
  {% if quality_groups %}
    {% for subject, group in quality_groups.items() %}
      <div class="group">
        <div class="group-title">{{ subject }} — {{ group|length }} note{{ '' if group|length == 1 else 's' }}</div>
        {% for n in group %}
          <div class="card">
            <div class="card-summary">{{ n.classification.summary_one_line }}</div>
            <div class="card-text">{{ n.text }}</div>
            {% if n.media %}
              <div class="media-grid">
                {% for m in n.media %}
                  {% if m.kind == 'image' %}<img src="media/{{ m.filename }}" alt="" onclick="window.open(this.src)">{% endif %}
                {% endfor %}
              </div>
            {% endif %}
            <div class="card-meta">{{ n.to_dict()['ts_sast'] }}</div>
          </div>
        {% endfor %}
      </div>
    {% endfor %}
  {% else %}
    <p class="empty">No quality or operations notes logged this week.</p>
  {% endif %}
</div>

<div class="section">
  <h2>Other Observations ({{ theme_groups.values()|map('length')|sum }})</h2>
  {% if theme_groups %}
    {% for theme, group in theme_groups.items() %}
      <div class="group">
        <div class="group-title">{{ theme }} — {{ group|length }} note{{ '' if group|length == 1 else 's' }}</div>
        {% for n in group %}
          <div class="card">
            <div class="card-summary">{{ n.classification.summary_one_line }}</div>
            <div class="card-text">{{ n.text }}</div>
            {% if n.media %}
              <div class="media-grid">
                {% for m in n.media %}
                  {% if m.kind == 'image' %}<img src="media/{{ m.filename }}" alt="" onclick="window.open(this.src)">{% endif %}
                {% endfor %}
              </div>
            {% endif %}
            <div class="card-meta">{{ n.to_dict()['ts_sast'] }}</div>
          </div>
        {% endfor %}
      </div>
    {% endfor %}
  {% else %}
    <p class="empty">No other observations logged this week.</p>
  {% endif %}
</div>

<div class="footer">
  Olympic Paints Weekly Sales Report · {{ iso_week }}
</div>

<script>
const OLY_THEMES=['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t,btn){
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme',t);
  document.querySelectorAll('.theme-bar button').forEach(b=>b.classList.toggle('active',b===btn));
}
</script>
</body>
</html>
```

**Note for the implementing engineer:** the `:root` and `.theme-*` blocks above are abbreviated for plan length. Before committing, expand them with the full CSS token block from `CLAUDE.md` (the `.theme-light`, `.theme-dark`, `.theme-brand`, `.theme-navy` blocks verbatim).

- [ ] **Step 5: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_render.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/render.py" \
            "1.Projects/Weekly Sales Report/weekly/templates/report.html.j2" \
            "1.Projects/Weekly Sales Report/tests/test_render.py"
git commit -m "feat(weekly): render.py + report.html.j2 (Olympic navy theme)"
```

---

### Task 10: `debounce.py` — 5-second rebuild scheduler

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/debounce.py` (overwrites placeholder)
- Create: `1.Projects/Weekly Sales Report/tests/test_debounce.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_debounce.py
import time
from weekly.debounce import Debouncer


def test_single_call_fires_after_delay():
    calls = []
    d = Debouncer(delay_seconds=0.2, fn=lambda: calls.append(1))
    d.schedule()
    time.sleep(0.35)
    assert len(calls) == 1


def test_burst_collapses_to_one_call():
    calls = []
    d = Debouncer(delay_seconds=0.2, fn=lambda: calls.append(1))
    for _ in range(8):
        d.schedule()
        time.sleep(0.02)
    time.sleep(0.5)
    assert len(calls) == 1


def test_two_separate_calls_fire_twice():
    calls = []
    d = Debouncer(delay_seconds=0.2, fn=lambda: calls.append(1))
    d.schedule()
    time.sleep(0.4)
    d.schedule()
    time.sleep(0.4)
    assert len(calls) == 2


def test_exception_in_fn_does_not_crash_subsequent_schedules():
    calls = []
    def fn():
        if not calls:
            calls.append("err")
            raise RuntimeError("boom")
        calls.append("ok")
    d = Debouncer(delay_seconds=0.1, fn=fn)
    d.schedule()
    time.sleep(0.2)
    d.schedule()
    time.sleep(0.2)
    assert calls == ["err", "ok"]
```

- [ ] **Step 2: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_debounce.py -v`
Expected: FAIL — class missing.

- [ ] **Step 3: Write implementation**

```python
# weekly/debounce.py
"""5-second debouncer for the rebuild trigger.

A burst of intake calls collapses into a single rebuild. Thread-safe.
"""
from __future__ import annotations
import threading
import traceback
from typing import Callable

_global_debouncer = None


class Debouncer:
    def __init__(self, *, delay_seconds: float, fn: Callable[[], None]):
        self.delay = delay_seconds
        self.fn = fn
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _run(self):
        try:
            self.fn()
        except Exception:
            traceback.print_exc()

    def schedule(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.delay, self._run)
            self._timer.daemon = True
            self._timer.start()


def _default_rebuild():
    """Imported lazily so debounce.py has no compile-report dependency at import time."""
    from weekly.compile_report import run_for_current_week
    run_for_current_week()


def schedule_rebuild() -> None:
    """Module-level convenience: lazily build a single global Debouncer."""
    global _global_debouncer
    if _global_debouncer is None:
        _global_debouncer = Debouncer(delay_seconds=5.0, fn=_default_rebuild)
    _global_debouncer.schedule()
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_debounce.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/debounce.py" \
            "1.Projects/Weekly Sales Report/tests/test_debounce.py"
git commit -m "feat(weekly): debounce.py — 5s rebuild debouncer (thread-safe, fault-tolerant)"
```

---

### Task 11: `compile_report.py` — full pipeline

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/compile_report.py`
- Create: `1.Projects/Weekly Sales Report/tests/test_compile_report.py`
- Create: `1.Projects/Weekly Sales Report/tests/fixtures/_test_W00/notes/*.json` (5 fixture files)

- [ ] **Step 1: Write fixture notes (5 sample notes for the test week)**

Create 5 JSON files at `tests/fixtures/_test_W00/notes/`. Use these exact contents — the test asserts against them:

```json
// tests/fixtures/_test_W00/notes/2026-01-05T09-00-00_aaaa.json
{
  "id": "2026-01-05T09-00-00_aaaa",
  "ts_utc": "2026-01-05T07:00:00+00:00",
  "ts_sast": "2026-01-05T09:00:00+02:00",
  "iso_week": "2026-W02",
  "source": "telegram",
  "source_meta": {},
  "text": "AC says customer wants bigger discount on Pick & Save",
  "hashtags": ["#rep:AC"],
  "media": [],
  "classification": null,
  "_compile_state": "pending",
  "_notion_state": "synced"
}
```
```json
// tests/fixtures/_test_W00/notes/2026-01-05T10-00-00_bbbb.json
{
  "id": "2026-01-05T10-00-00_bbbb",
  "ts_utc": "2026-01-05T08:00:00+00:00",
  "ts_sast": "2026-01-05T10:00:00+02:00",
  "iso_week": "2026-W02",
  "source": "telegram",
  "source_meta": {},
  "text": "Batch 2026-PVA-117 viscosity too high — site complaint",
  "hashtags": ["#quality"],
  "media": [],
  "classification": null,
  "_compile_state": "pending",
  "_notion_state": "synced"
}
```
```json
// tests/fixtures/_test_W00/notes/2026-01-05T11-00-00_cccc.json
{
  "id": "2026-01-05T11-00-00_cccc",
  "ts_utc": "2026-01-05T09:00:00+00:00",
  "ts_sast": "2026-01-05T11:00:00+02:00",
  "iso_week": "2026-W02",
  "source": "folder",
  "source_meta": {},
  "text": "Idea: open a depot in Tzaneen",
  "hashtags": [],
  "media": [],
  "classification": null,
  "_compile_state": "pending",
  "_notion_state": "synced"
}
```
```json
// tests/fixtures/_test_W00/notes/2026-01-05T12-00-00_dddd.json
{
  "id": "2026-01-05T12-00-00_dddd",
  "ts_utc": "2026-01-05T10:00:00+00:00",
  "ts_sast": "2026-01-05T12:00:00+02:00",
  "iso_week": "2026-W02",
  "source": "telegram",
  "source_meta": {},
  "text": "Competitor X dropped Pick & Save equivalent by R30 in Mokopane",
  "hashtags": [],
  "media": [],
  "classification": null,
  "_compile_state": "pending",
  "_notion_state": "synced"
}
```
```json
// tests/fixtures/_test_W00/notes/2026-01-05T13-00-00_eeee.json
{
  "id": "2026-01-05T13-00-00_eeee",
  "ts_utc": "2026-01-05T11:00:00+00:00",
  "ts_sast": "2026-01-05T13:00:00+02:00",
  "iso_week": "2026-W02",
  "source": "telegram",
  "source_meta": {},
  "text": "Competitor Y running 2-for-1 in Polokwane",
  "hashtags": [],
  "media": [],
  "classification": null,
  "_compile_state": "pending",
  "_notion_state": "synced"
}
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_compile_report.py
import json
import shutil
from pathlib import Path
import pytest
from weekly.compile_report import compile_week
from weekly.classifier import FakeClaudeClient


@pytest.fixture
def populated_week(tmp_path):
    src = Path(__file__).parent / "fixtures" / "_test_W00"
    dst = tmp_path / "2026-W02"
    shutil.copytree(src, dst)
    return tmp_path


def _fake_client():
    return FakeClaudeClient(
        classify_response=[
            {"id": "2026-01-05T09-00-00_aaaa", "section": "rep_feedback",
             "subject": "AC / Pick & Save", "summary_one_line": "AC reports discount pressure",
             "tags_inferred": ["discount", "pick_save"]},
            {"id": "2026-01-05T10-00-00_bbbb", "section": "quality_ops",
             "subject": "Batch 2026-PVA-117 viscosity",
             "summary_one_line": "Viscosity complaint on batch 117",
             "tags_inferred": ["pva", "viscosity"]},
            {"id": "2026-01-05T11-00-00_cccc", "section": "other",
             "subject": "Tzaneen depot idea",
             "summary_one_line": "Idea: open depot in Tzaneen",
             "tags_inferred": ["depot", "tzaneen"]},
            {"id": "2026-01-05T12-00-00_dddd", "section": "other",
             "subject": "Competitor X price drop",
             "summary_one_line": "Competitor X cut R30 in Mokopane",
             "tags_inferred": ["competitor", "mokopane"]},
            {"id": "2026-01-05T13-00-00_eeee", "section": "other",
             "subject": "Competitor Y 2-for-1",
             "summary_one_line": "Competitor Y 2-for-1 in Polokwane",
             "tags_inferred": ["competitor", "polokwane"]},
        ],
        cluster_response=[
            {"id": "2026-01-05T11-00-00_cccc", "theme_label": "Product ideas"},
            {"id": "2026-01-05T12-00-00_dddd", "theme_label": "Competitor activity"},
            {"id": "2026-01-05T13-00-00_eeee", "theme_label": "Competitor activity"},
        ],
    )


def test_compile_writes_report_html(populated_week):
    out = compile_week(
        week_dir=populated_week / "2026-W02",
        client=_fake_client(),
        exec_summary_bullets=["test summary"],
        locked=False,
    )
    assert out.exists()
    assert out.name == "report.html"
    html = out.read_text(encoding="utf-8")
    assert "AC reports discount pressure" in html
    assert "Viscosity complaint on batch 117" in html
    assert "Competitor activity" in html
    assert "Product ideas" in html


def test_compile_writes_classification_back_to_json(populated_week):
    compile_week(week_dir=populated_week / "2026-W02", client=_fake_client(),
                 exec_summary_bullets=[], locked=False)
    notes_dir = populated_week / "2026-W02" / "notes"
    payload = json.loads((notes_dir / "2026-01-05T09-00-00_aaaa.json").read_text(encoding="utf-8"))
    assert payload["_compile_state"] == "classified"
    assert payload["classification"]["section"] == "rep_feedback"


def test_compile_is_idempotent_on_second_run(populated_week):
    fake = _fake_client()
    compile_week(week_dir=populated_week / "2026-W02", client=fake,
                 exec_summary_bullets=[], locked=False)
    first_call_count = fake.classify_calls
    compile_week(week_dir=populated_week / "2026-W02", client=fake,
                 exec_summary_bullets=[], locked=False)
    # Second run should NOT re-classify already-classified notes
    assert fake.classify_calls == first_call_count


def test_compile_writes_locked_html_when_locked_true(populated_week):
    out = compile_week(week_dir=populated_week / "2026-W02", client=_fake_client(),
                        exec_summary_bullets=[], locked=True)
    assert out.name == "report_locked.html"
    assert (populated_week / "2026-W02" / "report_locked.html").exists()
```

- [ ] **Step 3: Run test, confirm failure**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_compile_report.py -v`
Expected: FAIL — module missing.

- [ ] **Step 4: Write implementation**

```python
# weekly/compile_report.py
"""End-to-end compile: load → classify → cluster → render → write."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from weekly.note_model import Note
from weekly.classifier import classify_batch, cluster_other, ClaudeClient, AnthropicClaudeClient
from weekly.render import render_report
from weekly.week_paths import paths_for


def _period_label(iso_week: str) -> str:
    """Turn '2026-W21' into '18 May – 24 May 2026'."""
    year_s, w_s = iso_week.split("-W")
    year, week = int(year_s), int(w_s)
    monday = datetime.fromisocalendar(year, week, 1)
    sunday = datetime.fromisocalendar(year, week, 7)
    return f"{monday.strftime('%-d %b')} – {sunday.strftime('%-d %b %Y')}"


def _generate_exec_summary(notes: list[Note], client: ClaudeClient | None) -> list[str]:
    """Cheap deterministic summary in Phase 1 — Claude-written summary is a hook for later."""
    if not notes:
        return []
    n_rep = sum(1 for n in notes if (n.classification or {}).get("section") == "rep_feedback")
    n_quality = sum(1 for n in notes if (n.classification or {}).get("section") == "quality_ops")
    n_other = sum(1 for n in notes if (n.classification or {}).get("section") == "other")
    return [
        f"{len(notes)} notes captured this week.",
        f"{n_rep} rep-feedback items, {n_quality} quality/ops items, {n_other} other observations.",
    ]


def _load_notes(notes_dir: Path) -> list[Note]:
    notes: list[Note] = []
    for p in sorted(notes_dir.glob("*.json")):
        notes.append(Note.from_dict(json.loads(p.read_text(encoding="utf-8"))))
    return notes


def _save_notes(notes: list[Note], notes_dir: Path) -> None:
    for n in notes:
        path = notes_dir / f"{n.id}.json"
        path.write_text(json.dumps(n.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def compile_week(
    *, week_dir: Path, client: ClaudeClient, exec_summary_bullets: list[str] | None = None,
    locked: bool = False,
) -> Path:
    iso_week = week_dir.name
    notes_dir = week_dir / "notes"
    notes = _load_notes(notes_dir)
    classify_batch(notes, client=client)
    cluster_other(notes, client=client)
    _save_notes(notes, notes_dir)

    bullets = exec_summary_bullets if exec_summary_bullets is not None else _generate_exec_summary(notes, client)
    html = render_report(
        iso_week=iso_week,
        period_label=_period_label(iso_week),
        notes=notes,
        exec_summary_bullets=bullets,
        locked=locked,
    )
    target = week_dir / ("report_locked.html" if locked else "report.html")
    target.write_text(html, encoding="utf-8")
    return target


def run_for_current_week() -> Path:
    """Called by debouncer. Uses real Claude client + real config."""
    from weekly.config import Config
    cfg = Config.from_env()
    paths = paths_for(datetime.now(timezone.utc), root=cfg.project_root)
    paths.ensure_dirs()
    client = AnthropicClaudeClient(api_key=cfg.anthropic_api_key)
    return compile_week(week_dir=paths.week_dir, client=client, locked=False)
```

**Note on `%-d`:** that strftime token is POSIX-only. On Windows use `%#d`. Implementing engineer should swap based on platform — or pre-format manually:
```python
return f"{int(monday.strftime('%d'))} {monday.strftime('%b')} – {int(sunday.strftime('%d'))} {sunday.strftime('%b %Y')}"
```

- [ ] **Step 5: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_compile_report.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/compile_report.py" \
            "1.Projects/Weekly Sales Report/tests/test_compile_report.py" \
            "1.Projects/Weekly Sales Report/tests/fixtures/_test_W00/"
git commit -m "feat(weekly): compile_report.py — full classify→cluster→render pipeline"
```

---

### Task 12: `folder_watcher.py` — watchdog daemon

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/folder_watcher.py`

- [ ] **Step 1: Write implementation**

```python
# weekly/folder_watcher.py
"""Long-running watchdog daemon. Routes file drops in 0.Inbox/weekly/ → note_intake.ingest_file()."""
from __future__ import annotations
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import truststore
truststore.inject_into_ssl()

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from weekly.config import Config
from weekly.note_intake import ingest_file


class InboxHandler(FileSystemEventHandler):
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.name.startswith(".") or path.name == ".gitkeep":
            return
        # Small delay so the file finishes writing
        time.sleep(0.5)
        try:
            note = ingest_file(
                file_path=path,
                caption=None,
                source="folder",
                source_meta={"path": str(path)},
                now=datetime.now(timezone.utc),
                root=self.project_root,
            )
            print(f"[watcher] ingested {path.name} → {note.id}")
            # Move source file out of the watch dir so it isn't re-processed
            archived = path.parent / "Archived"
            archived.mkdir(exist_ok=True)
            path.rename(archived / path.name)
        except Exception as e:
            print(f"[watcher] FAILED to ingest {path}: {e}", file=sys.stderr)


def main() -> int:
    cfg = Config.from_env()
    handler = InboxHandler(cfg.project_root)
    obs = Observer()
    obs.schedule(handler, str(cfg.inbox_dir), recursive=False)
    obs.start()
    print(f"[watcher] watching {cfg.inbox_dir}")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Manual smoke test**

Set up `.env` first (real values from PULSE `.env`), then run:
```bash
cd "1.Projects/Weekly Sales Report"
python -m weekly.folder_watcher
```
In a second shell, drop a small text file into `0.Inbox/weekly/`:
```bash
echo "test note" > "0.Inbox/weekly/manual_test.txt"
```
Expected: watcher logs `[watcher] ingested manual_test.txt → <id>` and the file moves to `0.Inbox/weekly/Archived/`. A new JSON note exists in `1.Projects/Weekly Sales Report/<current ISO week>/notes/`.

- [ ] **Step 3: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/folder_watcher.py"
git commit -m "feat(weekly): folder_watcher.py — watchdog daemon routes drops to intake"
```

---

### Task 13: `telegram_listener.py` — inbound long-polling

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/telegram_listener.py`

- [ ] **Step 1: Write implementation**

```python
# weekly/telegram_listener.py
"""Long-polling inbound Telegram listener for Quintus's chat only.

Routes text → note_intake.ingest_text(), media → ingest_file().
The PULSE bot continues to handle its own outbound traffic; we only listen
for messages from the configured chat ID.
"""
from __future__ import annotations
import os
import sys
import time
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import requests
import truststore
truststore.inject_into_ssl()

from weekly.config import Config
from weekly.note_intake import ingest_text, ingest_file

POLL_TIMEOUT = 30


def _api(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


def _file_api(token: str, path: str) -> str:
    return f"https://api.telegram.org/file/bot{token}/{path}"


def _largest_photo(message: dict) -> dict | None:
    photos = message.get("photo")
    if not photos:
        return None
    return max(photos, key=lambda p: p.get("file_size", 0))


def _download_file(token: str, file_id: str, suggested_name: str) -> Path:
    meta = requests.get(_api(token, "getFile"), params={"file_id": file_id}, timeout=15).json()
    file_path = meta["result"]["file_path"]
    url = _file_api(token, file_path)
    suffix = Path(file_path).suffix or Path(suggested_name).suffix
    out = Path(tempfile.mkdtemp()) / (suggested_name + suffix)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        out.write_bytes(r.content)
    return out


def handle_message(message: dict, cfg: Config) -> None:
    chat_id = str(message.get("chat", {}).get("id", ""))
    if chat_id != cfg.quintus_chat_id:
        return
    msg_id = message.get("message_id")
    now = datetime.now(timezone.utc)
    src_meta = {"chat_id": chat_id, "message_id": msg_id,
                "forwarded_from": message.get("forward_from", {}).get("id")}

    photo = _largest_photo(message)
    document = message.get("document")
    voice = message.get("voice")
    video = message.get("video")

    if photo or document or voice or video:
        caption = message.get("caption") or ""
        file_id = (photo or document or voice or video)["file_id"]
        suggested = (document or {}).get("file_name") or f"tg_{msg_id}"
        tmp = _download_file(cfg.telegram_bot_token, file_id, suggested)
        ingest_file(
            file_path=tmp, caption=caption, source="telegram",
            source_meta=src_meta, now=now, root=cfg.project_root,
        )
    else:
        text = message.get("text") or ""
        if not text.strip():
            return
        ingest_text(
            text=text, hashtags=None, source="telegram",
            source_meta=src_meta, now=now, root=cfg.project_root,
        )


def poll_forever(cfg: Config) -> None:
    offset = 0
    print(f"[telegram] listening for chat {cfg.quintus_chat_id}", flush=True)
    while True:
        try:
            resp = requests.get(
                _api(cfg.telegram_bot_token, "getUpdates"),
                params={"timeout": POLL_TIMEOUT, "offset": offset, "allowed_updates": ["message"]},
                timeout=POLL_TIMEOUT + 10,
            )
            data = resp.json()
            for u in data.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message")
                if msg:
                    try:
                        handle_message(msg, cfg)
                    except Exception as e:
                        print(f"[telegram] handle_message error: {e}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"[telegram] poll error: {e}", file=sys.stderr)
            time.sleep(5)


def main() -> int:
    cfg = Config.from_env()
    poll_forever(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Conflict note for the engineer:** PULSE may have its own `getUpdates` consumer. Telegram allows ONE long-poller per token at a time — if PULSE is currently polling the same bot, this listener will see "Conflict: terminated by other getUpdates" errors. Check `pulse_telegram.py` and verify PULSE only **sends** (does not poll). If PULSE does poll, we need to either (a) merge both consumers into a single bot dispatcher or (b) use webhooks instead. As of inspection (Task 13 launch), `pulse_telegram.py` is send-only — confirm this still holds before deploying.

- [ ] **Step 2: Manual smoke test**

```bash
cd "1.Projects/Weekly Sales Report"
python -m weekly.telegram_listener
```
On phone: DM the PULSE bot with `#test this is a captured note`.
Expected: listener logs the message and a new JSON note appears in the current week's `notes/`.

- [ ] **Step 3: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/telegram_listener.py"
git commit -m "feat(weekly): telegram_listener.py — long-poll inbound from Quintus's chat only"
```

---

### Task 14: `portal_deploy.py` — copy HTML+media to Vercel portal repo

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/portal_deploy.py`

- [ ] **Step 1: Locate the portal repo and confirm path**

Run: `ls "C:\Users\quint\olympic-paints-portal" 2>&1 | head -5` (or whatever the portal repo path is — per memory `reference_olympic_portal_v1.md`).
If the path differs, update `PORTAL_REPO_PATH` in `.env`.

- [ ] **Step 2: Write implementation**

```python
# weekly/portal_deploy.py
"""Copy the week's report HTML + media into the Vercel portal repo and commit/push.

Expects the portal repo layout to expose /public/weekly/<iso_week>/ via Next.js static files.
"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path


def deploy_current(*, week_dir: Path, portal_repo: Path, iso_week: str, locked: bool = False) -> None:
    target_root = portal_repo / "public" / "weekly"
    target_root.mkdir(parents=True, exist_ok=True)

    # Per-week archive
    per_week = target_root / iso_week
    per_week.mkdir(parents=True, exist_ok=True)
    src_html = week_dir / ("report_locked.html" if locked else "report.html")
    if src_html.exists():
        shutil.copy2(src_html, per_week / "index.html")

    # media
    src_media = week_dir / "media"
    if src_media.is_dir():
        dst_media = per_week / "media"
        if dst_media.exists():
            shutil.rmtree(dst_media)
        shutil.copytree(src_media, dst_media)

    # logo
    logo = Path(__file__).resolve().parent.parent.parent.parent / "3.Resources" / \
        "9. Brand Assets & Images" / "Misc Pictures" / "Olympic Paints Logo Digital.jpg"
    if logo.exists():
        shutil.copy2(logo, per_week / "logo.jpg")

    # "current" alias points to this week for the /weekly route default
    current = target_root / "current"
    if current.exists():
        if current.is_symlink() or current.is_file():
            current.unlink()
        else:
            shutil.rmtree(current)
    shutil.copytree(per_week, current)

    # git commit + push
    _git(portal_repo, "add", "public/weekly")
    rc = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=portal_repo).returncode
    if rc == 0:
        return  # nothing to commit
    _git(portal_repo, "commit", "-m", f"weekly: refresh {iso_week} ({'locked' if locked else 'live'})")
    _git(portal_repo, "push")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True)
```

- [ ] **Step 3: Add the Next.js route to the portal repo**

In the portal repo (separate git checkout), create:
```typescript
// app/weekly/page.tsx
import { redirect } from 'next/navigation';
export default function WeeklyIndex() {
  redirect('/weekly/current/');
}
```

This makes `portal.vercel.app/weekly` redirect to the static HTML at `/public/weekly/current/index.html`. Auth comes for free because the portal middleware already gates everything except `/login`.

Commit + push the portal repo:
```bash
cd "C:\Users\quint\olympic-paints-portal"
git add app/weekly/
git commit -m "weekly: add /weekly route serving static report"
git push
```

- [ ] **Step 4: Wire `portal_deploy.deploy_current` into `compile_report.run_for_current_week`**

Edit `weekly/compile_report.py`. After `compile_week()` returns, call `deploy_current()`:

```python
# weekly/compile_report.py — replace run_for_current_week
def run_for_current_week() -> Path:
    from weekly.config import Config
    from weekly.portal_deploy import deploy_current
    cfg = Config.from_env()
    paths = paths_for(datetime.now(timezone.utc), root=cfg.project_root)
    paths.ensure_dirs()
    client = AnthropicClaudeClient(api_key=cfg.anthropic_api_key)
    out = compile_week(week_dir=paths.week_dir, client=client, locked=False)
    try:
        deploy_current(week_dir=paths.week_dir, portal_repo=cfg.portal_repo_path,
                       iso_week=paths.iso_week, locked=False)
    except Exception as e:
        print(f"[compile] deploy failed (non-fatal): {e}")
    return out
```

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/portal_deploy.py" \
            "1.Projects/Weekly Sales Report/weekly/compile_report.py"
git commit -m "feat(weekly): portal_deploy.py — copy HTML+media+logo to portal, push"
```

---

### Task 15: `send_weekly_email.py` — Friday 07:00 Outlook email

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/send_weekly_email.py`

- [ ] **Step 1: Write implementation**

```python
# weekly/send_weekly_email.py
"""Friday 07:00 SAST: build current report → email to Quintus via Outlook (win32com).

Uses force-flush pattern (see memory feedback_outlook_send_flush.md).
"""
from __future__ import annotations
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import truststore
truststore.inject_into_ssl()

from weekly.classifier import AnthropicClaudeClient
from weekly.compile_report import compile_week
from weekly.config import Config
from weekly.week_paths import paths_for


def _outlook():
    import win32com.client
    return win32com.client.Dispatch("Outlook.Application")


def _send_via_outlook(*, subject: str, html_body: str, attachment: Path, to_addr: str) -> None:
    app = _outlook()
    mail = app.CreateItem(0)
    mail.Subject = subject
    mail.HTMLBody = html_body
    mail.To = to_addr
    mail.Attachments.Add(str(attachment))
    mail.Send()
    # Force-flush: stuck items in Outbox
    namespace = app.GetNamespace("MAPI")
    outbox = namespace.GetDefaultFolder(4)  # olFolderOutbox
    deadline = time.time() + 30
    while time.time() < deadline and outbox.Items.Count > 0:
        for i in range(outbox.Items.Count):
            try:
                outbox.Items[i + 1].Send()
            except Exception:
                pass
        time.sleep(1)


def build_and_send() -> int:
    cfg = Config.from_env()
    now = datetime.now(timezone.utc)
    paths = paths_for(now, root=cfg.project_root)
    paths.ensure_dirs()

    client = AnthropicClaudeClient(api_key=cfg.anthropic_api_key)
    report_path = compile_week(week_dir=paths.week_dir, client=client, locked=False)

    subject = f"Weekly Sales Report — {paths.iso_week} (in-progress snapshot, will lock Sunday)"
    body = (
        f"<p>Live snapshot of the Weekly Sales Report for {paths.iso_week}.</p>"
        f"<p>Open in the portal: "
        f"<a href='https://olympic-paints-portal.vercel.app/weekly/'>portal.vercel.app/weekly</a></p>"
        f"<p>Or open the attached HTML.</p>"
    )

    _send_via_outlook(
        subject=subject, html_body=body, attachment=report_path, to_addr=cfg.quintus_email,
    )

    paths.friday_email_log.write_text(json.dumps({
        "sent_at_utc": now.isoformat(),
        "to": cfg.quintus_email,
        "report_path": str(report_path),
    }, indent=2), encoding="utf-8")
    print(f"[email] sent {report_path.name} to {cfg.quintus_email}")
    return 0


def main() -> int:
    try:
        return build_and_send()
    except Exception as e:
        # Best-effort Telegram alert on failure
        try:
            import requests
            cfg = Config.from_env()
            requests.post(
                f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage",
                json={"chat_id": cfg.quintus_chat_id,
                      "text": f"⚠️ Weekly report email FAILED: {e}"},
                timeout=10,
            )
        except Exception:
            pass
        print(f"[email] FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Manual smoke test (DRY — don't send)**

Inspect that the script imports without errors:
```bash
cd "1.Projects/Weekly Sales Report"
python -c "from weekly.send_weekly_email import build_and_send; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/send_weekly_email.py"
git commit -m "feat(weekly): send_weekly_email.py — Friday 07:00 SAST Outlook send + force-flush"
```

---

### Task 16: `archive_week.py` + `init_new_week.py`

**Files:**
- Create: `1.Projects/Weekly Sales Report/weekly/archive_week.py`
- Create: `1.Projects/Weekly Sales Report/weekly/init_new_week.py`
- Create: `1.Projects/Weekly Sales Report/tests/test_archive_week.py`

- [ ] **Step 1: Write `archive_week.py`**

```python
# weekly/archive_week.py
"""Sunday 23:59 SAST: build report_locked.html, update _archive_index.json."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import truststore
truststore.inject_into_ssl()

from weekly.classifier import AnthropicClaudeClient
from weekly.compile_report import compile_week
from weekly.config import Config
from weekly.portal_deploy import deploy_current
from weekly.week_paths import paths_for


def lock_current_week() -> Path:
    cfg = Config.from_env()
    now = datetime.now(timezone.utc)
    paths = paths_for(now, root=cfg.project_root)
    client = AnthropicClaudeClient(api_key=cfg.anthropic_api_key)
    locked_path = compile_week(week_dir=paths.week_dir, client=client, locked=True)

    # Update archive index
    idx_path = paths.archive_index
    idx = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else []
    if paths.iso_week not in [e["iso_week"] for e in idx]:
        idx.append({
            "iso_week": paths.iso_week,
            "locked_at_utc": now.isoformat(),
            "report_path": str(locked_path.relative_to(cfg.project_root)),
        })
        idx_path.write_text(json.dumps(idx, indent=2), encoding="utf-8")

    try:
        deploy_current(week_dir=paths.week_dir, portal_repo=cfg.portal_repo_path,
                       iso_week=paths.iso_week, locked=True)
    except Exception as e:
        print(f"[archive] deploy failed (non-fatal): {e}", file=sys.stderr)

    print(f"[archive] locked {paths.iso_week}")
    return locked_path


def main() -> int:
    lock_current_week()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Write `init_new_week.py`**

```python
# weekly/init_new_week.py
"""Monday 00:01 SAST: create the new week's empty bucket + week_meta.json."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from weekly.config import Config
from weekly.week_paths import paths_for


def init_current() -> Path:
    cfg = Config.from_env()
    now = datetime.now(timezone.utc)
    paths = paths_for(now, root=cfg.project_root)
    paths.ensure_dirs()
    if not paths.week_meta.exists():
        year, week, _ = now.isocalendar()
        monday = datetime.fromisocalendar(year, week, 1).isoformat()
        sunday = datetime.fromisocalendar(year, week, 7).isoformat()
        paths.week_meta.write_text(json.dumps({
            "iso_week": paths.iso_week,
            "starts_iso": monday,
            "ends_iso": sunday,
            "status": "open",
            "created_at_utc": now.isoformat(),
        }, indent=2), encoding="utf-8")
    print(f"[init] week {paths.iso_week} ready")
    return paths.week_dir


def main() -> int:
    init_current()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_archive_week.py
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import pytest
from weekly.archive_week import lock_current_week
from weekly.init_new_week import init_current
from weekly.classifier import FakeClaudeClient


@pytest.fixture
def cfg_for(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("NOTION_API_TOKEN", "x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("NOTION_WEEKLY_DB_ID", "x")
    monkeypatch.setenv("PORTAL_REPO_PATH", str(tmp_path / "portal_repo"))
    monkeypatch.setenv("WEEKLY_PROJECT_ROOT", str(tmp_path / "wp"))
    monkeypatch.setenv("WEEKLY_INBOX_DIR", str(tmp_path / "in"))
    (tmp_path / "in").mkdir()
    (tmp_path / "wp").mkdir()
    (tmp_path / "portal_repo").mkdir()
    return tmp_path


def test_init_creates_week_meta(cfg_for):
    week_dir = init_current()
    meta = week_dir / "week_meta.json"
    assert meta.exists()
    data = json.loads(meta.read_text(encoding="utf-8"))
    assert data["status"] == "open"


def test_lock_writes_archive_index_and_locked_html(cfg_for, monkeypatch):
    # Seed current week with a fixture note + fake client
    week_dir = init_current()
    notes_dir = week_dir / "notes"
    notes_dir.mkdir(exist_ok=True)
    (notes_dir / "n1.json").write_text(json.dumps({
        "id": "n1",
        "ts_utc": "2026-05-21T12:00:00+00:00",
        "iso_week": week_dir.name,
        "source": "telegram",
        "source_meta": {},
        "text": "test note",
        "hashtags": [],
        "media": [],
        "classification": None,
        "_compile_state": "pending",
        "_notion_state": "synced",
    }), encoding="utf-8")

    fake = FakeClaudeClient(
        classify_response=[{"id": "n1", "section": "rep_feedback", "subject": "X",
                             "summary_one_line": "summary", "tags_inferred": []}],
        cluster_response=[],
    )
    with patch("weekly.archive_week.AnthropicClaudeClient", lambda **_: fake), \
         patch("weekly.archive_week.deploy_current", lambda **_: None):
        out = lock_current_week()

    assert out.name == "report_locked.html"
    idx = json.loads((cfg_for / "wp" / "_archive_index.json").read_text(encoding="utf-8"))
    assert any(e["iso_week"] == week_dir.name for e in idx)
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd "1.Projects/Weekly Sales Report" && pytest tests/test_archive_week.py -v`
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/weekly/archive_week.py" \
            "1.Projects/Weekly Sales Report/weekly/init_new_week.py" \
            "1.Projects/Weekly Sales Report/tests/test_archive_week.py"
git commit -m "feat(weekly): archive_week.py + init_new_week.py + tests"
```

---

### Task 17: Task Scheduler registration

**Files:**
- Create: `1.Projects/Weekly Sales Report/scheduler/register.ps1`
- Create: `1.Projects/Weekly Sales Report/scheduler/unregister.ps1`

**Reminder:** scheduled tasks log to `C:\Users\quint\.claude\logs\weekly-report\` (never OneDrive paths). Save these scripts as **UTF-8 with BOM** per memory `feedback_pulse_scripts_python_m.md`.

- [ ] **Step 1: Write `register.ps1`**

```powershell
# scheduler/register.ps1
# Registers all Weekly Sales Report scheduled jobs.
# Run from an elevated PowerShell prompt: powershell -File register.ps1

$ErrorActionPreference = "Stop"

$ProjectDir = "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Weekly Sales Report"
$LogDir = "C:\Users\quint\.claude\logs\weekly-report"
$Python = "python"  # assumes python on PATH

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Register-WeeklyTask {
    param([string]$Name, [string]$Module, [string]$Trigger, [string]$ExtraTriggerArgs = "")

    $action = New-ScheduledTaskAction `
        -Execute $Python `
        -Argument "-m weekly.$Module" `
        -WorkingDirectory $ProjectDir

    $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
        -StartWhenAvailable -DontStopOnIdleEnd

    $triggerScript = "New-ScheduledTaskTrigger $Trigger $ExtraTriggerArgs"
    $trig = Invoke-Expression $triggerScript

    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trig `
        -Settings $settings -RunLevel Highest -Force | Out-Null
    Write-Host "Registered: $Name"
}

# Friday 07:00 SAST email
Register-WeeklyTask -Name "Olympic — Weekly Report Friday Email" `
    -Module "send_weekly_email" `
    -Trigger "-Weekly -DaysOfWeek Friday -At 07:00"

# Sunday 23:59 SAST archive
Register-WeeklyTask -Name "Olympic — Weekly Report Sunday Lock" `
    -Module "archive_week" `
    -Trigger "-Weekly -DaysOfWeek Sunday -At 23:59"

# Monday 00:01 SAST init
Register-WeeklyTask -Name "Olympic — Weekly Report Monday Init" `
    -Module "init_new_week" `
    -Trigger "-Weekly -DaysOfWeek Monday -At 00:01"

# Notion retry every 5 minutes
Register-WeeklyTask -Name "Olympic — Weekly Report Notion Retry" `
    -Module "notion_retry" `
    -Trigger "-Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([System.TimeSpan]::MaxValue)"

# Folder watcher at boot
Register-WeeklyTask -Name "Olympic — Weekly Report Folder Watcher" `
    -Module "folder_watcher" `
    -Trigger "-AtStartup"

# Telegram listener at boot
Register-WeeklyTask -Name "Olympic — Weekly Report Telegram Listener" `
    -Module "telegram_listener" `
    -Trigger "-AtStartup"

Write-Host "All Weekly Sales Report tasks registered."
```

- [ ] **Step 2: Write `unregister.ps1`**

```powershell
# scheduler/unregister.ps1
$tasks = @(
  "Olympic — Weekly Report Friday Email",
  "Olympic — Weekly Report Sunday Lock",
  "Olympic — Weekly Report Monday Init",
  "Olympic — Weekly Report Notion Retry",
  "Olympic — Weekly Report Folder Watcher",
  "Olympic — Weekly Report Telegram Listener"
)
foreach ($t in $tasks) {
  try { Unregister-ScheduledTask -TaskName $t -Confirm:$false; Write-Host "Removed: $t" }
  catch { Write-Host "Not found: $t" }
}
```

- [ ] **Step 3: Save both as UTF-8 BOM**

Re-save in your editor with the BOM. Verify in PowerShell:
```powershell
[System.IO.File]::ReadAllBytes("scheduler\register.ps1")[0..2]
```
Expected: `239 187 191` (the UTF-8 BOM bytes).

- [ ] **Step 4: Dry-run smoke test**

Don't register yet. Just confirm the script parses:
```powershell
powershell -NoProfile -Command "Get-Content scheduler\register.ps1 | Out-Null; Write-Host 'OK'"
```

- [ ] **Step 5: Commit**

```bash
git add -f "1.Projects/Weekly Sales Report/scheduler/register.ps1" \
            "1.Projects/Weekly Sales Report/scheduler/unregister.ps1"
git commit -m "feat(weekly): scheduler/register.ps1 + unregister.ps1 (6 schtasks jobs)"
```

---

### Task 18: Notion DB creation + end-to-end smoke

**Files:** none — manual setup + smoke test.

- [ ] **Step 1: Manually create the Notion database**

In Notion (Olympic Paints workspace):
1. Create a new full-page database titled "Weekly Sales Notes".
2. Add the 12 columns per spec §5 (Title is the default; add the other 11).
3. Share the database with the "Olympic Paints Automations" integration (database menu → Connections → Add → Olympic Paints Automations).
4. Copy the database ID from the URL (the 32-char hex after the `/` before `?v=`).
5. Add it to `.env` as `NOTION_WEEKLY_DB_ID`.

- [ ] **Step 2: End-to-end smoke run (manual)**

```bash
cd "1.Projects/Weekly Sales Report"

# Init current week
python -m weekly.init_new_week

# Drop a folder file
echo "smoke test note" > "../../0.Inbox/weekly/smoke.txt"

# Start watcher + listener in two shells (or just watcher for now)
python -m weekly.folder_watcher
# (wait for ingestion log line)

# Run a compile manually
python -c "from datetime import datetime, timezone; from weekly.compile_report import run_for_current_week; print(run_for_current_week())"

# Send Friday email (DRY — change to_addr to yourself first, or comment out the Send call)
# python -m weekly.send_weekly_email
```

Expected after `run_for_current_week()`:
- `1.Projects/Weekly Sales Report/<W##>/notes/*.json` contains the smoke note with `classification` populated.
- `1.Projects/Weekly Sales Report/<W##>/report.html` exists and renders cleanly in a browser.
- Notion "Weekly Sales Notes" DB has a new row with Section populated.
- Portal repo has a new commit with the HTML+media+logo under `public/weekly/<W##>/` and `public/weekly/current/`.

- [ ] **Step 3: Register scheduled tasks**

```powershell
powershell -File "1.Projects\Weekly Sales Report\scheduler\register.ps1"
```

Verify in Task Scheduler GUI that all 6 jobs appear.

- [ ] **Step 4: Final commit (no code change — version bump)**

```bash
git add -f "1.Projects/Weekly Sales Report/README.md"
# (edit README to document the manual Notion DB step before committing)
git commit -m "docs(weekly): document Notion DB setup + manual smoke procedure"
```

---

## Self-review notes

**Spec coverage check:**
- §3 Architecture diagram — covered by Tasks 5, 7, 11, 12, 13, 14.
- §4 Components table — every file in the table has a corresponding task.
- §5 Data shape (JSON + folder structure + Notion schema) — Tasks 3, 5, 7.
- §6 Compile algorithm — Task 11 (5-step algorithm matches spec).
- §7 Report layout — Task 9 (Jinja template covers hero, exec summary, 3 sections + empty placeholders).
- §8 Error handling (Notion down, Claude fails, Vercel fails, Outlook not running, watcher crashes, bot crashes) — disk-first persistence (Task 5), retry (Task 8), Telegram alert on email failure (Task 15), restart-on-failure schtasks (Task 17).
- §9 Edge cases — Sunday/Monday boundary covered in Task 2 tests; deleted note natively works because compile re-reads every file; Notion-edit-not-propagated is documented as out-of-scope.
- §10 Scheduled jobs — all 5 jobs + folder watcher + telegram listener registered in Task 17.
- §11 Testing strategy — Tasks 2, 3, 5, 6, 7, 9, 10, 11, 16 all use mocked clients; integration test in Task 11 uses fixture week + FakeClaudeClient.

**Placeholder scan:**
- No "TBD" or "implement later" remain.
- The one abbreviated CSS in Task 9's template is flagged with explicit instruction: "expand with the full CSS token block from CLAUDE.md before committing."
- Windows-specific strftime `%-d` flagged with the Windows-safe alternative in Task 11.

**Type consistency:**
- `Note` dataclass shape matches across Tasks 3, 5, 7, 9, 11, 16.
- `classify_batch(notes, *, client)` and `cluster_other(notes, *, client)` signatures consistent across Tasks 6 and 11.
- `paths_for(dt, *, root)` signature consistent across Tasks 2, 5, 11, 16.
- `deploy_current(*, week_dir, portal_repo, iso_week, locked)` consistent across Tasks 14, 16.
- `mirror_note(note)` returns a `Note` consistently across Tasks 5, 7, 8.

---
