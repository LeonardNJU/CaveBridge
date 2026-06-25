# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.guide import guide


def test_guide_languages_and_content():
    zh = guide("zh")
    en = guide("en")
    assert "玩法说明" in zh and "自动存档" in zh and "/save" in zh
    assert "How to Play" in en and "Autosave" in en and "/save" in en
    assert zh != en
