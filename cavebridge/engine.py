# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

import re
import subprocess

from cavebridge.state import GameState, parse_state_json

_PROMPT_RE = re.compile(r"@@ADVPROMPT (CMD|ASK|AUTO)@@")
_PROMPT_ECHO = re.compile(r"^>\s")   # echoed "> command" / bare prompt line


def _clean(text: str) -> str:
    """Strip echoed prompt/command lines and collapse blank-line runs from
    engine output (keeps real output like '>>Foof!<<', which isn't '> ')."""
    out: list[str] = []
    for ln in text.split("\n"):
        s = ln.rstrip()
        if s == ">" or _PROMPT_ECHO.match(s):
            continue
        if not s and (not out or not out[-1]):   # collapse consecutive blanks
            continue
        out.append(s)
    return "\n".join(out).strip()


class Turn:
    """kind: 'normal' (has .state) | 'ask' (has .question; call answer()) |
    'ended' (process exited; .text holds the final output)."""

    def __init__(self, kind: str, text: str, state: GameState | None = None,
                 question: str | None = None):
        self.kind, self.text, self.state, self.question = kind, text, state, question


# Drives the `advent -j` subprocess over plain pipes (no PTY): the engine's
# @@ADVPROMPT@@ / @@ADVSTATE@@ sentinels are printf'd with fflush, so output
# flushes correctly without a terminal. This works on Windows, Linux and macOS.
# Single subprocess at a time (cb_prompt_kind is a process-global in the engine).
class Engine:
    def __init__(self, advent_path: str, seed: int, autosave_path: str,
                 exits_by_loc: list[list[str]] | None = None) -> None:
        self.seed = seed
        self.mode = "starting"      # starting | cmd | ask | ended
        self._exits = exits_by_loc or []   # loc id -> directional exits (front-end)
        self.proc = subprocess.Popen(
            [advent_path, "-j", "-a", autosave_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1,
        )

    def _send(self, line: str) -> None:
        try:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError, OSError):
            pass

    def _read(self) -> tuple[str, str]:
        """Read lines until the next ADVPROMPT sentinel; return (kind, text).
        kind is CMD/ASK/AUTO, or 'EOF' when the process exits."""
        buf: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":                       # pipe closed -> process ended
                return "EOF", "".join(buf)
            m = _PROMPT_RE.search(line)
            if m:
                return m.group(1), "".join(buf)
            buf.append(line)

    def _advance(self, text: str = "") -> Turn:
        while True:
            kind, before = self._read()
            text += before
            if kind == "CMD":
                self.mode = "cmd"
                return Turn("normal", _clean(text))
            if kind == "AUTO":
                self._send("no")                 # decline instructions/hints/clue
                continue
            if kind == "ASK":
                self.mode = "ask"
                return Turn("ask", _clean(text), question=_clean(before))
            self.mode = "ended"                  # EOF
            return Turn("ended", _clean(text))

    def _fetch_state(self) -> GameState:
        self._send("@state")
        _, before = self._read()                 # ADVSTATE block then CMD prompt
        st = parse_state_json(before)
        if 0 <= st.loc < len(self._exits):       # attach exits (front-end map)
            st.exits = list(self._exits[st.loc])
        return st

    def _finish(self, turn: Turn) -> Turn:
        if turn.kind == "normal":
            turn.state = self._fetch_state()
        return turn

    def start(self, fresh: bool) -> Turn:
        """Drive to the first command prompt. Returns a Turn: 'normal' (with
        initial .state) or 'ended' if the process exited (e.g. corrupt restore)."""
        turn = self._advance()                   # declines instructions if fresh
        text = turn.text                         # intro / restore banner
        if fresh and turn.kind == "normal":
            self._send(f"seed {self.seed}")      # seed ONLY fresh games
            turn = self._advance()
            turn.text = text + turn.text         # keep the intro, append seed echo
        return self._finish(turn)

    def step(self, command: str) -> Turn:
        if self.mode != "cmd":
            raise RuntimeError(f"step() requires a command prompt, in {self.mode}")
        command = (command or "").strip()
        if not command or command.startswith("#") or len(command.split()) > 2:
            command = "look"                     # keep protocol in sync
        self._send(command)
        return self._finish(self._advance())

    def answer(self, yes: bool) -> Turn:
        if self.mode != "ask":
            raise RuntimeError(f"answer() requires an ask prompt, in {self.mode}")
        self._send("yes" if yes else "no")
        return self._finish(self._advance())

    def state(self) -> GameState:
        if self.mode != "cmd":
            raise RuntimeError(f"state() requires a command prompt, in {self.mode}")
        return self._fetch_state()

    def close(self) -> Turn | None:
        try:
            if self.mode == "ended":
                return None
            if self.mode == "ask":
                # Decline any pending gameplay yes/no before quitting, so "quit"
                # is never misread as a yes/no answer (e.g. the dragon).
                self._send("no")
                t = self._advance()
                if t.kind == "ended":
                    return t
            self._send("quit")
            turn = self._advance()               # quit -> ASK confirm
            if turn.kind == "ask":
                self._send("yes")
                turn = self._advance()           # -> ended (EOF)
            return turn
        except Exception:
            return None
        finally:
            for step in (
                lambda: self.proc.stdin.close(),
                lambda: self.proc.terminate(),
                lambda: self.proc.wait(timeout=3),
            ):
                try:
                    step()
                except Exception:
                    pass
            if self.proc.poll() is None:
                try:
                    self.proc.kill()
                except Exception:
                    pass
