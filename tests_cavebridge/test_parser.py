# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.llm import FakeLLM
from cavebridge.state import GameState, ObjectRef
from cavebridge.vocab import Vocab
from cavebridge.parser import _system_prompt, parse_intent, parse_yes_no

STATE = GameState(turns=1, loc=3, loc_name="inside building", dark=False,
                  visible=[ObjectRef(2, "lamp")], inventory=[])
VOCAB = Vocab(["west", "in"], ["lamp"], ["take"])


def test_maps_and_uses_json():
    r = parse_intent(FakeLLM(['{"command": "take lamp"}']), STATE, [], "拿灯", VOCAB, "zh")
    assert (r.cannot, r.commands) == (False, ["take lamp"])


def test_multi_command_batch():
    r = parse_intent(FakeLLM(['{"commands": ["take keys", "take lamp", "take food"]}']),
                     STATE, [], "都拿了", VOCAB, "zh")
    assert (r.cannot, r.commands) == (False, ["take keys", "take lamp", "take food"])


def test_out_of_world():
    r = parse_intent(FakeLLM(['{"cannot": true, "reason": "你没有炸药"}']),
                     STATE, [], "炸墙", VOCAB, "zh")
    assert r.cannot and r.commands is None and "炸药" in r.reason


def test_malformed_and_empty_are_safe():
    assert parse_intent(FakeLLM(["not json"]), STATE, [], "x", VOCAB, "en").cannot
    assert parse_intent(FakeLLM(['{"command": ""}']), STATE, [], "x", VOCAB, "en").cannot


def test_yes_no():
    assert parse_yes_no(FakeLLM(['{"yes": true}']), "Quit?", "好的", "zh") is True
    assert parse_yes_no(FakeLLM(["garbage"]), "Quit?", "...", "en") is False


def test_purist_prompt_drops_conveniences_keeps_ux():
    full = _system_prompt(multi_step=True, auto_advance=True)
    pure = _system_prompt(multi_step=False, auto_advance=False)
    assert "@takeall" in full and "@repeat" in full
    assert "@takeall" not in pure and "@repeat" not in pure   # gameplay conveniences gone
    assert "exactly ONE action" in pure                       # one-shot rule added
    assert "@exits" in pure and "@save" in pure               # UX routing always kept


def test_parse_intent_threads_purist_into_prompt():
    llm = FakeLLM(['{"command": "take lamp"}'])
    parse_intent(llm, STATE, [], "拿灯", VOCAB, "zh",
                 multi_step=False, auto_advance=False)
    system = llm.calls[0]["messages"][0]["content"]
    assert "@takeall" not in system and "@repeat" not in system


def test_json_extracted_from_surrounding_prose():
    # reasoning models may wrap JSON in prose; the parser must still find it
    wrapped = 'Sure! Here is the command:\n{"command": "take lamp"}\nHope that helps.'
    r = parse_intent(FakeLLM([wrapped]), STATE, [], "拿灯", VOCAB, "zh")
    assert (r.cannot, r.commands) == (False, ["take lamp"])
    assert parse_yes_no(FakeLLM(['ok -> {"yes": true} done']), "Q?", "好", "zh") is True
