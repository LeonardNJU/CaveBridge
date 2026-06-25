# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.llm import FakeLLM
from cavebridge.state import GameState, ObjectRef
from cavebridge.vocab import Vocab
from cavebridge.hints import HintManager

V = Vocab([], [], [])


def _s(loc, prop=0):
    return GameState(turns=loc, loc=loc, loc_name="x", dark=False,
                     visible=[ObjectRef(2, "o", prop)], inventory=[])


def test_disabled_silent():
    hm = HintManager(enabled=False, threshold=2)
    hm.observe(_s(1))
    assert hm.maybe_hint(FakeLLM([]), _s(1), V, "en") is None


def test_hint_after_threshold():
    hm = HintManager(enabled=True, threshold=2)
    for _ in range(3):
        hm.observe(_s(1))
    assert hm.maybe_hint(FakeLLM(["look down"]), _s(1), V, "en") == "look down"


def test_prop_change_resets():
    hm = HintManager(enabled=True, threshold=2)
    hm.observe(_s(1, 0)); hm.observe(_s(1, 0)); hm.observe(_s(1, 1))
    assert hm.maybe_hint(FakeLLM([]), _s(1, 1), V, "en") is None
