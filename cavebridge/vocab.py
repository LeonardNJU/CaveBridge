# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass
class Vocab:
    motions: list[str]
    objects: list[str]
    actions: list[str]


def _words(section: list) -> list[str]:
    out: set[str] = set()
    for entry in section:
        if isinstance(entry, (tuple, list)) and len(entry) == 2:
            attrs = entry[1]
        elif isinstance(entry, dict):
            attrs = next(iter(entry.values()))
        else:
            continue
        for w in (attrs or {}).get("words") or []:
            if w:
                out.add(str(w).lower())
    return sorted(out)


def load_vocab(yaml_path: str) -> Vocab:
    with open(yaml_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return Vocab(_words(data.get("motions", [])),
                 _words(data.get("objects", [])),
                 _words(data.get("actions", [])))


# Travel-rule verb tokens (5-char-uppercased) that are plain directions, mapped
# to a clean word. Excludes magic words / named-place teleports, so exits never
# spoil. Front-end only — computed from adventure.yaml, no engine change.
_DIR = {
    # compass / vertical / in-out
    "NORTH": "north", "SOUTH": "south", "EAST": "east", "WEST": "west",
    "NE": "ne", "NW": "nw", "SE": "se", "SW": "sw",
    "UP": "up", "UPWAR": "up", "DOWN": "down",
    "ENTER": "in", "IN": "in", "INSID": "in", "INWAR": "in",
    "OUT": "out", "OUTSI": "out",
    # common terrain-following moves (named in room text; not spoilers)
    "DOWNS": "downstream", "STREA": "downstream", "GULLY": "downstream",
    "UPSTR": "upstream", "FORES": "forest", "CRAWL": "crawl", "CANYO": "canyon",
}


def load_exits(yaml_path: str) -> list[list[str]]:
    """Map location index -> clean directional exit words, parsed from the
    travel rules in adventure.yaml. Index matches the engine's `loc` id."""
    with open(yaml_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    out: list[list[str]] = []
    for entry in data.get("locations", []):
        if isinstance(entry, (tuple, list)) and len(entry) == 2:
            attrs = entry[1]
        elif isinstance(entry, dict):
            attrs = next(iter(entry.values()))
        else:
            attrs = {}
        seen: list[str] = []
        for rule in (attrs or {}).get("travel", []) or []:
            for verb in rule.get("verbs", []) or []:
                w = _DIR.get(str(verb).upper())
                if w and w not in seen:
                    seen.append(w)
        out.append(seen)
    return out
