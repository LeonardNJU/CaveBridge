# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

_STATE_RE = re.compile(r"@@ADVSTATE_BEGIN@@(\{.*?\})@@ADVSTATE_END@@", re.DOTALL)


@dataclass
class ObjectRef:
    id: int
    name: str
    prop: int = 0


@dataclass
class GameState:
    turns: int
    loc: int
    loc_name: str
    dark: bool
    lamp_on: bool = False
    fuel: int = 0
    flags: dict = field(default_factory=dict)
    exits: list[str] = field(default_factory=list)
    visible: list[ObjectRef] = field(default_factory=list)
    inventory: list[ObjectRef] = field(default_factory=list)

    @classmethod
    def from_obj(cls, d: dict) -> "GameState":
        lamp = d.get("lamp", {}) or {}

        def mk(lst):
            return [ObjectRef(o["id"], o["name"], o.get("prop", 0)) for o in lst]

        return cls(
            turns=d["turns"], loc=d["loc"], loc_name=d["loc_name"],
            dark=bool(d["dark"]), lamp_on=bool(lamp.get("on", False)),
            fuel=int(lamp.get("fuel", 0)), flags=d.get("flags", {}) or {},
            exits=list(d.get("exits", []) or []),
            visible=mk(d.get("visible", [])), inventory=mk(d.get("inventory", [])),
        )

    def signature(self) -> tuple:
        return (
            self.loc, self.dark,
            tuple(sorted((o.id, o.prop) for o in self.inventory)),
            tuple(sorted((o.id, o.prop) for o in self.visible)),
        )


def parse_state_json(raw: str) -> GameState:
    m = _STATE_RE.search(raw)
    if not m:
        raise ValueError("no @@ADVSTATE@@ block in engine output")
    return GameState.from_obj(json.loads(m.group(1)))
