# Transcription Processor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pipeline that watches a drop folder for audio/transcription files, uses Whisper + Claude to produce structured meeting minutes, writes a `.docx`, creates a Notion meeting page, and extracts action items into the Task Database — all in one automated run.

**Architecture:** Single monolithic script (`transcription_processor.py`) handles the full pipeline; a separate lightweight watcher (`transcription_watcher.py`) triggers it on new file drops using `watchdog`. Mirrors the existing HAVEN pipeline pattern exactly.

**Tech Stack:** Python 3.13, openai-whisper (local, `large` model), python-docx, watchdog, requests (Notion API), claude CLI via `.claude/claude_cli_helper.py`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `transcription_processor.py` | Create | Full pipeline: text extraction, Whisper, Claude calls, .docx writer, Notion, action items |
| `transcription_watcher.py` | Create | Folder watcher — triggers processor on new files |
| `run_transcription_watcher.bat` | Create | Task Scheduler launcher for the watcher |
| `0.Inbox/Transcriptions/` | Create dir | Drop zone for input files |
| `0.Inbox/Transcriptions/Archived/` | Create dir | Processed files moved here |
| `0.Inbox/Transcriptions/Failed/` | Create dir | Failed files + .error.txt sidecar |

All paths are relative to `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\`.

---

## Task 1: Bootstrap — dependencies, folders, ffmpeg check

**Files:**
- Create: `transcription_processor.py` (skeleton only)

- [ ] **Step 1: Create the inbox folders**

Run in PowerShell:
```powershell
New-Item -ItemType Directory -Force "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\Transcriptions"
New-Item -ItemType Directory -Force "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\Transcriptions\Archived"
New-Item -ItemType Directory -Force "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\Transcriptions\Failed"
```

Expected: Three directories created (or already exist).

- [ ] **Step 2: Install Python dependencies**

Run:
```
pip install openai-whisper python-docx watchdog
```

Note: `ffmpeg` must be on PATH. Test with `ffmpeg -version`. If missing:
```
winget install ffmpeg
```
Then restart the terminal so PATH updates.

- [ ] **Step 3: Write the script skeleton with config and startup checks**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\transcription_processor.py`:

```python
#!/usr/bin/env python3
"""
Transcription Processor — Olympic Paints
Watches 0.Inbox/Transcriptions/ for audio/transcript files, structures them
into meeting minutes, writes .docx, creates Notion meeting page, extracts
action items into Task Database.

Usage:
    python transcription_processor.py --file "path/to/file.mp3"
    python transcription_processor.py --inbox
"""

import os
import sys
import json
import shutil
import logging
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# ─── sys.path for claude_cli_helper ───────────────────────────────────────────
_HELPER_DIR = Path(__file__).parent / ".claude"
if str(_HELPER_DIR) not in sys.path:
    sys.path.insert(0, str(_HELPER_DIR))

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    print("ERROR: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)

try:
    from claude_cli_helper import call_claude_cli, ClaudeCliError
except ImportError:
    print("ERROR: .claude/claude_cli_helper.py not found")
    sys.exit(1)

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_DIR             = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
TRANSCRIPTION_INBOX  = BASE_DIR / "0.Inbox" / "Transcriptions"
MINUTES_OUTPUT_DIR   = BASE_DIR / "3.Resources" / "3. Meeting Minutes"
LOG_DIR              = BASE_DIR / "logs"

MEETING_DATABASE_ID    = "247ff48d2bb18009979bd25bac9fe72e"
TASK_DATABASE_ID       = "247ff48d2bb1800ca00aca3b59f789eb"
ACTION_STATE_COMMITTED = "301ff48d2bb180af869fdc19b6f6b062"

NOTION_API_URL     = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"

WHISPER_MODEL        = "large"
METADATA_MODEL       = "claude-haiku-4-5-20251001"
STRUCTURING_MODEL    = "claude-sonnet-4-6"
MERGE_MODEL          = "claude-haiku-4-5-20251001"
CHUNK_WORDS          = 3000
CHUNK_OVERLAP_WORDS  = 200
MIN_TRANSCRIPT_WORDS = 50
TELEGRAM_CHAT_ID     = "8042233389"

AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".aac", ".wma", ".ogg"}
TEXT_EXTENSIONS  = {".txt", ".docx", ".doc", ".vtt", ".srt", ".pdf"}
ALL_EXTENSIONS   = AUDIO_EXTENSIONS | TEXT_EXTENSIONS

VALID_AREAS = {"Olympic", "Timion", "Quintus", "Flomatic", "GOD"}

# ─── Startup checks ───────────────────────────────────────────────────────────

def _check_prerequisites() -> None:
    """Exit early with clear messages if required tools are missing."""
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg not found on PATH.")
        print("Install with: winget install ffmpeg")
        print("Then restart your terminal.")
        sys.exit(1)

    notion_token = os.getenv("NOTION_API_TOKEN")
    if not notion_token:
        print("ERROR: NOTION_API_TOKEN environment variable not set.")
        sys.exit(1)

# ─── Logging ──────────────────────────────────────────────────────────────────

def _setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"transcription_processor_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)

logger = _setup_logging()
```

- [ ] **Step 4: Verify the skeleton imports without error**

Run:
```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\transcription_processor.py"
```

Expected output (since no `__main__` block yet, it will just exit cleanly — no ImportError or missing ffmpeg/token errors if both are configured).

- [ ] **Step 5: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add transcription_processor.py skeleton with config and prereq checks"
```

---

## Task 2: Text extraction from all input formats

**Files:**
- Modify: `transcription_processor.py` — add `extract_text_from_file()` function

- [ ] **Step 1: Add the text extraction function**

Append to `transcription_processor.py` after the logging setup block:

```python
# ─── Text Extraction ──────────────────────────────────────────────────────────

