# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

from cavebridge.llm import LLM
from cavebridge.state import GameState
from cavebridge.vocab import Vocab

_SYSTEM = """You are a gentle, tiered hint engine for Colossal Cave Adventure.
Produce ONE short nudge in the target language. Lower tiers hint at WHAT to
consider; only the highest tier names a concrete next step. Never dump the
full solution."""


class HintManager:
    def __init__(self, enabled: bool, threshold: int = 3):
        self.enabled = enabled
        self.threshold = threshold
        self._last_sig: tuple | None = None
        self._stuck = 0

    def observe(self, state: GameState) -> None:
        sig = state.signature()
        self._stuck = self._stuck + 1 if sig == self._last_sig else 0
        self._last_sig = sig

    def _tier(self, explicit: bool) -> int:
        return 3 if explicit else 1 + min(self._stuck - self.threshold, 1)

    def maybe_hint(self, llm: LLM, state: GameState, vocab: Vocab, language: str,
                   *, explicit: bool = False) -> str | None:
        if not explicit and (not self.enabled or self._stuck < self.threshold):
            return None
        inv = ", ".join(o.name for o in state.inventory) or "(empty)"
        vis = ", ".join(o.name for o in state.visible) or "(nothing)"
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content":
                f"Target language: {language}. Hint tier: {self._tier(explicit)} "
                f"(1=subtle,3=concrete).\nLocation: {state.loc_name}.\n"
                f"Carrying: {inv}. Visible: {vis}."},
        ]
        return llm.complete(messages, temperature=0.5)
