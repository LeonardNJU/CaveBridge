# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.config import config_path, load_config, save_config


def test_missing_file_returns_empty(tmp_path):
    assert load_config(str(tmp_path / "nope.json")) == {}


def test_roundtrip_keeps_known_fields_only(tmp_path):
    p = config_path(str(tmp_path))
    save_config(p, {"base_url": "http://x/v1", "api_key": "k", "model": "m",
                    "language": "zh", "junk": "drop me"})
    got = load_config(p)
    assert got == {"base_url": "http://x/v1", "api_key": "k", "model": "m",
                   "language": "zh"}


def test_blank_values_are_not_persisted(tmp_path):
    p = config_path(str(tmp_path))
    save_config(p, {"base_url": "", "api_key": None, "model": "m", "language": "en"})
    assert load_config(p) == {"model": "m", "language": "en"}


def test_corrupt_file_is_ignored(tmp_path):
    p = config_path(str(tmp_path))
    (tmp_path / "config.json").write_text("{not json", encoding="utf-8")
    assert load_config(p) == {}
