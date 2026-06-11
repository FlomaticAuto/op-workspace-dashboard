# Transcription Processor — Design Spec
**Date:** 2026-05-18  
**Project:** Olympic Paints  
**Status:** Approved for implementation

---

## Overview

A tool that watches a drop folder for raw meeting transcription and audio files, converts them to structured meeting minutes via Claude, saves a `.docx` to the Meeting Minutes folder, creates a Notion meeting page, and immediately extracts action items into the Task Database — all in one automated run.

Mirrors the existing HAVEN pipeline pattern (`process_inbox.py` + `haven_watcher.py`).

---

## New Files

```
transcription_processor.py        ← main script (CLI + core pipeline)
transcription_watcher.py          ← folder watcher (calls processor on new files)
run_transcription_watcher.bat     ← Task Scheduler / manual launcher
```

---

## Folder Structure

```
0.Inbox/Transcriptions/           ← drop zone for input files
0.Inbox/Transcriptions/Archived/  ← successfully processed files moved here
0.Inbox/Transcriptions/Failed/    ← failed files moved here + .error.txt sidecar

3.Resources/3. Meeting Minutes/   ← structured .docx output (existing folder)
```

---

## Supported Input Formats

| Category | Extensions |
|---|---|
| Audio | `.mp3`, `.mp4`, `.m4a`, `.wav`, `.aac`, `.wma`, `.ogg` |
| Text / Transcript | `.txt`, `.docx`, `.doc`, `.vtt`, `.srt`, `.pdf` |

---

## Pipeline Flow

```
Input file dropped in 0.Inbox/Transcriptions/
        │
        ▼
1. DETECT file type
   ├── Audio → Whisper large → raw transcript text
   └── Text/Doc → extract text directly
        │
        ▼
2. EXTRACT METADATA  [Claude Haiku — full transcript]
   • Extracts: title, date, attendees[], location
   • Preserves speaker labels if present (e.g. "Quintus Lategan: ...")
   • Fallbacks: file creation date → date; filename stem → title; blank → attendees
   • CLI manual mode: prompts user for any missing fields interactively
        │
        ▼
3. STRUCTURE MINUTES  [Claude Sonnet — chunked]
   • Transcript split into ~3,000-word chunks, ~200-word overlap
   • Each chunk structured independently into partial minutes
   • Merge call (Haiku) collapses partial minutes into final document
   • Output sections:
       - Meeting Details (title, date, time, location, attendees)
       - Executive Summary (3–5 sentences)
       - Topics Discussed (numbered, speaker-attributed where available)
       - Key Decisions (bulleted)
       - Action Items (owner, description, due date)
       - Next Steps / Next Meeting
        │
        ▼
4. WRITE .docx
   • Filename: MM_<title>_<YYYY_MM_DD>.docx
   • Saved to: 3.Resources/3. Meeting Minutes/
        │
        ▼
5. CREATE Notion meeting page
   • Database: MEETING_DATABASE_ID (247ff48d2bb18009979bd25bac9fe72e)
   • Properties: title, date, attendees
   • Body: full structured minutes as Notion blocks
   • Duplicate check: skip if page with same title + date already exists
        │
        ▼
6. EXTRACT action items  [reuses meeting_minutes_extractor.py logic]
   • Reads the newly created Notion page body
   • Creates task page in TASK_DATABASE_ID linked to the meeting
   • Appends to-do checkboxes per action item
        │
        ▼
7. ARCHIVE input file → 0.Inbox/Transcriptions/Archived/
8. TELEGRAM notification with summary
```

---

## Chunking Strategy

Long transcripts degrade Claude's output quality when fed as a single block. To prevent this:

- Transcript split into chunks of **~3,000 words** with **~200-word overlap**
- Sonnet structures each chunk into partial minutes independently
- A final **Haiku merge call** collapses all partial minutes into one coherent document, deduplicating overlapping content
- Metadata extraction (Call 1) reads the full transcript — Haiku handles this as fact-finding, not synthesis

A 90-minute meeting (~9,000 words) produces 3 chunk passes + 1 merge = 4 Claude calls for the structuring phase.

---

## Claude Calls Summary

