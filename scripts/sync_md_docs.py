"""sync_md_docs.py — copy all project .md files into workspace-dashboard/docs/md/

Runs from the workspace-dashboard root. Copies every .md from the main
Olympic Paints repo into docs/md/ preserving the relative path structure,
skipping venv / node_modules / .git / .pytest_cache noise.

Usage:
    python scripts/sync_md_docs.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints")
DEST_ROOT = Path(__file__).parent.parent / "docs" / "md"

SKIP_DIRS = {
    ".git", ".pytest_cache", "node_modules", "venv",
    "__pycache__", ".claude",
}

SKIP_PATH_FRAGMENTS = [
    "venv/Lib/site-packages",
    "venv\\Lib\\site-packages",
    "olympic-vector-db/venv",
    "olympic-vector-db\\venv",
]


def should_skip(path: Path) -> bool:
    parts = path.parts
    if any(p in SKIP_DIRS for p in parts):
        return True
    path_str = str(path)
    return any(frag in path_str for frag in SKIP_PATH_FRAGMENTS)


def sync() -> None:
    copied = 0
    removed = 0

    # Track which destination files are still valid
    valid_dests: set[Path] = set()

    for src in REPO_ROOT.rglob("*.md"):
        if should_skip(src):
            continue
        rel = src.relative_to(REPO_ROOT)
        dest = DEST_ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(src, dest)
            copied += 1
        valid_dests.add(dest)

    # Remove stale files (deleted from source)
    if DEST_ROOT.exists():
        for stale in DEST_ROOT.rglob("*.md"):
            if stale not in valid_dests:
                stale.unlink()
                removed += 1

    print(f"sync_md_docs: {copied} copied, {removed} removed -> {DEST_ROOT}")


if __name__ == "__main__":
    sync()
