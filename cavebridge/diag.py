# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
"""Error snapshots + one-click GitHub issue reporting.

When a turn fails (the LLM endpoint errors, or returns nothing), we write a
sanitized snapshot to <save_dir>/errors/ and offer a pre-filled "New issue" URL.
The snapshot never contains the API key — only the endpoint URL and model, which
are what's useful for debugging a connection problem.
"""
from __future__ import annotations

import os
import urllib.parse

REPO = "LeonardNJU/CaveBridge"


def errors_dir(save_dir: str) -> str:
    return os.path.join(save_dir, "errors")


def _next_path(save_dir: str, kind: str) -> str:
    d = errors_dir(save_dir)
    os.makedirs(d, exist_ok=True)
    n = 1 + sum(1 for f in os.listdir(d) if f.endswith(".txt"))
    return os.path.join(d, f"{kind}-{n}.txt")


def build_report(*, kind: str, summary: str, detail: str, base_url: str | None,
                 model: str | None, language: str, player_input: str,
                 location: str, recent: list[str]) -> str:
    """Assemble the snapshot text. NEVER include the api_key."""
    import platform
    import sys
    lines = [
        "## CaveBridge error report",
        f"- kind: {kind}",
        f"- summary: {summary}",
        f"- model: {model or '(unset)'}",
        f"- endpoint: {base_url or '(default OpenAI)'}",
        f"- language: {language}",
        f"- python: {sys.version.split()[0]}  platform: {platform.platform()}",
        f"- player input: {player_input!r}",
        f"- location: {location}",
        "",
        "## recent turns",
        *(recent[-6:] or ["(none)"]),
        "",
        "## detail",
        "```",
        detail.strip(),
        "```",
    ]
    return "\n".join(lines)


def save_snapshot(save_dir: str, kind: str, text: str) -> str:
    """Write the snapshot to disk; return its path."""
    path = _next_path(save_dir, kind)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def issue_url(title: str, body: str) -> str:
    """Pre-filled GitHub 'New issue' URL the user can open, review, and submit."""
    note = ("_Before submitting, please review the snapshot below and remove "
            "anything you'd rather not share._\n\n")
    q = urllib.parse.urlencode({
        "title": title,
        "labels": "bug",
        "body": (note + body)[:6500],     # keep the URL under GitHub's length limit
    })
    return f"https://github.com/{REPO}/issues/new?{q}"