| Step | Model | Purpose |
|---|---|---|
| Metadata extraction | `claude-haiku-4-5-20251001` | Extract title, date, attendees, speakers from full transcript |
| Chunk structuring (×N) | `claude-sonnet-4-6` | Structure each transcript chunk into partial minutes |
| Merge | `claude-haiku-4-5-20251001` | Collapse partial minutes into final coherent document |
| Action item extraction | `claude-haiku-4-5-20251001` | Reuses existing EXTRACTION_PROMPT from meeting_minutes_extractor.py |

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Whisper fails (corrupt/unsupported audio) | Move to `Failed/` + `.error.txt` sidecar + Telegram notify |
| Transcript < 50 words | Move to `Failed/` + `.error.txt` — not worth processing |
| Metadata partially missing | Use fallbacks (filename stem, file creation date) — never block pipeline |
| Notion page creation fails | `.docx` still written; log + Telegram notify; **do not archive** source file (allows retry) |
| Action item extraction fails | Non-blocking — meeting page and `.docx` already exist; log + notify |
| Duplicate meeting detected | Skip Notion creation; notify; still archive file |
| Watcher sees `.tmp` / `~$*` / file < 1KB | Ignore silently |
| Watcher sees new file | Wait 2 seconds before processing (ensures write is complete) |

---

## Configuration

```python
WHISPER_MODEL        = "large"
TRANSCRIPTION_INBOX  = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\Transcriptions")
MINUTES_OUTPUT_DIR   = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\3. Meeting Minutes")
MEETING_DATABASE_ID  = "247ff48d2bb18009979bd25bac9fe72e"
TASK_DATABASE_ID     = "247ff48d2bb1800ca00aca3b59f789eb"
ACTION_STATE_COMMITTED = "301ff48d2bb180af869fdc19b6f6b062"
METADATA_MODEL       = "claude-haiku-4-5-20251001"
STRUCTURING_MODEL    = "claude-sonnet-4-6"
MERGE_MODEL          = "claude-haiku-4-5-20251001"
CHUNK_WORDS          = 3000
CHUNK_OVERLAP_WORDS  = 200
MIN_TRANSCRIPT_WORDS = 50
TELEGRAM_CHAT_ID     = "8042233389"
```

**Environment variables required:**
```
NOTION_API_TOKEN
TELEGRAM_BOT_TOKEN
```

---

## Dependencies

```
openai-whisper    ← local Whisper transcription (pip install openai-whisper)
ffmpeg            ← required by Whisper for audio decoding (winget install ffmpeg)
python-docx       ← write .docx files (pip install python-docx)
watchdog          ← folder watcher (already used by haven_watcher.py)
```

Script checks for `ffmpeg` on PATH at startup and exits with a clear install instruction if missing.

---

## CLI Usage

```bash
# Process a single file manually (prompts for missing metadata)
python transcription_processor.py --file "path/to/transcript.txt"

# Process all files currently in the inbox (batch run)
python transcription_processor.py --inbox

# Start the folder watcher (continuous)
python transcription_watcher.py
```

---

## Watcher Behaviour

- Uses `watchdog` `FileSystemEventHandler` — same pattern as `haven_watcher.py`
- Watches `0.Inbox/Transcriptions/` recursively: no (top-level files only)
- Triggers on `on_created` events for supported extensions
- Ignores: `.tmp`, `~$*` (Word lock files), files < 1KB
- Waits 2 seconds after file creation before processing
- Logs to `logs/transcription_watcher_YYYY-MM-DD.log`

---

## Output Document Format (.docx)

Filename: `MM_<SanitisedTitle>_<YYYY_MM_DD>.docx`

Sections (Word styles):
- **Heading 1:** Meeting title
- **Normal:** Date, location, attendees
- **Heading 2:** Executive Summary
- **Normal:** Summary paragraph
- **Heading 2:** Topics Discussed
- **Heading 3 + Normal:** Per-topic with speaker attribution
- **Heading 2:** Key Decisions (bulleted list)
- **Heading 2:** Action Items (table: Owner | Action | Due Date)
- **Heading 2:** Next Steps

---

## Notion Page Structure

**Properties set on creation:**
- `Document Name` / `Name` (title) — meeting title
- `Date` — extracted or file-creation date
- `Attendees` — comma-separated string

**Body blocks:** Full structured minutes written as Notion paragraph + heading blocks, matching the existing `_block_to_text` format used by `meeting_minutes_extractor.py` for round-trip consistency.

---

## Reuse from Existing Codebase

| Reused component | Source |
|---|---|
| `NotionClient` class | `meeting_minutes_extractor.py` — copied verbatim |
| `EXTRACTION_PROMPT` + `call_claude_cli` | `meeting_minutes_extractor.py` — called directly |
| `_telegram_notify()` | `meeting_minutes_extractor.py` — copied verbatim |
| `claude_cli_helper` | `.claude/claude_cli_helper.py` — imported as-is |
| Watcher pattern | `haven_watcher.py` — mirrored |
| Log directory convention | All existing scripts — `logs/` subfolder |