def _extract_text_docx(path: Path) -> str:
    from docx import Document as _Doc
    doc = _Doc(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_text_pdf(path: Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        pass
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        return "\n".join(page.get_text() for page in doc)
    except ImportError:
        pass
    raise RuntimeError(
        "No PDF library available. Install pdfplumber: pip install pdfplumber"
    )


def _extract_text_vtt(path: Path) -> str:
    """Strip VTT timestamps and return plain speaker-labelled text."""
    lines, result = path.read_text(encoding="utf-8", errors="ignore").splitlines(), []
    for line in lines:
        # Skip WEBVTT header, timestamp lines (contain '-->'), and blank lines
        if line.startswith("WEBVTT") or "-->" in line or not line.strip():
            continue
        # Skip pure numeric cue identifiers
        if re.match(r"^\d+$", line.strip()):
            continue
        result.append(line)
    return "\n".join(result)


def _extract_text_srt(path: Path) -> str:
    """Strip SRT timestamps and cue numbers; return plain text."""
    lines, result = path.read_text(encoding="utf-8", errors="ignore").splitlines(), []
    for line in lines:
        if re.match(r"^\d+$", line.strip()):
            continue
        if "-->" in line:
            continue
        if line.strip():
            result.append(line)
    return "\n".join(result)


def extract_text_from_file(path: Path) -> str:
    """
    Return plain text from a text/document/transcript file.
    Raises RuntimeError if the format is unsupported or unreadable.
    """
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix in (".docx", ".doc"):
        return _extract_text_docx(path)
    if suffix == ".pdf":
        return _extract_text_pdf(path)
    if suffix == ".vtt":
        return _extract_text_vtt(path)
    if suffix == ".srt":
        return _extract_text_srt(path)
    raise RuntimeError(f"Unsupported text format: {suffix}")
```

- [ ] **Step 2: Write a quick inline test**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_text_extraction.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcription_processor import _extract_text_vtt, _extract_text_srt

VTT_SAMPLE = """WEBVTT

1
00:00:01.000 --> 00:00:03.000
Quintus Lategan: Good morning everyone.

2
00:00:04.000 --> 00:00:06.000
Aboo Cassim: Morning, ready to start."""

SRT_SAMPLE = """1
00:00:01,000 --> 00:00:03,000
Quintus Lategan: Good morning everyone.

2
00:00:04,000 --> 00:00:06,000
Aboo Cassim: Morning, ready to start."""


def test_vtt_strips_timestamps():
    tmp = Path("tmp_test.vtt")
    tmp.write_text(VTT_SAMPLE, encoding="utf-8")
    result = _extract_text_vtt(tmp)
    tmp.unlink()
    assert "Quintus Lategan: Good morning everyone." in result
    assert "-->" not in result
    assert "WEBVTT" not in result


def test_srt_strips_timestamps():
    tmp = Path("tmp_test.srt")
    tmp.write_text(SRT_SAMPLE, encoding="utf-8")
    result = _extract_text_srt(tmp)
    tmp.unlink()
    assert "Aboo Cassim: Morning, ready to start." in result
    assert "-->" not in result


if __name__ == "__main__":
    test_vtt_strips_timestamps()
    test_srt_strips_timestamps()
    print("All text extraction tests passed.")
```

- [ ] **Step 3: Run the tests**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_text_extraction.py"
```

Expected: `All text extraction tests passed.`

- [ ] **Step 4: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py tests/test_text_extraction.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add text extraction for txt/docx/pdf/vtt/srt formats"
```

---

## Task 3: Whisper audio transcription

**Files:**
- Modify: `transcription_processor.py` — add `transcribe_audio()` function

- [ ] **Step 1: Add the Whisper transcription function**

Append to `transcription_processor.py`:

```python
# ─── Audio Transcription (Whisper) ────────────────────────────────────────────

def transcribe_audio(path: Path) -> str:
    """
    Transcribe an audio/video file using local Whisper (large model).
    Returns plain text transcript. Raises RuntimeError on failure.
    """
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "openai-whisper not installed. Run: pip install openai-whisper"
        )

    logger.info(f"  Loading Whisper model '{WHISPER_MODEL}' (first load may take ~30s)...")
    model = whisper.load_model(WHISPER_MODEL)
    logger.info(f"  Transcribing {path.name}...")
    result = model.transcribe(str(path), verbose=False)
    segments = result.get("segments", [])
    if not segments:
        return result.get("text", "").strip()
    # Preserve speaker turns as line breaks (Whisper base doesn't diarise,
    # but each segment is a natural utterance boundary)
    return "\n".join(seg["text"].strip() for seg in segments if seg.get("text", "").strip())
```

- [ ] **Step 2: Write a test using a tiny synthetic WAV**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_whisper.py`:

```python
"""
Smoke test: create a 1-second silent WAV and confirm Whisper runs without error.
We can't assert on transcript content (silent audio), but we verify the function
returns a string without raising.
"""
import sys
import struct
import wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcription_processor import transcribe_audio


def _make_silent_wav(path: Path, duration_secs: float = 1.0, sample_rate: int = 16000):
    n_frames = int(sample_rate * duration_secs)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_frames)


def test_transcribe_silent_wav():
    tmp = Path("tmp_silent.wav")
    _make_silent_wav(tmp)
    try:
        result = transcribe_audio(tmp)
        assert isinstance(result, str), f"Expected str, got {type(result)}"
        print(f"  Transcript (silent): {result!r}")
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    test_transcribe_silent_wav()
    print("Whisper smoke test passed.")
```

- [ ] **Step 3: Run the test**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_whisper.py"
```

Expected: `Whisper smoke test passed.` (may take 30-60s on first run while downloading the `large` model weights ~2.9GB).

- [ ] **Step 4: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py tests/test_whisper.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add Whisper large audio transcription"
```

---

## Task 4: Metadata extraction via Claude Haiku

**Files:**
- Modify: `transcription_processor.py` — add `extract_metadata()` function and interactive fallback

- [ ] **Step 1: Add the metadata extraction function**

Append to `transcription_processor.py`:

```python
# ─── Metadata Extraction ──────────────────────────────────────────────────────

_METADATA_SYSTEM = (
    "You are a meeting metadata extractor. "
    "Return ONLY a valid JSON object — no prose, no markdown fences. "
    "Keys: title (str), date (ISO date YYYY-MM-DD or null), "
    "attendees (list of str), location (str or null). "
    "Extract from the transcript. If a field cannot be found, use null."
)

_METADATA_PROMPT = """\
Extract meeting metadata from this transcript.

TRANSCRIPT:
{transcript}

Return JSON with keys: title, date, attendees (list), location.
If a field is absent from the transcript use null.
Return ONLY the raw JSON object."""


def extract_metadata(transcript: str, file_path: Path) -> Dict[str, Any]:
    """
    Use Claude Haiku to extract title, date, attendees, location from transcript.
    Applies fallbacks: filename stem for title, file ctime for date.
    Returns dict: {title, date, attendees, location}.
    """
    try:
        meta = call_claude_cli(
            system_prompt=_METADATA_SYSTEM,
            user_prompt=_METADATA_PROMPT.format(transcript=transcript[:12000]),
            model=METADATA_MODEL,
            max_seconds=120,
        )
        if not isinstance(meta, dict):
            raise ClaudeCliError(f"Expected dict, got {type(meta).__name__}")
    except ClaudeCliError as e:
        logger.warning(f"  Metadata extraction failed: {e} — using fallbacks")
        meta = {}

    # Fallbacks
    if not meta.get("title"):
        meta["title"] = file_path.stem.replace("_", " ").replace("-", " ").title()
    if not meta.get("date"):
        ctime = datetime.fromtimestamp(file_path.stat().st_ctime)
        meta["date"] = ctime.strftime("%Y-%m-%d")
    if not meta.get("attendees"):
        meta["attendees"] = []
    if not meta.get("location"):
        meta["location"] = None

    logger.info(f"  Metadata: title='{meta['title']}', date={meta['date']}, attendees={meta['attendees']}")
    return meta


def prompt_missing_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interactively prompt the user to fill in any null/empty metadata fields.
    Only called in --file (manual) mode.
    """
    if not meta.get("title") or meta["title"].strip() == "":
        val = input(f"  Meeting title [{meta.get('title', '')}]: ").strip()
        if val:
            meta["title"] = val

    if not meta.get("date"):
        val = input(f"  Meeting date (YYYY-MM-DD) [{meta.get('date', '')}]: ").strip()
        if val:
            meta["date"] = val

    if not meta.get("attendees"):
        val = input("  Attendees (comma-separated, or Enter to skip): ").strip()
        if val:
            meta["attendees"] = [a.strip() for a in val.split(",")]

    return meta
```

- [ ] **Step 2: Write a test for the fallback logic**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_metadata.py`:

```python
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcription_processor import extract_metadata


def test_metadata_fallback_uses_filename_and_ctime():
    """When Claude returns an empty dict, fallbacks kick in."""
    fake_path = Path("My_Important_Meeting_2026_05_18.mp3")

    with patch("transcription_processor.call_claude_cli", side_effect=Exception("no claude")):
        # patch stat().st_ctime to a known value
        mock_stat = MagicMock()
        mock_stat.st_ctime = 1747526400.0  # 2026-05-18 00:00:00 UTC
        with patch.object(Path, "stat", return_value=mock_stat):
            result = extract_metadata("some short text here", fake_path)

    assert result["title"] == "My Important Meeting 2026 05 18"
    assert result["date"] == "2026-05-18"
    assert result["attendees"] == []


def test_metadata_claude_result_used_when_present():
    """When Claude returns valid metadata it is used as-is."""
    fake_path = Path("untitled.txt")
    claude_response = {
        "title": "Sales Strategy Q2",
        "date": "2026-05-15",
        "attendees": ["Quintus", "Aboo"],
        "location": "Boardroom",
    }
    with patch("transcription_processor.call_claude_cli", return_value=claude_response):
        mock_stat = MagicMock()
        mock_stat.st_ctime = 1747526400.0
        with patch.object(Path, "stat", return_value=mock_stat):
            result = extract_metadata("some transcript text", fake_path)

    assert result["title"] == "Sales Strategy Q2"
    assert result["date"] == "2026-05-15"
    assert result["attendees"] == ["Quintus", "Aboo"]


if __name__ == "__main__":
    test_metadata_fallback_uses_filename_and_ctime()
    test_metadata_claude_result_used_when_present()
    print("All metadata tests passed.")
```

- [ ] **Step 3: Run the tests**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_metadata.py"
```

Expected: `All metadata tests passed.`

- [ ] **Step 4: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py tests/test_metadata.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add metadata extraction with Claude Haiku + fallbacks"
```

---

## Task 5: Transcript chunking + Claude Sonnet structuring + Haiku merge

**Files:**
- Modify: `transcription_processor.py` — add `chunk_transcript()`, `structure_chunk()`, `merge_partial_minutes()`

- [ ] **Step 1: Add chunking helper**

Append to `transcription_processor.py`:

```python
# ─── Chunking ─────────────────────────────────────────────────────────────────

def chunk_transcript(text: str, chunk_words: int = CHUNK_WORDS, overlap_words: int = CHUNK_OVERLAP_WORDS) -> List[str]:
    """
    Split transcript into overlapping word-based chunks.
    Returns list of chunk strings. Single chunk if text is short enough.
    """
    words = text.split()
    if len(words) <= chunk_words:
        return [text]

    chunks, start = [], 0
    while start < len(words):
        end = min(start + chunk_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_words
    return chunks
```

- [ ] **Step 2: Add chunk structuring and merge functions**

Append to `transcription_processor.py`:

```python
# ─── Minutes Structuring ──────────────────────────────────────────────────────

_STRUCTURE_SYSTEM = (
    "You are a professional meeting minutes writer for Olympic Paints (Limpopo, SA). "
    "Return ONLY a valid JSON object — no prose, no markdown fences. "
    "Keys: summary (str), topics (list of {heading: str, points: list of str}), "
    "decisions (list of str), action_items (list of {owner: str, action: str, due_date: str|null}), "
    "next_steps (list of str). "
    "Preserve speaker attribution (e.g. 'Quintus: ...') where present in the transcript."
)

_STRUCTURE_PROMPT = """\
Structure the following meeting transcript excerpt into meeting minutes.

Meeting title: {title}
Date: {date}
Attendees: {attendees}
Chunk {chunk_num} of {total_chunks}:

--- TRANSCRIPT EXCERPT ---
{chunk_text}
--- END EXCERPT ---

Return a JSON object with keys:
  summary      — 2-3 sentence summary of THIS excerpt
  topics       — list of {{heading, points[]}} (preserve speaker labels where present)
  decisions    — list of decisions made in this excerpt
  action_items — list of {{owner, action, due_date}} (due_date: ISO date or null)
  next_steps   — list of next steps mentioned

Return ONLY the raw JSON object."""

_MERGE_SYSTEM = (
    "You are a meeting minutes editor. "
    "You receive partial minutes from consecutive transcript chunks. "
    "Return ONLY a valid JSON object — no prose, no markdown fences. "
    "Merge them into one coherent, deduplicated document. "
    "Keys: executive_summary (str, 3-5 sentences), "
    "topics (list of {heading: str, points: list of str}), "
    "decisions (list of str), "
    "action_items (list of {owner: str, action: str, due_date: str|null}), "
    "next_steps (list of str)."
)

_MERGE_PROMPT = """\
Merge these partial meeting minutes into one coherent document.
Deduplicate repeated points. Preserve all unique content. Combine the summaries
into a 3-5 sentence executive summary.

Partial minutes (JSON array):
{partials_json}

Return a single merged JSON object with keys:
  executive_summary, topics, decisions, action_items, next_steps"""


def structure_chunk(
    chunk_text: str,
    title: str,
    date: str,
    attendees: List[str],
    chunk_num: int,
    total_chunks: int,
) -> Dict:
    """Structure one transcript chunk into partial minutes via Claude Sonnet."""
    prompt = _STRUCTURE_PROMPT.format(
        title=title,
        date=date,
        attendees=", ".join(attendees) if attendees else "Unknown",
        chunk_num=chunk_num,
        total_chunks=total_chunks,
        chunk_text=chunk_text,
    )
    result = call_claude_cli(
        system_prompt=_STRUCTURE_SYSTEM,
        user_prompt=prompt,
        model=STRUCTURING_MODEL,
        max_seconds=300,
    )
    if not isinstance(result, dict):
        raise ClaudeCliError(f"structure_chunk: expected dict, got {type(result).__name__}")
    return result


def merge_partial_minutes(partials: List[Dict]) -> Dict:
    """Merge all partial minutes dicts into one coherent document via Claude Haiku."""
    if len(partials) == 1:
        # Single chunk — promote summary to executive_summary and return
        p = partials[0]
        return {
            "executive_summary": p.get("summary", ""),
            "topics": p.get("topics", []),
            "decisions": p.get("decisions", []),
            "action_items": p.get("action_items", []),
            "next_steps": p.get("next_steps", []),
        }

    result = call_claude_cli(
        system_prompt=_MERGE_SYSTEM,
        user_prompt=_MERGE_PROMPT.format(partials_json=json.dumps(partials, indent=2)),
        model=MERGE_MODEL,
        max_seconds=180,
    )
    if not isinstance(result, dict):
        raise ClaudeCliError(f"merge_partial_minutes: expected dict, got {type(result).__name__}")
    return result


def build_structured_minutes(
    transcript: str,
    title: str,
    date: str,
    attendees: List[str],
) -> Dict:
    """
    Full structuring pipeline: chunk → structure each chunk → merge.
    Returns final minutes dict with keys:
      executive_summary, topics, decisions, action_items, next_steps
    """
    chunks = chunk_transcript(transcript)
    logger.info(f"  Transcript split into {len(chunks)} chunk(s)")

    partials = []
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"  Structuring chunk {i}/{len(chunks)}...")
        partial = structure_chunk(chunk, title, date, attendees, i, len(chunks))
        partials.append(partial)

    logger.info("  Merging partial minutes...")
    return merge_partial_minutes(partials)
```

- [ ] **Step 2: Write tests for chunking logic**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_chunking.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcription_processor import chunk_transcript


def test_short_transcript_returns_single_chunk():
    text = " ".join(["word"] * 100)
    chunks = chunk_transcript(text, chunk_words=3000, overlap_words=200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_long_transcript_splits_correctly():
    # 7000 words, chunk=3000, overlap=200 → chunks at 0-3000, 2800-5800, 5600-7000
    text = " ".join([f"w{i}" for i in range(7000)])
    chunks = chunk_transcript(text, chunk_words=3000, overlap_words=200)
    assert len(chunks) == 3
    # Verify overlap: last 200 words of chunk 1 should appear at start of chunk 2
    chunk1_words = chunks[0].split()
    chunk2_words = chunks[1].split()
    assert chunk1_words[-200:] == chunk2_words[:200]


def test_exact_chunk_boundary_no_infinite_loop():
    text = " ".join(["word"] * 3000)
    chunks = chunk_transcript(text, chunk_words=3000, overlap_words=200)
    assert len(chunks) == 1


if __name__ == "__main__":
    test_short_transcript_returns_single_chunk()
    test_long_transcript_splits_correctly()
    test_exact_chunk_boundary_no_infinite_loop()
    print("All chunking tests passed.")
```

- [ ] **Step 3: Run the tests**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_chunking.py"
```

Expected: `All chunking tests passed.`

- [ ] **Step 4: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py tests/test_chunking.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add chunked Claude Sonnet structuring and Haiku merge"
```

---

## Task 6: Write structured minutes to .docx

**Files:**
- Modify: `transcription_processor.py` — add `write_docx()` function

- [ ] **Step 1: Add the .docx writer**

Append to `transcription_processor.py`:

```python
# ─── .docx Writer ─────────────────────────────────────────────────────────────

def _sanitise_filename(s: str) -> str:
    """Replace characters illegal in Windows filenames."""
    return re.sub(r'[\\/:*?"<>|]', "_", s).strip()


def write_docx(minutes: Dict, meta: Dict) -> Path:
    """
    Write structured minutes dict to a .docx file.
    Returns the Path of the written file.
    """
    title    = meta.get("title", "Untitled Meeting")
    date_str = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    attendees = meta.get("attendees", [])
    location  = meta.get("location") or "—"

    safe_title = _sanitise_filename(title)
    safe_date  = date_str.replace("-", "_")
    filename   = f"MM_{safe_title}_{safe_date}.docx"
    out_path   = MINUTES_OUTPUT_DIR / filename

    doc = Document()

    # Title
    h = doc.add_heading(title, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Meeting details
    doc.add_paragraph(f"Date: {date_str}")
    doc.add_paragraph(f"Location: {location}")
    doc.add_paragraph(f"Attendees: {', '.join(attendees) if attendees else '—'}")

    # Executive Summary
    doc.add_heading("Executive Summary", level=2)
    doc.add_paragraph(minutes.get("executive_summary", ""))

    # Topics Discussed
    topics = minutes.get("topics", [])
    if topics:
        doc.add_heading("Topics Discussed", level=2)
        for i, topic in enumerate(topics, 1):
            doc.add_heading(f"{i}. {topic.get('heading', '')}", level=3)
            for point in topic.get("points", []):
                doc.add_paragraph(point, style="List Bullet")

    # Key Decisions
    decisions = minutes.get("decisions", [])
    if decisions:
        doc.add_heading("Key Decisions", level=2)
        for d in decisions:
            doc.add_paragraph(d, style="List Bullet")

    # Action Items (table)
    action_items = minutes.get("action_items", [])
    if action_items:
        doc.add_heading("Action Items", level=2)
        tbl = doc.add_table(rows=1, cols=3)
        tbl.style = "Table Grid"
        hdr = tbl.rows[0].cells
        hdr[0].text, hdr[1].text, hdr[2].text = "Owner", "Action", "Due Date"
        for item in action_items:
            row = tbl.add_row().cells
            row[0].text = item.get("owner", "—")
            row[1].text = item.get("action", "")
            row[2].text = item.get("due_date") or "—"

    # Next Steps
    next_steps = minutes.get("next_steps", [])
    if next_steps:
        doc.add_heading("Next Steps", level=2)
        for s in next_steps:
            doc.add_paragraph(s, style="List Bullet")

    doc.save(str(out_path))
    logger.info(f"  .docx written: {out_path.name}")
    return out_path
```

- [ ] **Step 2: Write a test for the .docx writer**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_docx_writer.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcription_processor import write_docx, MINUTES_OUTPUT_DIR
from docx import Document


SAMPLE_MINUTES = {
    "executive_summary": "The team reviewed Q2 pricing strategy and agreed on a 5% list-price increase.",
    "topics": [
        {"heading": "Pricing Review", "points": ["Quintus: proposed 5% increase", "Aboo: agreed"]},
    ],
    "decisions": ["5% list-price increase approved for Q2."],
    "action_items": [
        {"owner": "Quintus", "action": "Update price list", "due_date": "2026-05-30"},
    ],
    "next_steps": ["Quintus to circulate updated price list by 30 May."],
}

SAMPLE_META = {
    "title": "Q2 Pricing Strategy",
    "date": "2026-05-18",
    "attendees": ["Quintus Lategan", "Aboo Cassim"],
    "location": "Boardroom",
}


def test_docx_is_written_and_readable():
    path = write_docx(SAMPLE_MINUTES, SAMPLE_META)
    assert path.exists(), f"Expected {path} to exist"
    doc = Document(str(path))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Q2 Pricing Strategy" in full_text
    assert "Quintus Lategan" in full_text
    assert "5% list-price increase approved" in full_text
    # Cleanup
    path.unlink()
    print(f"  Written and verified: {path.name}")


if __name__ == "__main__":
    test_docx_is_written_and_readable()
    print("All docx writer tests passed.")
```

- [ ] **Step 3: Run the test**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\tests\test_docx_writer.py"
```

Expected: `All docx writer tests passed.`

- [ ] **Step 4: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py tests/test_docx_writer.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add .docx writer for structured meeting minutes"
```

---

## Task 7: Notion client + meeting page creation + duplicate check

**Files:**
- Modify: `transcription_processor.py` — add `NotionClient` class and `create_notion_meeting_page()`

- [ ] **Step 1: Add the NotionClient (copied verbatim from meeting_minutes_extractor.py)**

Append to `transcription_processor.py`:

```python
# ─── Notion Client ────────────────────────────────────────────────────────────

class NotionClient:
    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json",
        }

    def _get(self, endpoint: str) -> Dict:
        r = requests.get(f"{NOTION_API_URL}{endpoint}", headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, body: Dict) -> Dict:
        r = requests.post(f"{NOTION_API_URL}{endpoint}", headers=self.headers, json=body)
        r.raise_for_status()
        return r.json()

    def _patch(self, endpoint: str, body: Dict) -> Dict:
        r = requests.patch(f"{NOTION_API_URL}{endpoint}", headers=self.headers, json=body)
        r.raise_for_status()
        return r.json()

    def query_database(self, db_id: str, filter_dict: Optional[Dict] = None) -> List[Dict]:
        results, cursor = [], None
        while True:
            body: Dict[str, Any] = {"page_size": 100}
            if filter_dict:
                body["filter"] = filter_dict
            if cursor:
                body["start_cursor"] = cursor
            data = self._post(f"/databases/{db_id}/query", body)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return results

    def meeting_exists(self, title: str, date: str) -> bool:
        """Return True if a meeting page with the same title and date already exists."""
        try:
            pages = self.query_database(MEETING_DATABASE_ID, filter_dict={
                "and": [
                    {"property": "Document Name", "title": {"equals": title}},
                    {"property": "Date", "date": {"equals": date}},
                ]
            })
            return len(pages) > 0
        except Exception:
            # If the filter fails (e.g. property name mismatch), don't block creation
            return False

    def create_meeting_page(self, title: str, date: str, attendees: List[str], minutes: Dict) -> str:
        """
        Create a meeting page in MEETING_DATABASE_ID.
        Writes the structured minutes as Notion blocks in the page body.
        Returns the new page ID.
        """
        properties: Dict[str, Any] = {
            "Document Name": {
                "title": [{"text": {"content": title[:200]}}]
            },
        }
        if date:
            properties["Date"] = {"date": {"start": date}}
        if attendees:
            properties["Attendees"] = {
                "rich_text": [{"text": {"content": ", ".join(attendees)[:2000]}}]
            }

        children = _minutes_to_notion_blocks(minutes)
        payload = {
            "parent": {"database_id": MEETING_DATABASE_ID},
            "properties": properties,
            "children": children[:100],  # Notion max 100 blocks per create call
        }
        result = self._post("/pages", payload)
        page_id = result["id"]

        # Append remaining blocks if minutes produced > 100 blocks
        if len(children) > 100:
            for i in range(100, len(children), 100):
                time.sleep(0.5)
                self._patch(f"/blocks/{page_id}/children", {"children": children[i:i+100]})

        return page_id

    def get_page_content(self, page_id: str) -> str:
        """Read ALL blocks from a Notion page and return as plain text."""
        return self._read_blocks(page_id, depth=0)

    def _read_blocks(self, block_id: str, depth: int) -> str:
        parts, cursor = [], None
        while True:
            endpoint = f"/blocks/{block_id}/children"
            if cursor:
                endpoint += f"?start_cursor={cursor}"
            try:
                data = self._get(endpoint)
            except Exception as e:
                logger.warning(f"Could not fetch blocks for {block_id}: {e}")
                break
            for block in data.get("results", []):
                line = self._block_to_text(block, depth)
                if line:
                    parts.append(line)
                if block.get("has_children"):
                    child_text = self._read_blocks(block["id"], depth + 1)
                    if child_text:
                        parts.append(child_text)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return "\n".join(parts)

    @staticmethod
    def _block_to_text(block: Dict, depth: int) -> str:
        btype = block.get("type", "")
        pad   = "  " * depth

        def rich(key: str) -> str:
            return "".join(
                t.get("text", {}).get("content", "")
                for t in block.get(key, {}).get("rich_text", [])
            )

        if btype == "heading_1":   return f"{pad}# {rich('heading_1')}"
        if btype == "heading_2":   return f"{pad}## {rich('heading_2')}"
        if btype == "heading_3":   return f"{pad}### {rich('heading_3')}"
        if btype == "paragraph":
            t = rich("paragraph")
            return f"{pad}{t}" if t else ""
        if btype == "bulleted_list_item": return f"{pad}• {rich('bulleted_list_item')}"
        if btype == "numbered_list_item": return f"{pad}- {rich('numbered_list_item')}"
        if btype == "to_do":
            checked = block.get("to_do", {}).get("checked", False)
            return f"{pad}[{'x' if checked else ' '}] {rich('to_do')}"
        if btype == "quote":    return f"{pad}> {rich('quote')}"
        if btype == "callout":  return f"{pad}>> {rich('callout')}"
        if btype == "divider":  return f"{pad}---"
        return ""

    def create_meeting_task(self, meeting_title: str, meeting_id: str, area: str) -> Optional[str]:
        if area not in VALID_AREAS:
            area = "Olympic"
        task_title = f"{meeting_title} — Action Items"
        properties: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": task_title[:200]}}]},
            "Area": {"select": {"name": area}},
            "MM": {"relation": [{"id": meeting_id}]},
            "Action State": {"relation": [{"id": ACTION_STATE_COMMITTED}]},
        }
        try:
            result = self._post("/pages", {
                "parent": {"database_id": TASK_DATABASE_ID},
                "properties": properties,
            })
            return result.get("id")
        except Exception as e:
            logger.error(f"Failed to create task for meeting '{meeting_title}': {e}")
            return None

    def append_action_blocks(self, task_page_id: str, meeting_title: str, action_items: List[Dict]) -> None:
        blocks: List[Dict[str, Any]] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": f"Actions — {meeting_title}"}}]
                },
            }
        ]
        for item in action_items:
            label  = item.get("action", item.get("title", "")).strip()
            owner  = item.get("owner", "").strip()
            due    = item.get("due_date") or ""
            text   = f"[{owner}] {label}" if owner else label
            if due:
                text += f" (by {due})"
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                    "checked": False,
                },
            })
        time.sleep(1)
        for i in range(0, len(blocks), 100):
            try:
                self._patch(f"/blocks/{task_page_id}/children", {"children": blocks[i:i+100]})
            except Exception as e:
                logger.error(f"Failed to append blocks to task {task_page_id}: {e}")


def _minutes_to_notion_blocks(minutes: Dict) -> List[Dict[str, Any]]:
    """Convert structured minutes dict to Notion block objects."""
    blocks: List[Dict[str, Any]] = []

    def para(text: str) -> Dict:
        return {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def h2(text: str) -> Dict:
        return {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def h3(text: str) -> Dict:
        return {
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def bullet(text: str) -> Dict:
        return {
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    summary = minutes.get("executive_summary", "")
    if summary:
        blocks.append(h2("Executive Summary"))
        blocks.append(para(summary))

    topics = minutes.get("topics", [])
    if topics:
        blocks.append(h2("Topics Discussed"))
        for topic in topics:
            blocks.append(h3(topic.get("heading", "")))
            for point in topic.get("points", []):
                blocks.append(bullet(point))

    decisions = minutes.get("decisions", [])
    if decisions:
        blocks.append(h2("Key Decisions"))
        for d in decisions:
            blocks.append(bullet(d))

    action_items = minutes.get("action_items", [])
    if action_items:
        blocks.append(h2("Action Items"))
        for item in action_items:
            owner = item.get("owner", "—")
            action = item.get("action", "")
            due = item.get("due_date") or "—"
            blocks.append(bullet(f"[{owner}] {action} — due {due}"))

    next_steps = minutes.get("next_steps", [])
    if next_steps:
        blocks.append(h2("Next Steps"))
        for s in next_steps:
            blocks.append(bullet(s))

    return blocks
```

- [ ] **Step 2: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add NotionClient with meeting page creation, duplicate check, task creation"
```

---

## Task 8: Action item extraction (reusing existing Claude prompt)

**Files:**
- Modify: `transcription_processor.py` — add `extract_action_items()` and Telegram helper

- [ ] **Step 1: Add action item extraction and Telegram notify**

Append to `transcription_processor.py`:

```python
# ─── Action Item Extraction ───────────────────────────────────────────────────

_EXTRACTION_SYSTEM_PROMPT = (
    "You are a meeting-minutes action-item extractor. "
    "Return ONLY a valid JSON array of action items — no prose, no markdown fences. "
    "Each item must have keys: title, description, owner, due_date (ISO date or null), area. "
    "Area must be one of: Olympic, Timion, Quintus, Flomatic, GOD."
)

_EXTRACTION_PROMPT = """\
You are extracting action items from Olympic Paints meeting minutes.

Meeting: {title}
Date: {date}
Attendees: {attendees}

--- MEETING CONTENT START ---
{content}
--- MEETING CONTENT END ---

Extract every action item, follow-up, decision requiring action, or task mentioned.
Read them as a person would — do not require special formatting or labels.

Return a JSON array. Each element must have:
  "title"       — short, actionable task name (max 100 chars)
  "description" — context: who, what, why (from the minutes)
  "owner"       — first name of responsible person, or "Unassigned"
  "due_date"    — ISO date YYYY-MM-DD if mentioned, otherwise null
  "area"        — one of: Olympic, Timion, Quintus, Flomatic, GOD

Rules:
• Capture implicit tasks, not only lines labelled "Action:"
• If there are genuinely no action items, return []
• Return ONLY the raw JSON array — no markdown, no explanation"""


def extract_action_items(page_content: str, title: str, date: str, attendees: List[str]) -> List[Dict]:
    """Extract action items from structured minutes text via Claude Haiku."""
    if not page_content.strip():
        return []

    prompt = _EXTRACTION_PROMPT.format(
        title=title or "Untitled",
        date=date or "Unknown",
        attendees=", ".join(attendees) if attendees else "Unknown",
        content=page_content[:8000],
    )

    try:
        items = call_claude_cli(
            system_prompt=_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=prompt,
            model=METADATA_MODEL,
            max_seconds=180,
        )
        if not isinstance(items, list):
            logger.error(f"Action item extraction: expected list, got {type(items).__name__}")
            return []
        logger.info(f"  Action items extracted: {len(items)}")
        return items
    except ClaudeCliError as e:
        logger.error(f"Action item extraction failed: {e}")
        return []


# ─── Telegram ─────────────────────────────────────────────────────────────────

def _telegram_notify(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
    except Exception:
        pass
```

- [ ] **Step 2: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add action item extraction and Telegram notification"
```

---

## Task 9: Main pipeline orchestrator + error handling + archive logic

**Files:**
- Modify: `transcription_processor.py` — add `process_file()`, `_fail_file()`, `_archive_file()`, `run_inbox()`, `__main__` block

- [ ] **Step 1: Add the orchestrator**

Append to `transcription_processor.py`:

```python
# ─── File Helpers ─────────────────────────────────────────────────────────────

def _fail_file(file_path: Path, reason: str) -> None:
    """Move file to Failed/ and write a .error.txt sidecar."""
    failed_dir = TRANSCRIPTION_INBOX / "Failed"
    failed_dir.mkdir(exist_ok=True)
    dest = failed_dir / file_path.name
    try:
        shutil.move(str(file_path), str(dest))
    except Exception:
        dest = file_path  # leave in place if move fails
    error_file = failed_dir / f"{file_path.stem}.error.txt"
    error_file.write_text(f"{datetime.now().isoformat()}\n{reason}\n", encoding="utf-8")
    logger.error(f"  FAILED: {file_path.name} → Failed/ ({reason})")
    _telegram_notify(f"❌ Transcription Processor — failed: {file_path.name}\n{reason}")


def _archive_file(file_path: Path) -> None:
    """Move file to Archived/ after successful processing."""
    archived_dir = TRANSCRIPTION_INBOX / "Archived"
    archived_dir.mkdir(exist_ok=True)
    dest = archived_dir / file_path.name
    shutil.move(str(file_path), str(dest))
    logger.info(f"  Archived: {file_path.name} → Archived/")


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def process_file(file_path: Path, interactive: bool = False) -> bool:
    """
    Full pipeline for a single transcription/audio file.
    Returns True on success, False on failure.
    interactive=True prompts for missing metadata (--file CLI mode).
    """
    logger.info("=" * 60)
    logger.info(f"Processing: {file_path.name}")

    suffix = file_path.suffix.lower()

    # ── Step 1: Extract raw text ──────────────────────────────────────────────
    if suffix in AUDIO_EXTENSIONS:
        try:
            transcript = transcribe_audio(file_path)
        except Exception as e:
            _fail_file(file_path, f"Whisper transcription error: {e}")
            return False
    elif suffix in TEXT_EXTENSIONS:
        try:
            transcript = extract_text_from_file(file_path)
        except Exception as e:
            _fail_file(file_path, f"Text extraction error: {e}")
            return False
    else:
        _fail_file(file_path, f"Unsupported file type: {suffix}")
        return False

    word_count = len(transcript.split())
    logger.info(f"  Transcript: {word_count} words")

    if word_count < MIN_TRANSCRIPT_WORDS:
        _fail_file(file_path, f"Transcript too short ({word_count} words, minimum {MIN_TRANSCRIPT_WORDS})")
        return False

    # ── Step 2: Extract metadata ──────────────────────────────────────────────
    meta = extract_metadata(transcript, file_path)
    if interactive:
        meta = prompt_missing_metadata(meta)

    # ── Step 3: Structure minutes ─────────────────────────────────────────────
    try:
        minutes = build_structured_minutes(
            transcript,
            title=meta["title"],
            date=meta["date"],
            attendees=meta["attendees"],
        )
    except Exception as e:
        _fail_file(file_path, f"Claude structuring error: {e}")
        return False

    # ── Step 4: Write .docx ───────────────────────────────────────────────────
    try:
        docx_path = write_docx(minutes, meta)
    except Exception as e:
        logger.error(f"  .docx write failed: {e}")
        # Non-fatal — continue to Notion
        docx_path = None

    # ── Step 5 & 6: Notion meeting page + action items ────────────────────────
    notion = NotionClient(os.environ["NOTION_API_TOKEN"])

    if notion.meeting_exists(meta["title"], meta["date"]):
        logger.info(f"  Duplicate detected — meeting '{meta['title']}' on {meta['date']} already in Notion. Skipping Notion creation.")
        _telegram_notify(f"⚠️ Transcription Processor — duplicate skipped: {meta['title']} ({meta['date']})")
        _archive_file(file_path)
        return True

    try:
        page_id = notion.create_meeting_page(
            title=meta["title"],
            date=meta["date"],
            attendees=meta["attendees"],
            minutes=minutes,
        )
        logger.info(f"  Notion meeting page created: {page_id}")
    except Exception as e:
        logger.error(f"  Notion page creation failed: {e}")
        _telegram_notify(f"❌ Transcription Processor — Notion page creation failed for '{meta['title']}': {e}")
        # Do NOT archive — leave file for retry
        return False

    # Extract action items from the Notion page body (round-trip for accuracy)
    time.sleep(2)  # Let Notion settle
    try:
        page_content = notion.get_page_content(page_id)
        action_items = extract_action_items(
            page_content,
            title=meta["title"],
            date=meta["date"],
            attendees=meta["attendees"],
        )
    except Exception as e:
        logger.error(f"  Action item extraction failed: {e}")
        action_items = []

    if action_items:
        # Determine area from action items (most common, default Olympic)
        area_counts: Dict[str, int] = {}
        for item in action_items:
            a = item.get("area", "Olympic")
            area_counts[a] = area_counts.get(a, 0) + 1
        area = max(area_counts, key=area_counts.get) if area_counts else "Olympic"
        if area not in VALID_AREAS:
            area = "Olympic"

        task_id = notion.create_meeting_task(meta["title"], page_id, area)
        if task_id:
            notion.append_action_blocks(task_id, meta["title"], action_items)
            logger.info(f"  Task page created [{area}] with {len(action_items)} action item(s)")

    # ── Step 7: Archive ───────────────────────────────────────────────────────
    _archive_file(file_path)

    # ── Step 8: Telegram summary ──────────────────────────────────────────────
    _telegram_notify(
        f"✅ Transcription Processor\n"
        f"📄 {meta['title']} ({meta['date']})\n"
        f"👥 {', '.join(meta['attendees']) if meta['attendees'] else 'attendees unknown'}\n"
        f"📝 {len(action_items)} action item(s) extracted\n"
        f"📁 .docx: {docx_path.name if docx_path else 'write failed'}"
    )

    logger.info(f"Done: {file_path.name}")
    return True


def run_inbox() -> None:
    """Process all eligible files currently in TRANSCRIPTION_INBOX."""
    files = [
        f for f in TRANSCRIPTION_INBOX.iterdir()
        if f.is_file()
        and f.suffix.lower() in ALL_EXTENSIONS
        and not f.name.startswith("~$")
        and not f.name.endswith(".tmp")
        and f.stat().st_size >= 1024
    ]

    if not files:
        logger.info("No eligible files in inbox.")
        return

    logger.info(f"Found {len(files)} file(s) in inbox.")
    for f in files:
        process_file(f, interactive=False)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    _check_prerequisites()

    parser = argparse.ArgumentParser(description="Olympic Paints Transcription Processor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", metavar="PATH", help="Process a single file (interactive metadata prompts)")
    group.add_argument("--inbox", action="store_true", help="Process all files in the Transcriptions inbox")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"ERROR: File not found: {path}")
            sys.exit(1)
        success = process_file(path, interactive=True)
        sys.exit(0 if success else 1)
    else:
        run_inbox()
```

- [ ] **Step 2: Smoke-test the CLI with --help**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\transcription_processor.py" --help
```

Expected output:
```
usage: transcription_processor.py [-h] (--file PATH | --inbox)
...
```

- [ ] **Step 3: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_processor.py
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add main pipeline orchestrator, error handling, archive logic, CLI entry point"
```

---

## Task 10: Folder watcher

**Files:**
- Create: `transcription_watcher.py`

- [ ] **Step 1: Create the watcher script**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\transcription_watcher.py`:

```python
#!/usr/bin/env python3
"""
Transcription Watcher — Olympic Paints
Monitors 0.Inbox/Transcriptions/ for new files and triggers transcription_processor.py.
Run continuously via Task Scheduler or manually.
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR            = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
TRANSCRIPTION_INBOX = BASE_DIR / "0.Inbox" / "Transcriptions"
PROCESSOR_SCRIPT    = BASE_DIR / "transcription_processor.py"
LOG_DIR             = Path(r"C:\Users\quint\.claude\logs\transcription")

AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".aac", ".wma", ".ogg"}
TEXT_EXTENSIONS  = {".txt", ".docx", ".doc", ".vtt", ".srt", ".pdf"}
ALL_EXTENSIONS   = AUDIO_EXTENSIONS | TEXT_EXTENSIONS

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"transcription_watcher_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class TranscriptionHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in ALL_EXTENSIONS:
            return
        if path.name.startswith("~$") or path.name.endswith(".tmp"):
            return

        # Wait for write to complete
        time.sleep(2)

        if not path.exists():
            return
        if path.stat().st_size < 1024:
            logger.info(f"Ignoring small file (<1KB): {path.name}")
            return

        logger.info(f"New file detected: {path.name}")
        self._process(path)

    def _process(self, path: Path) -> None:
        try:
            result = subprocess.run(
                [sys.executable, str(PROCESSOR_SCRIPT), "--file", str(path)],
                timeout=1800,  # 30 min for large audio files
            )
            if result.returncode == 0:
                logger.info(f"Processed successfully: {path.name}")
            else:
                logger.error(f"Processor exited with code {result.returncode}: {path.name}")
        except subprocess.TimeoutExpired:
            logger.error(f"Processor timed out for: {path.name}")
        except Exception as e:
            logger.error(f"Unexpected error processing {path.name}: {e}")


