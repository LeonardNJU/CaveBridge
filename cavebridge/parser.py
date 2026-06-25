# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

import json
from dataclasses import dataclass

from cavebridge.llm import LLM
from cavebridge.state import GameState
from cavebridge.vocab import Vocab

_HEADER = """You are the input parser for Colossal Cave Adventure. Translate the \
player's free text into one or more canonical engine commands. Each command is at \
most two words: a verb plus optional object, or a single direction/word.

Reply with JSON only:
  {"commands": ["<cmd>", ...]}   one or more canonical commands, in order, OR
  {"cannot": true, "reason": "<short in-world reason, no spoilers>"}   if impossible.

Rules:
- A single action -> a one-element list."""

# Optional rule — multi-step / batch commands. Dropped in purist mode.
_RULE_MULTISTEP = """\
- Several actions in one request ("go north then take the gold", "放棒子，捉鸟") ->
  one command per action, in order.
- "Take everything"/"都拿了"/"拿所有东西" -> the single token ["@takeall"] (optionally
  after a move, e.g. ["enter","@takeall"]). Do NOT expand it into per-object takes
  yourself. Likewise "drop everything" -> ["@dropall"]."""

# Optional rule — auto-advance loops. Dropped in purist mode.
_RULE_AUTOADVANCE = """\
- "Keep going <dir> until <X>" / "一直往<dir>走直到<X>" / "<dir>走到<X>为止" ->
  ["@repeat:<canonical command>:<the goal as a short English phrase>"].
  e.g. "顺着小溪一直下游直到看见栅栏" -> ["@repeat:downstream:reach the grate"];
  "一直往北走" -> ["@repeat:north:keep heading north until something blocks the way"]."""

# Always-on rules — exits Q&A, save/load routing, passthrough, vocabulary.
_RULE_TAIL = """\
- A question about where the player can go / what the exits are ("有哪些出口","能去哪",
  "附近有什么路") -> ["@exits"].
- Saving/loading is handled by the front-end, NOT the engine. "save"/"存档"/"保存" ->
  ["@save"]; "load"/"读档"/"恢复存档" -> ["@load"]. Never emit the engine's save/resume.
- If the player typed a valid game word, magic word, meta word, or direction directly
  (xyzzy, plugh, score, inventory, look, n, west, ...), pass it through unchanged.
- Use ONLY the game's vocabulary and the objects/exits in the context; never invent.
- Use {"cannot"} only for intents impossible in this world (no such ability/item);
  otherwise prefer a best-effort command and let the engine judge."""

_RULE_ONESHOT = ("- The player gets exactly ONE action per turn. Never combine "
                 "actions or take/drop everything at once; emit a single command.")


def _system_prompt(multi_step: bool, auto_advance: bool) -> str:
    """Assemble the parser system prompt. Purist mode (both off) keeps only
    translation + the always-on routing rules."""
    parts = [_HEADER]
    if multi_step:
        parts.append(_RULE_MULTISTEP)
    if auto_advance:
        parts.append(_RULE_AUTOADVANCE)
    parts.append(_RULE_TAIL)
    if not multi_step:
        parts.append(_RULE_ONESHOT)
    return "\n".join(parts)


@dataclass
class ParseResult:
    commands: list[str] | None
    cannot: bool
    reason: str | None


def _extract_json(text: str) -> dict | None:
    """Extract and parse the first balanced {...} object from a reply (reasoning
    models may wrap the JSON in prose). Returns None if none parses."""
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


def _vocab_text(vocab: Vocab) -> str:
    """Stable across turns -> stays in the cached prefix."""
    return ("Use only the game's vocabulary:\n"
            f"Motions/directions: {', '.join(vocab.motions[:90])}\n"
            f"Verbs: {', '.join(vocab.actions[:90])}\n"
            f"Objects: {', '.join(vocab.objects[:90])}")


def _scene_text(state: GameState) -> str:
    """Volatile -> goes last so it doesn't break the cached prefix."""
    vis = ", ".join(o.name for o in state.visible) or "(nothing notable)"
    inv = ", ".join(o.name for o in state.inventory) or "(empty)"
    exits = ", ".join(state.exits) or "(unknown)"
    return (f"Current location: {state.loc_name}. Dark: {state.dark}.\n"
            f"Visible here: {vis}.\nCarrying: {inv}.\nExits: {exits}.")


def parse_intent(llm: LLM, state: GameState, history: list[str],
                 player_text: str, vocab: Vocab, language: str, *,
                 multi_step: bool = True, auto_advance: bool = True) -> ParseResult:
    # Cache-friendly order: stable (rules + vocab) first, then recent turns
    # (append-only), then the volatile scene + player input.
    system = _system_prompt(multi_step, auto_advance) + "\n\n" + _vocab_text(vocab)
    messages = [{"role": "system", "content": system}]
    if history:
        # full append-only history -> stable growing prefix (cache-friendly)
        messages.append({"role": "user", "content":
            "Recent turns (oldest first), for resolving references like 'the "
            "passage' or 'it':\n" + "\n".join(history)})
    messages.append({"role": "user", "content":
                     _scene_text(state) + f"\n\nPlayer ({language}): {player_text}"})
    raw = llm.complete(messages, json_mode=True, temperature=0.0)
    data = _extract_json(raw)
    if data is None:
        return ParseResult(None, True, "(could not understand that)")
    if data.get("cannot"):
        return ParseResult(None, True, data.get("reason", ""))
    cmds = data.get("commands")
    if isinstance(cmds, str):
        cmds = [cmds]
    if not cmds:                              # tolerate {"command": "..."} too
        one = data.get("command")
        cmds = [one] if isinstance(one, str) else []
    cmds = [c.strip() for c in cmds if isinstance(c, str) and c.strip()][:10]
    if not cmds:
        return ParseResult(None, True, "(no actionable command)")
    return ParseResult(cmds, False, None)


def judge_loop_stop(llm: LLM, goal: str, observation: str) -> tuple[bool, str]:
    """LLM decides whether an auto-advance loop should stop. Stop on goal reached,
    danger, or a stall. Defaults to STOP if the reply can't be parsed (never loops
    forever on bad output)."""
    messages = [
        {"role": "system", "content":
         "You supervise an auto-advance loop in a text adventure. Given the player's "
         "goal and the latest game observation, decide whether to STOP advancing. "
         "Stop if: the goal appears reached, OR there is danger (darkness, a pit, a "
         "monster/dwarf, a threat of death, getting lost in a maze), OR the move "
         "failed/stalled. Otherwise continue. Reply JSON only: "
         '{"stop": true|false, "reason": "<short>"}.'},
        {"role": "user", "content": f"Goal: {goal}\nLatest observation:\n{observation}"},
    ]
    raw = llm.complete(messages, json_mode=True, temperature=0.0)
    data = _extract_json(raw)
    if not data:
        return True, "(stopping: unclear)"
    return bool(data.get("stop", True)), str(data.get("reason", ""))


def parse_yes_no(llm: LLM, question: str, player_text: str, language: str) -> bool:
    messages = [
        {"role": "system", "content": 'Map the player reply to the yes/no '
         'question to JSON {"yes": true|false}. Reply with JSON only.'},
        {"role": "user", "content": f"Question: {question}\nPlayer ({language}): {player_text}"},
    ]
    raw = llm.complete(messages, json_mode=True, temperature=0.0)
    data = _extract_json(raw)
    return bool(data.get("yes", False)) if data else False
