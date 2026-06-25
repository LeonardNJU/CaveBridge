# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

import os
import shutil


class SaveStore:
    def __init__(self, slots_dir: str):
        self.slots_dir = slots_dir
        os.makedirs(slots_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        safe = "".join(c for c in name if c.isalnum() or c in "-_") or "save"
        return os.path.join(self.slots_dir, f"{safe}.adv")

    def save(self, name: str, live_autosave_path: str) -> str:
        dst = self._path(name)
        shutil.copyfile(live_autosave_path, dst)
        return dst

    def load(self, name: str, live_autosave_path: str) -> None:
        src = self._path(name)
        if not os.path.exists(src):
            raise FileNotFoundError(f"no save slot named {name!r}")
        shutil.copyfile(src, live_autosave_path)

    def list(self) -> list[str]:
        return sorted(f[:-4] for f in os.listdir(self.slots_dir) if f.endswith(".adv"))
