# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
import os
import pytest
from cavebridge.engine import Engine

ADVENT = os.path.abspath("./advent")
pytestmark = pytest.mark.skipif(
    not os.path.exists(ADVENT),
    reason="build advent with `make CFLAGS=-DADVENT_AUTOSAVE` first",
)

NOBJECTS = 69   # from dungeon.h; synthetic fixed-object ids are id+NOBJECTS


def _fresh(tmp_path, name="s.adv"):
    p = str(tmp_path / name)
    if os.path.exists(p):
        os.remove(p)
    e = Engine(ADVENT, seed=1, autosave_path=p)
    e.start(fresh=True)
    return e, p


def test_take_lamp_updates_inventory_no_extra_turns(tmp_path):
    e, _ = _fresh(tmp_path)
    e.step("in")
    t = e.step("take lamp")
    assert t.kind == "normal"
    assert any(o.name == "lamp" for o in t.state.inventory)
    assert t.state.turns == 2          # seed + @state cost no net turn
    e.close()


def test_fixed_object_grate_normalized_id(tmp_path):
    # In the chamber BELOW the grate, the grate's SECONDARY placement has the
    # synthetic atloc id GRATE+NOBJECTS (=72). If emit_state_json failed to
    # normalize, it would surface as id 72; correct code shows the real id<=69.
    # Verified path (lit chamber) against the real binary:
    e, _ = _fresh(tmp_path)
    for mv in ("in", "take keys", "take lamp", "lamp on", "out",
               "down", "down", "south", "unlock grate", "down"):
        e.step(mv)
    vis = e.state().visible
    assert any("grate" in o.name.lower() for o in vis), \
        "expected the grate visible in the chamber below the grate"
    assert all(o.id <= NOBJECTS for o in vis)   # synthetic id 72 -> normalized
    e.close()


def test_quit_yields_ended_turn_not_crash(tmp_path):
    e, _ = _fresh(tmp_path)
    e.step("in")
    t = e.close()                      # returns an 'ended' Turn, no exception
    assert t is not None and t.kind == "ended"


def test_save_file_then_resume_restores_state(tmp_path):
    import shutil
    e, live = _fresh(tmp_path)
    e.step("in")
    e.step("take lamp")
    e.close()                          # per-turn autosave persisted 'live'
    slot = str(tmp_path / "slot.adv")
    shutil.copyfile(live, slot)
    shutil.copyfile(slot, live)        # simulate /load: slot -> live
    e2 = Engine(ADVENT, seed=1, autosave_path=live)
    e2.start(fresh=False)              # resume: no reseed
    assert any(o.name == "lamp" for o in e2.state().inventory)
    e2.close()
