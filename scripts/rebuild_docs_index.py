"""rebuild_docs_index.py — sync .md files and regenerate the Docs Index table in index.html

Runs weekly (Wednesday ~06:00 via Task Scheduler). Does three things:
1. Copies all project .md files into docs/md/ (via sync_md_docs logic)
2. Scans docs/md/, extracts a one-line summary from each file
3. Rewrites the <tbody id="docBody"> block in index.html
4. Commits and pushes to main

Usage:
    python scripts/rebuild_docs_index.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints")
WD_ROOT   = Path(__file__).parent.parent          # workspace-dashboard root
DOCS_MD   = WD_ROOT / "docs" / "md"
INDEX_HTML = WD_ROOT / "index.html"

SKIP_DIRS = {".git", ".pytest_cache", "node_modules", "venv", "__pycache__", ".claude"}
SKIP_PATH_FRAGMENTS = [
    "venv/Lib/site-packages", "venv\\Lib/site-packages",
    "venv\\Lib\\site-packages",
    "olympic-vector-db/venv", "olympic-vector-db\\venv",
]

# ── Area classification ────────────────────────────────────────────────────────

def classify_area(rel: Path) -> tuple[str, str]:
    """Return (area_key, area_label) for a path relative to docs/md/."""
    parts = rel.parts
    top = parts[0].lower() if parts else ""

    if top in ("agents",):
        return "agents", "Agents"
    if top == "3.resources" and len(parts) > 1 and "19. runbooks" in parts[1].lower():
        return "runbooks", "Runbooks"
    if top in ("1.projects",):
        return "projects", "Projects"
    if top == "3.resources" and len(parts) > 1 and "17. strategic" in parts[1].lower():
        return "intel", "Intel"
    if top == "2.areas" and len(parts) > 1 and any(
        x in parts[1].lower() for x in ("11. hr", "12. health")
    ):
        return "safety", "Safety/HR"
    if top == "2.areas":
        return "modules", "Modules"
    if top == "3.resources":
        return "modules", "Modules"
    if top in ("docs", "olympic-email-studio", "olympic-paints-hub",
               "geo-map", "ollama-dashboard"):
        return "modules", "Modules"
    # Root-level files
    return "root", "Root"


# ── Summary extraction ─────────────────────────────────────────────────────────

def extract_summary(path: Path) -> str:
    """Return a one-line summary from the file's first heading or first paragraph."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return path.stem.replace("-", " ").replace("_", " ").title()

    lines = text.splitlines()
    # Skip YAML front-matter
    start = 0
    if lines and lines[0].strip() == "---":
        for i, ln in enumerate(lines[1:], 1):
            if ln.strip() == "---":
                start = i + 1
                break

    summary = ""
    for ln in lines[start:]:
        stripped = ln.strip()
        if not stripped:
            continue
        # Skip badge/shield lines and HTML tags
        if stripped.startswith("![") or stripped.startswith("<"):
            continue
        # Use first heading (strip #s)
        if stripped.startswith("#"):
            summary = re.sub(r"^#+\s*", "", stripped)
            break
        # Use first non-empty prose line
        summary = stripped
        break

    # Clean up: strip markdown bold/italic, inline code, links
    summary = re.sub(r"\*\*(.+?)\*\*", r"\1", summary)
    summary = re.sub(r"\*(.+?)\*",     r"\1", summary)
    summary = re.sub(r"`(.+?)`",       r"\1", summary)
    summary = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", summary)
    summary = re.sub(r"\s+", " ", summary).strip()

    # Truncate to ~120 chars at a word boundary
    if len(summary) > 120:
        summary = summary[:117].rsplit(" ", 1)[0] + "…"

    return summary or path.stem.replace("-", " ").replace("_", " ")


# ── HTML helpers ───────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def build_row(rel: Path, summary: str) -> str:
    area_key, area_label = classify_area(rel)
    filename = rel.name
    # directory label shown in .doc-path — use forward slashes, prefix /
    dir_parts = rel.parts[:-1]
    dir_label = "/" + "/".join(dir_parts) + "/" if dir_parts else "/"

    return (
        f'              <tr data-area="{area_key}" data-file="{esc(filename)}" '
        f'data-summary="{esc(summary)}">\n'
        f'                <td><div class="doc-file">{esc(filename)}</div>'
        f'<div class="doc-path">{esc(dir_label)}</div></td>\n'
        f'                <td><span class="doc-area-pill area-{area_key}">'
        f'{area_label}</span></td>\n'
        f'                <td class="doc-summary">{esc(summary)}</td>\n'
        f'              </tr>'
    )


# ── Sync step (same logic as sync_md_docs.py) ─────────────────────────────────

def should_skip(path: Path) -> bool:
    if any(p in SKIP_DIRS for p in path.parts):
        return True
    path_str = str(path)
    return any(frag in path_str for frag in SKIP_PATH_FRAGMENTS)


def sync_files() -> int:
    copied = 0
    valid: set[Path] = set()
    for src in REPO_ROOT.rglob("*.md"):
        if should_skip(src):
            continue
        rel  = src.relative_to(REPO_ROOT)
        dest = DOCS_MD / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(src, dest)
            copied += 1
        valid.add(dest)
    removed = 0
    if DOCS_MD.exists():
        for stale in DOCS_MD.rglob("*.md"):
            if stale not in valid:
                stale.unlink()
                removed += 1
    print(f"  sync: {copied} copied, {removed} removed")
    return copied + removed


# ── Index rebuild ──────────────────────────────────────────────────────────────

def rebuild_index() -> int:
    # Collect all .md files, sorted: area-key then path
    files: list[Path] = sorted(
        DOCS_MD.rglob("*.md"),
        key=lambda p: (classify_area(p.relative_to(DOCS_MD))[0], str(p).lower())
    )

    rows: list[str] = []
    last_area = ""
    for f in files:
        rel = f.relative_to(DOCS_MD)
        area_key, _ = classify_area(rel)
        if area_key != last_area:
            rows.append(f"\n              <!-- {area_key.upper()} -->")
            last_area = area_key
        summary = extract_summary(f)
        rows.append(build_row(rel, summary))

    new_tbody = (
        '            <tbody id="docBody">\n'
        + "\n".join(rows)
        + "\n            </tbody>"
    )

    html = INDEX_HTML.read_text(encoding="utf-8")
    # Replace everything between <tbody id="docBody"> ... </tbody>
    pattern = r'<tbody id="docBody">.*?</tbody>'
    new_html, count = re.subn(pattern, new_tbody, html, flags=re.DOTALL)
    if count == 0:
        print("ERROR: could not find <tbody id=\"docBody\"> in index.html", file=sys.stderr)
        sys.exit(1)

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(f"  index: {len(files)} rows written to index.html")
    return len(files)


# ── Git push ───────────────────────────────────────────────────────────────────

def git_push(n_files: int) -> None:
    cmds = [
        ["git", "checkout", "main"],
        ["git", "add", "docs/md/", "index.html"],
        ["git", "commit", "-m", f"chore(docs-index): weekly sync — {n_files} .md files"],
        ["git", "push", "origin", "main"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=WD_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            # "nothing to commit" is fine
            if "nothing to commit" in result.stdout + result.stderr:
                print("  git: nothing changed, skipping push")
                return
            print(f"  git error ({' '.join(cmd)}):\n{result.stderr}", file=sys.stderr)
            sys.exit(1)
    print("  git: pushed to main")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("rebuild_docs_index: starting")
    sync_files()
    n = rebuild_index()
    git_push(n)
    print("rebuild_docs_index: done")
