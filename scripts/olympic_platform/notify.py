"""Telegram alert for failed jobs.

Reads TELEGRAM_BOT_TOKEN from environment. If absent, calls become no-ops
so the wrapper still records heartbeats in environments without Telegram.

Chat ID is fixed to Quintus's bot chat (8042233389) per project memory.
"""

from __future__ import annotations

import os
import ssl
import urllib.parse
import urllib.request

try:
    import truststore  # local CA inspection — required on this machine
    truststore.inject_into_ssl()
except Exception:
    pass

CHAT_ID = "8042233389"
API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def send_failure_alert(
    job_id: str,
    agent: str,
    exit_code: int,
    stderr_tail: str,
    log_path: str,
) -> bool:
    """Send a failure alert to Telegram. Returns True on success, False otherwise.

    Never raises — failure to notify must not mask the original job failure.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return False

    body_lines = [
        f"❌ <b>{agent} — {job_id}</b> failed",
        f"exit_code: <code>{exit_code}</code>",
        f"log: <code>{log_path}</code>",
    ]
    if stderr_tail.strip():
        tail = stderr_tail.strip()
        if len(tail) > 800:
            tail = "…" + tail[-800:]
        body_lines.append("<pre>" + _html_escape(tail) + "</pre>")

    payload = urllib.parse.urlencode(
        {
            "chat_id": CHAT_ID,
            "text": "\n".join(body_lines),
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        API_BASE.format(token=token),
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context()) as resp:
            return resp.status == 200
    except Exception:
        return False


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