def start_watcher():
    if not TRANSCRIPTION_INBOX.exists():
        logger.error(f"Inbox not found: {TRANSCRIPTION_INBOX}")
        sys.exit(1)
    if not PROCESSOR_SCRIPT.exists():
        logger.error(f"Processor script not found: {PROCESSOR_SCRIPT}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Transcription Watcher Starting")
    logger.info(f"Monitoring: {TRANSCRIPTION_INBOX}")
    logger.info("=" * 60)

    handler  = TranscriptionHandler()
    observer = Observer()
    observer.schedule(handler, str(TRANSCRIPTION_INBOX), recursive=False)

    try:
        observer.start()
        logger.info("Watcher active. Waiting for files...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        observer.stop()
    finally:
        observer.join()
        logger.info("Watcher stopped.")


if __name__ == "__main__":
    start_watcher()
```

- [ ] **Step 2: Write the .bat launcher**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\run_transcription_watcher.bat`:

```bat
@echo off
cd /d "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints"
C:\Python313\python.exe transcription_watcher.py
```

- [ ] **Step 3: Smoke-test the watcher starts cleanly**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\transcription_watcher.py"
```

Expected: `Watcher active. Waiting for files...` — then Ctrl+C to stop.

- [ ] **Step 4: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add transcription_watcher.py run_transcription_watcher.bat
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add folder watcher and bat launcher"
```

---

## Task 11: Register watcher in Windows Task Scheduler

**Files:**
- No code changes — Task Scheduler setup only

- [ ] **Step 1: Register the Task Scheduler job**

Run in PowerShell (as administrator or current user):

```powershell
$action  = New-ScheduledTaskAction -Execute "C:\Python313\python.exe" `
             -Argument "transcription_watcher.py" `
             -WorkingDirectory "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
              -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Olympic — Transcription Watcher" `
  -Action $action -Trigger $trigger -Settings $settings `
  -Description "Watches 0.Inbox/Transcriptions/ and processes new audio/transcript files" `
  -RunLevel Highest -Force
```

- [ ] **Step 2: Verify the task appears in Task Scheduler**

```powershell
Get-ScheduledTask -TaskName "Olympic — Transcription Watcher" | Select-Object TaskName, State
```

Expected: `State: Ready`

- [ ] **Step 3: Commit task registration notes**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit --allow-empty -m "chore: register Transcription Watcher in Task Scheduler (AtLogOn trigger)"
```

---

## Task 12: End-to-end integration test with a real .txt file

**Files:**
- No code changes — manual integration verification

- [ ] **Step 1: Create a sample transcript file**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\Transcriptions\test_meeting_2026_05_18.txt` with content:

```
Quintus Lategan: Good morning everyone, let's get started. Today is May 18th 2026.

Quintus Lategan: First item on the agenda is Q2 pricing. Aboo, can you take us through the proposed increase?

Aboo Cassim: Sure. We're proposing a 5% list price increase effective June 1st across all enamel ranges.

Quintus Lategan: Any concerns from the team?

Nikhil Panchal: We need to notify stockists at least two weeks in advance.

Quintus Lategan: Agreed. Aboo, can you send the updated price list to all stockists by May 25th?

Aboo Cassim: I'll handle that.

Quintus Lategan: Second item — the new bucket packaging rollout. Sigma, what's the status?

Aboo Cassim: The artwork is approved, we're waiting on the supplier. Byron to follow up with Plastop by end of this week.

Quintus Lategan: Perfect. Byron, please confirm the delivery date once you have it.

Quintus Lategan: That covers today's agenda. Next meeting same time next Monday.
```

- [ ] **Step 2: Run the processor manually**

```
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\transcription_processor.py" --file "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\Transcriptions\test_meeting_2026_05_18.txt"
```

- [ ] **Step 3: Verify all outputs**

Check each of these:

1. **Log output** — should show metadata extracted, chunks processed, Notion page created, action items found
2. **.docx file** — open `3.Resources/3. Meeting Minutes/MM_*.docx` and verify all sections present
3. **Notion** — open the Meeting Database and confirm new page exists with correct title, date, attendees
4. **Notion Task DB** — confirm a task page was created linked to the meeting with to-do checkboxes
5. **Archived** — confirm `test_meeting_2026_05_18.txt` moved to `0.Inbox/Transcriptions/Archived/`
6. **Telegram** — confirm notification received

- [ ] **Step 4: Commit**

```
git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit --allow-empty -m "test: end-to-end integration verified — .docx, Notion page, action items, archive, Telegram"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Audio formats → Whisper (Task 3)
- ✅ Text/doc formats → extract_text_from_file (Task 2)
- ✅ Metadata extraction with fallbacks (Task 4)
- ✅ Interactive prompts for manual CLI mode (Task 4 — `prompt_missing_metadata`)
- ✅ Chunked Sonnet structuring + Haiku merge (Task 5)
- ✅ .docx output with all required sections (Task 6)
- ✅ Notion meeting page creation (Task 7)
- ✅ Duplicate check before Notion creation (Task 7)
- ✅ Action items extracted and written as Notion to-do blocks (Task 8 + 9)
- ✅ Archive on success / Failed/ with .error.txt on failure (Task 9)
- ✅ Telegram notifications — success, failure, duplicate (Task 8 + 9)
- ✅ Folder watcher with 2-second delay, ignores .tmp/~$* (Task 10)
- ✅ Task Scheduler registration (Task 11)
- ✅ End-to-end integration test (Task 12)

**Type consistency:** All functions use `Dict`, `List`, `Optional`, `Any` from typing. `minutes` dict keys (`executive_summary`, `topics`, `decisions`, `action_items`, `next_steps`) are consistent across `merge_partial_minutes`, `write_docx`, `_minutes_to_notion_blocks`. `action_items` list items use `{owner, action, due_date}` throughout.

**No placeholders:** All code blocks are complete and self-contained.
