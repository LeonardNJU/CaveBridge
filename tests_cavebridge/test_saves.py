# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
import pytest
from cavebridge.saves import SaveStore


def test_roundtrip(tmp_path):
    live = tmp_path / "session.adv"
    live.write_bytes(b"A")
    store = SaveStore(str(tmp_path / "slots"))
    store.save("cp", str(live))
    assert "cp" in store.list()
    live.write_bytes(b"B")
    store.load("cp", str(live))
    assert live.read_bytes() == b"A"


def test_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        SaveStore(str(tmp_path / "s")).load("nope", str(tmp_path / "x.adv"))
