# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
"""Persistent player config (LLM connection + language).

Stored as JSON in the save directory so prebuilt-binary users never have to set
environment variables: the first run asks for the connection details and writes
them here; later runs read them; `/config` edits them.
"""
from __future__ import annotations

import json
import os

# Keys we persist. api_key is stored in plaintext (like ~/.netrc); the file is
# chmod 0600 on save. For local servers the key is a throwaway value anyway.
FIELDS = ("base_url", "api_key", "model", "language")


def config_path(save_dir: str) -> str:
    return os.path.join(save_dir, "config.json")


def load_config(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return {k: data[k] for k in FIELDS if k in data and data[k] is not None} \
            if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(path: str, values: dict) -> None:
    data = {k: values.get(k) for k in FIELDS if values.get(k)}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)        # best-effort; ignored on Windows
    except OSError:
        pass
