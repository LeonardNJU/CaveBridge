# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
"""Player-facing how-to-play guide for the CaveBridge front-end."""
from __future__ import annotations

GUIDE_ZH = """\
=== 巨洞冒险 · 玩法说明 ===

你在探索一个满是宝藏与危险的巨大洞穴。直接用大白话告诉我（你的 DM）想做什么，
我替你跟游戏打交道，并用中文讲给你听。

【怎么走】
- 方向：上、下、东、南、西、北（也认 in/out、ne/nw…）。
- 也能用地形词：进屋、出门、顺着小溪下游、钻进通道……
- 例："进那座小砖屋""往北走""下到洞里"。

【怎么互动】
- 拿 / 放 / 用 物品：拿灯、点灯、拿钥匙、开锁、放下棒子。
- 跟场景或生物互动：放鸟吓蛇、用斧子打矮人、喝水、吃东西。
- 观察：看看周围、查背包、有哪些出口、我现在在哪。

【目标】
- 深入洞穴找宝藏（金块、硬币、钻石……），带回起点的井房计分，满分 430。
- 小心黑暗（记得带灯并点亮！）、矮人、海盗和深坑。

【这个版本的便利功能】
- 自动存档：每回合自动存，进度不会丢；退出后下次启动会问你"继续 / 新开"。
- 存读档：/save 名字 存具名档，/load 名字 读回，/new 重开一局。
- 一句话多步："都拿了"（拿走眼前所有东西）、"放棒子，捉鸟"。
- 自动前进："一直下游走直到看见栅栏""一直往北走"——我替你连续走，遇到目标或危险就停。
- 提示：/hint 要一个提示；/hints on 开启卡住时的自动提示（不剧透，除非你开口）。
- 其它：/lang en|zh 切语言，/raw on|off 看/关原始指令与英文原文，/guide 再看本说明，
  /help 看命令，/quit 退出。

随时直接说话就行。祝你好运，冒险家！"""

GUIDE_EN = """\
=== Colossal Cave Adventure - How to Play ===

You're exploring a vast cave full of treasure and danger. Just tell me (your DM)
what you want to do in plain language; I deal with the game and narrate back.

[Moving]
- Directions: up, down, east, south, west, north (also in/out, ne/nw...).
- Terrain words work too: enter the building, go out, follow the stream
  downstream, crawl into the passage...
- e.g. "go into the brick house", "head north", "go down into the cave".

[Interacting]
- Take / drop / use items: take lamp, light it, take keys, unlock the grate, drop the rod.
- Act on the scene or creatures: release the bird to scare the snake, attack the
  dwarf with the axe, drink water, eat food.
- Observe: look around, check inventory, what are the exits, where am I.

[Goal]
- Go deep, find treasures (gold, coins, diamonds...) and carry them back to the
  well house to score. Max is 430. Beware darkness (bring & light the lamp!),
  dwarves, the pirate, and pits.

[This version's conveniences]
- Autosave every turn - progress is never lost; next launch asks resume vs new.
- Save slots: /save <name>, /load <name>, /new to restart.
- Multi-step in one line: "take everything", "drop the rod, catch the bird".
- Auto-advance: "keep going downstream until I see the grate", "keep heading north"
  - I take the steps for you and stop at the goal or on danger.
- Hints: /hint for one nudge; /hints on for auto-hints when stuck (never spoils
  unless you ask).
- Also: /lang en|zh, /raw on|off (show raw commands + engine text), /guide (this
  text again), /help, /quit.

Just talk to me whenever. Good luck, adventurer!"""


def guide(language: str) -> str:
    return GUIDE_ZH if language == "zh" else GUIDE_EN
