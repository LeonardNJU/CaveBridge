# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

import re
from typing import Iterator, Protocol

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think(text: str) -> str:
    """Remove <think>...</think> reasoning blocks (e.g. Qwen3) from a full reply."""
    return _THINK_RE.sub("", text).strip()


def _suffix_prefix_len(s: str, tag: str) -> int:
    """Longest suffix of s that is a (proper) prefix of tag — used to retain a
    possibly-incomplete tag at a chunk boundary while streaming."""
    for k in range(min(len(s), len(tag) - 1), 0, -1):
        if tag.startswith(s[-k:]):
            return k
    return 0


def strip_think_stream(deltas: Iterator[str]) -> Iterator[str]:
    """Transform a stream of text deltas, suppressing <think>...</think> spans.
    Tolerant of the tags being split across deltas."""
    OPEN, CLOSE = "<think>", "</think>"
    buf = ""
    inside = False
    for d in deltas:
        buf += d
        while True:
            if not inside:
                i = buf.find(OPEN)
                if i != -1:
                    if i > 0:
                        yield buf[:i]
                    buf = buf[i + len(OPEN):]
                    inside = True
                    continue
                keep = _suffix_prefix_len(buf, OPEN)   # maybe a partial <think>
                if len(buf) > keep:
                    yield buf[:len(buf) - keep]
                    buf = buf[len(buf) - keep:]
                break
            else:
                j = buf.find(CLOSE)
                if j != -1:
                    buf = buf[j + len(CLOSE):]
                    inside = False
                    continue
                buf = buf[len(buf) - _suffix_prefix_len(buf, CLOSE):]
                break
    if not inside and buf:
        yield buf


class LLM(Protocol):
    def complete(self, messages: list[dict], *, json_mode: bool = False,
                 temperature: float = 0.7, max_tokens: int | None = None) -> str: ...

    def stream(self, messages: list[dict], *, temperature: float = 0.7,
               max_tokens: int | None = None) -> Iterator[str]: ...


class LLMClient:
    def __init__(self, model: str, base_url: str | None, api_key: str | None,
                 timeout: float = 60.0):
        from openai import OpenAI
        self._OpenAI = OpenAI
        self._timeout = timeout
        self.model = model
        self.client = self._build(base_url, api_key)

    def _build(self, base_url: str | None, api_key: str | None):
        # A finite timeout (+ one retry) so a hung endpoint surfaces as an error in
        # ~seconds instead of freezing the game for the SDK's 10-minute default.
        return self._OpenAI(base_url=base_url, api_key=api_key or "none",
                            timeout=self._timeout, max_retries=1)

    def reconfigure(self, base_url: str | None, api_key: str | None,
                    model: str) -> None:
        """Rebuild the client/model so /config can change the endpoint live."""
        self.model = model
        self.client = self._build(base_url, api_key)

    def complete(self, messages: list[dict], *, json_mode: bool = False,
                 temperature: float = 0.7, max_tokens: int | None = None) -> str:
        kwargs: dict = {"model": self.model, "messages": messages,
                        "temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if json_mode:
            # Prefer native JSON mode, but some OpenAI-compatible servers
            # (e.g. LM Studio) reject {"type":"json_object"}. The prompts
            # already demand JSON-only output, so fall back transparently.
            try:
                resp = self.client.chat.completions.create(
                    **kwargs, response_format={"type": "json_object"})
                return strip_think(resp.choices[0].message.content or "")
            except Exception:
                pass
        resp = self.client.chat.completions.create(**kwargs)
        return strip_think(resp.choices[0].message.content or "")

    def stream(self, messages: list[dict], *, temperature: float = 0.7,
               max_tokens: int | None = None) -> Iterator[str]:
        kwargs: dict = {"model": self.model, "messages": messages,
                        "temperature": temperature, "stream": True}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        resp = self.client.chat.completions.create(**kwargs)

        def _deltas() -> Iterator[str]:
            for chunk in resp:
                if chunk.choices:
                    d = chunk.choices[0].delta.content
                    if d:
                        yield d

        yield from strip_think_stream(_deltas())


class FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def complete(self, messages: list[dict], *, json_mode: bool = False,
                 temperature: float = 0.7, max_tokens: int | None = None) -> str:
        self.calls.append({"messages": messages, "json_mode": json_mode,
                           "temperature": temperature})
        return self._responses.pop(0)

    def stream(self, messages: list[dict], *, temperature: float = 0.7,
               max_tokens: int | None = None) -> Iterator[str]:
        self.calls.append({"messages": messages, "stream": True,
                           "temperature": temperature})
        text = self._responses.pop(0)
        mid = len(text) // 2 or len(text)
        for part in (text[:mid], text[mid:]):   # 2 chunks, to exercise consumers
            if part:
                yield part
