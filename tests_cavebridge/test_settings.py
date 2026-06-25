# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.settings import Settings


def test_defaults():
    s = Settings()
    assert s.language == "en" and s.hints_enabled is False
    assert s.advent_path == "./advent"


def test_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://x/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_MODEL", "m")
    monkeypatch.setenv("CAVEBRIDGE_LANG", "zh")
    s = Settings.from_env()
    assert (s.base_url, s.api_key, s.model, s.language) == ("http://x/v1", "k", "m", "zh")


def test_conveniences_on_by_default():
    s = Settings()
    assert s.multi_step is True and s.auto_advance is True


def test_purist_env_disables_conveniences(monkeypatch):
    monkeypatch.setenv("CAVEBRIDGE_PURIST", "1")
    s = Settings.from_env()
    assert s.multi_step is False and s.auto_advance is False


def test_purist_can_be_overridden_per_feature(monkeypatch):
    monkeypatch.setenv("CAVEBRIDGE_PURIST", "1")
    monkeypatch.setenv("CAVEBRIDGE_AUTOADVANCE", "1")   # explicit override wins
    s = Settings.from_env()
    assert s.multi_step is False and s.auto_advance is True
