# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.llm import FakeLLM
from cavebridge.state import GameState, ObjectRef
from cavebridge.parser import ParseResult
from cavebridge.narrator import narrate, narrate_stream

STATE = GameState(turns=2, loc=3, loc_name="inside building", dark=False)


class _RecLLM:
    """Records the messages + max_tokens of the last call."""

    def __init__(self):
        self.kw: dict = {}

    def complete(self, messages, *, json_mode=False, temperature=0.7, max_tokens=None):
        self.kw = {"messages": messages, "max_tokens": max_tokens}
        return "ok"

    def stream(self, messages, *, temperature=0.7, max_tokens=None):
        self.kw = {"messages": messages, "max_tokens": max_tokens}
        yield "ok"


def test_passes_engine_output_and_delta():
    llm = FakeLLM(["你拿起了黄铜灯。"])
    text = narrate(llm, english="OK", state=STATE,
                   parse=ParseResult(["take lamp"], False, None),
                   hint=None, language="zh", delta="now carrying: lamp")
    assert text == "你拿起了黄铜灯。"
    content = llm.calls[0]["messages"][-1]["content"]
    assert "OK" in content and "now carrying: lamp" in content


def test_cannot_explained_in_character():
    text = narrate(FakeLLM(["你没带炸药。"]), english="", state=STATE,
                   parse=ParseResult(None, True, "no explosive"),
                   hint=None, language="zh", delta=None)
    assert "炸药" in text


def test_narrate_stream_chunks_and_returns_full():
    got = []
    full = narrate_stream(FakeLLM(["你拿起了黄铜灯。"]), english="OK", state=STATE,
                          parse=ParseResult(["take lamp"], False, None),
                          hint=None, language="zh", delta=None,
                          on_chunk=got.append)
    assert full == "你拿起了黄铜灯。"
    assert "".join(got) == "你拿起了黄铜灯。"
    assert len(got) >= 1


def test_narration_lists_items_commands_and_delta():
    # Regression: the DM must convey the FULL observation — every visible item,
    # the executed action(s), and the state delta (so terse "OK" becomes feedback).
    st = GameState(turns=1, loc=3, loc_name="inside", dark=False,
                   visible=[ObjectRef(1, "keys"), ObjectRef(2, "lamp")])
    rec = _RecLLM()
    narrate(rec, english="OK\nOK", state=st,
            parse=ParseResult(["take keys", "take lamp"], False, None),
            hint=None, language="zh", delta="now carrying: keys, lamp",
            commands=["take keys", "take lamp"])
    user = rec.kw["messages"][-1]["content"]
    assert "keys, lamp" in user                            # item checklist
    assert "take keys, take lamp" in user                  # executed actions
    assert "now carrying: keys, lamp" in user              # delta for feedback
    system = rec.kw["messages"][0]["content"]
    assert "COMPLETE" in system and "ACKNOWLEDGE ACTIONS" in system


def test_narration_uses_a_token_ceiling():
    # so long room descriptions are never truncated mid-sentence
    rec = _RecLLM()
    narrate(rec, english="a long room description", state=STATE,
            parse=ParseResult(["look"], False, None), hint=None, language="zh")
    assert rec.kw["max_tokens"] and rec.kw["max_tokens"] >= 400
    rec2 = _RecLLM()
    narrate_stream(rec2, english="x", state=STATE,
                   parse=ParseResult(["look"], False, None), hint=None,
                   language="zh", on_chunk=lambda _c: None)
    assert rec2.kw["max_tokens"] and rec2.kw["max_tokens"] >= 400
