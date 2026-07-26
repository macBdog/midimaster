"""CPU-only tests for staff geometry (no GPU)."""

from note_shader_test.staff_layout import (
    NOTE_TYPE,
    ORIGIN_NOTE,
    ShaderLayout,
    compute_note_positions,
    empty_uniform_buffers,
    pack_notes,
)


def test_c4_in_playable_range():
    pos = compute_note_positions()
    assert 60 in pos
    assert ORIGIN_NOTE in pos
    # Higher MIDI notes should be higher on the staff (greater Y)
    assert pos[72] > pos[60]
    assert pos[60] > pos[48]


def test_white_keys_step_evenly():
    pos = compute_note_positions()
    # C4=60, D4=62, E4=64 are consecutive white keys → equal spacing
    step_cd = pos[62] - pos[60]
    step_de = pos[64] - pos[62]
    assert abs(step_cd - step_de) < 1e-9


def test_shader_layout_matches_note_render_formulas():
    layout = ShaderLayout.from_midimaster_defaults()
    # Staff.Pos x = -0.85 → staff_pos_x = 0.5 + (-0.85)*0.5 = 0.075
    assert abs(layout.staff_pos_x - 0.075) < 1e-9
    assert abs(layout.staff_pos_y - 0.5) < 1e-9
    assert abs(layout.staff_width - 0.925) < 1e-9
    assert abs(layout.staff_note_spacing - 0.0275) < 1e-9
    subs = layout.substitutes()
    assert subs["NUM_NOTES"] == 32
    assert "staff_pos_x 0.075" in subs["#define staff_pos_x 0.0"]


def test_pack_notes_sets_slot_zero():
    buf = pack_notes([{"midi": 60, "x": 0.25, "type": "quarter", "decoration": "sharp"}])
    assert buf["types"][0] == NOTE_TYPE["quarter"]
    assert buf["decoration"][0] == 3  # sharp
    assert abs(buf["positions"][0] - 0.25) < 1e-9
    assert buf["colours"][3] == 1.0  # alpha
    # remaining slots empty type
    assert buf["types"][1] == 0


def test_empty_buffers_size():
    buf = empty_uniform_buffers(32)
    assert len(buf["positions"]) == 64
    assert len(buf["colours"]) == 128
    assert len(buf["types"]) == 32
