# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.llm import FakeLLM, LLMClient, strip_think, strip_think_stream


def test_strip_think_full():
    assert strip_think('<think>reasoning...</think>{"command":"take lamp"}') == '{"command":"take lamp"}'
    assert strip_think("no think here") == "no think here"


def test_strip_think_stream_suppresses_and_handles_split_tags():
    # tags split across deltas must still be suppressed
    deltas = ["Hello <th", "ink>secret rea", "soning</thi", "nk> world", "!"]
    assert "".join(strip_think_stream(iter(deltas))) == "Hello  world!"


def test_strip_think_stream_passthrough_without_tags():
    assert "".join(strip_think_stream(iter(["a", "bc", "d"]))) == "abcd"


def test_fake_stream_yields_chunks():
    llm = FakeLLM(["hello world"])
    chunks = list(llm.stream([{"role": "user", "content": "x"}]))
    assert "".join(chunks) == "hello world"
    assert len(chunks) >= 1 and llm.calls[0]["stream"] is True


def test_fake_queue_and_record():
    llm = FakeLLM(["a", "b"])
    assert llm.complete([{"role": "user", "content": "x"}], json_mode=True) == "a"
    assert llm.complete([{"role": "user", "content": "y"}]) == "b"
    assert llm.calls[0]["json_mode"] is True


def test_llmclient_falls_back_when_json_object_rejected():
    # Some OpenAI-compatible servers (LM Studio) reject json_object; the client
    # must retry without response_format rather than crash.
    used_response_format = []

    class _Msg:
        content = '{"ok": 1}'

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    class _Completions:
        def create(self, **kw):
            used_response_format.append("response_format" in kw)
            if "response_format" in kw:
                raise RuntimeError("'response_format.type' must be ...")
            return _Resp()

    c = LLMClient.__new__(LLMClient)   # bypass __init__ (no openai/network)
    c.model = "m"
    c.client = type("C", (), {"chat": type("Ch", (), {"completions": _Completions()})()})()
    out = c.complete([{"role": "user", "content": "x"}], json_mode=True)
    assert out == '{"ok": 1}'
    assert used_response_format == [True, False]   # tried, then fell back


def _client_capturing(seen):
    class _Completions:
        def create(self, **kw):
            seen.append(kw.get("max_tokens"))
            if kw.get("stream"):
                return iter([])                       # no chunks
            msg = type("M", (), {"content": "x"})()
            return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()

    c = LLMClient.__new__(LLMClient)
    c.model = "m"
    c.client = type("Cl", (), {"chat": type("Ch", (), {"completions": _Completions()})()})()
    return c


def test_complete_and_stream_forward_max_tokens():
    seen: list = []
    c = _client_capturing(seen)
    c.complete([{"role": "user", "content": "x"}], max_tokens=800)
    list(c.stream([{"role": "user", "content": "x"}], max_tokens=512))
    assert seen == [800, 512]


def test_max_tokens_omitted_when_none():
    seen_keys = []

    class _Completions:
        def create(self, **kw):
            seen_keys.append("max_tokens" in kw)
            msg = type("M", (), {"content": "x"})()
            return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()

    c = LLMClient.__new__(LLMClient)
    c.model = "m"
    c.client = type("Cl", (), {"chat": type("Ch", (), {"completions": _Completions()})()})()
    c.complete([{"role": "user", "content": "x"}])      # no max_tokens
    assert seen_keys == [False]                         # not sent when unset


def test_reconfigure_rebuilds_client_and_model():
    made = []

    def fake_openai(base_url=None, api_key=None, **kw):
        made.append((base_url, api_key, kw.get("timeout")))
        return ("client", base_url, api_key)

    c = LLMClient.__new__(LLMClient)
    c._OpenAI = fake_openai
    c._timeout = 60.0
    c.model, c.client = "old", "oldclient"
    c.reconfigure("http://new/v1", "k2", "newmodel")
    assert c.model == "newmodel"
    assert c.client == ("client", "http://new/v1", "k2")
    assert made == [("http://new/v1", "k2", 60.0)]      # timeout passed through
