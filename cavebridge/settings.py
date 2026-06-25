# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    language: str = "en"
    hints_enabled: bool = False
    show_raw: bool = True        # echo the canonical command(s) + raw engine output
    multi_step: bool = True      # one line -> several commands ("都拿了", "放棒子,捉鸟")
    auto_advance: bool = True    # "keep going until ..." loops
    seed: int = 1
    model: str = "gpt-4o-mini"
    base_url: str | None = None
    api_key: str | None = None
    advent_path: str = "./advent"
    autosave_path: str = ""   # set by __main__ to a unique per-session path
    timeout: float = 60.0     # per-LLM-request timeout (s) so a hung endpoint can't freeze the game

    @classmethod
    def from_env(cls) -> "Settings":
        # Purist mode: faithful to the 1977 original — keep only NL translation +
        # narration, drop the modern conveniences (unless individually overridden).
        purist = os.environ.get("CAVEBRIDGE_PURIST", "0") == "1"
        flag = lambda key, default: os.environ.get(key, default) == "1"
        return cls(
            language=os.environ.get("CAVEBRIDGE_LANG", "en"),
            hints_enabled=flag("CAVEBRIDGE_HINTS", "0"),
            show_raw=flag("CAVEBRIDGE_RAW", "1"),
            multi_step=flag("CAVEBRIDGE_MULTISTEP", "0" if purist else "1"),
            auto_advance=flag("CAVEBRIDGE_AUTOADVANCE", "0" if purist else "1"),
            seed=int(os.environ.get("CAVEBRIDGE_SEED", "1")),
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=os.environ.get("OPENAI_BASE_URL"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            advent_path=os.environ.get("CAVEBRIDGE_ADVENT", "./advent"),
            timeout=float(os.environ.get("CAVEBRIDGE_TIMEOUT", "60")),
        )
