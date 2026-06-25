# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
from cavebridge.state import GameState, ObjectRef, parse_state_json

SAMPLE = (
    'x @@ADVSTATE_BEGIN@@{"turns":3,"loc":3,"loc_name":"inside\\nbuilding",'
    '"dark":false,"lamp":{"on":true,"fuel":330},'
    '"flags":{"closed":false,"closng":false,"dflag":0},'
    '"visible":[{"id":2,"name":"lamp","prop":1}],'
    '"inventory":[{"id":1,"name":"keys","prop":0}]}@@ADVSTATE_END@@ y'
)


def test_parse_fields_and_types():
    st = parse_state_json(SAMPLE)
    assert (st.turns, st.loc, st.dark) == (3, 3, False)
    assert st.loc_name == "inside\nbuilding"
    assert st.lamp_on is True and st.fuel == 330
    assert st.inventory[0] == ObjectRef(1, "keys", 0)


def test_signature_reacts_to_prop_and_dark():
    a = parse_state_json(SAMPLE)
    b = parse_state_json(SAMPLE.replace('"prop":1', '"prop":9'))
    assert a.signature() != b.signature()


def test_missing_block_raises():
    import pytest
    with pytest.raises(ValueError):
        parse_state_json("nope")
