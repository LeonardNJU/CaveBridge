# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
import os
import pytest
from cavebridge.engine import Engine
from cavebridge.llm import FakeLLM
from cavebridge.saves import SaveStore
from cavebridge.settings import Settings
from cavebridge.vocab import Vocab
from cavebridge.repl import run_repl

ADVENT = os.path.abspath("./advent")
pytestmark = pytest.mark.skipif(not os.path.exists(ADVENT),
    reason="build advent with `make CFLAGS=-DADVENT_AUTOSAVE` first")


def test_full_turn_and_save_load(tmp_path):
    live = str(tmp_path / "s.adv")
    s = Settings(language="zh", autosave_path=live)
    saves = SaveStore(str(tmp_path / "slots"))

    def factory():
        return Engine(ADVENT, seed=1, autosave_path=live)

    llm = FakeLLM(['{"command": "in"}', "你走进小屋。",
                   '{"command": "take lamp"}', "你拿起黄铜灯。"])
    out: list[str] = []
    inputs = iter(["进屋", "拿灯", "/save a", "/load a", "/quit"])
    run_repl(settings=s, engine=factory(), llm=llm, vocab=Vocab(["in"], ["lamp"], ["take"]),
             input_fn=lambda: next(inputs), output_fn=out.append,
             saves=saves, engine_factory=factory)
    assert "黄铜灯" in "\n".join(out)
    assert "a" in saves.list()
