# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
import os
import pytest
from cavebridge.vocab import load_vocab, _words

YAML = os.path.abspath("./adventure.yaml")
pytestmark = pytest.mark.skipif(not os.path.exists(YAML), reason="run from repo root")


def test_unpacks_tuples_and_none_words():
    assert _words([("HERE", {"words": None}), ("KEYS", {"words": ["keys", "key"]})]) == ["key", "keys"]


def test_core_words_present_and_sorted():
    v = load_vocab(YAML)
    assert "lamp" in v.objects or "lantern" in v.objects
    assert "take" in v.actions or "carry" in v.actions
    assert v.objects == sorted(set(v.objects))


def test_load_exits_clean_and_spoiler_free():
    from cavebridge.vocab import load_exits
    ex = load_exits(YAML)
    start = set(ex[1])                              # LOC_START (id 1) = the road
    assert {"north", "south", "east", "west"} <= start
    assert "in" in start
    # never leak magic words / named-place teleports as "exits"
    for loc in ex:
        assert not ({"xyzzy", "plugh", "plover", "depression"} & set(loc))


def test_terrain_motions_are_named_not_collapsed_to_down():
    # Regression for "下游不是向下": terrain-following moves surface as their own
    # words (downstream/upstream/…), never collapsed into "down", and the raw
    # 5-char motion tokens never leak.
    from cavebridge.vocab import load_exits
    words = set()
    for loc in load_exits(YAML):
        words |= set(loc)
    assert "downstream" in words                       # the mapping actually fires
    assert not ({"DOWNS", "STREA", "GULLY", "UPSTR", "FORES"} & words)
    clean = {"north", "south", "east", "west", "ne", "nw", "se", "sw",
             "up", "down", "in", "out",
             "downstream", "upstream", "forest", "crawl", "canyon"}
    assert words <= clean                              # nothing unexpected leaks
