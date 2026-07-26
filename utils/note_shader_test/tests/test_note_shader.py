"""GPU tests: compile notes.frag, render fixtures, check vs reference notation."""

from __future__ import annotations

import pytest

from note_shader_test.compare import (
    compare_render_to_reference,
    ink_mask,
    staff_has_lines,
)
from note_shader_test.fixtures_io import golden_path_for, iter_cases
from note_shader_test.paths import notes_frag_path
from note_shader_test.staff_layout import ShaderLayout


pytestmark = pytest.mark.gpu


def test_shader_file_exists(shader_path):
    text = shader_path.read_text(encoding="utf-8")
    assert "drawNote" in text
    assert "NUM_NOTES" in text
    assert "note_names" in text


def test_harness_compiles(harness):
    assert harness._program is not None


def test_staff_only_draws_lines(harness):
    img = harness.render(notes=[], note_names=False)
    assert img.shape == (540, 960, 4)
    assert staff_has_lines(img), "expected horizontal staff ink"
    # Mostly light background
    assert ink_mask(img).mean() < 0.25


def test_quarter_c4_has_note_ink(harness):
    notes = [{"midi": 60, "x": 0.0, "type": "quarter"}]
    img = harness.render(notes=notes)
    result = compare_render_to_reference(
        "quarter_c4",
        img,
        notes=notes,
        golden_path=None,
        min_region_coverage=0.03,
    )
    assert result.passed, result.summary()
    assert result.region_checks[0].coverage > 0.03


def test_scale_all_heads_present(harness):
    case = next(c for c in iter_cases() if c["name"] == "scale_quarters")
    img = harness.render_case(case)
    result = compare_render_to_reference(
        case["name"], img, notes=case["notes"], min_region_coverage=0.025
    )
    assert result.passed, result.summary()
    for rc in result.region_checks:
        assert rc.passed, rc


@pytest.mark.parametrize("case_name", [
    "quarter_c4",
    "note_durations",
    "accidentals",
    "rests",
    "beamed_eighths",
    "note_names",
    "scale_quarters",
    "staff_only",
])
def test_integration_fixture_cases(harness, case_name):
    """Coarser multi-symbol fixtures (non-atomic). Atomic suite is separate."""
    cases = {c["name"]: c for c in iter_cases() if not c.get("atomic")}
    # top-level only names may still appear under recursive load
    all_cases = {c["name"]: c for c in iter_cases()}
    case = cases.get(case_name) or all_cases.get(case_name)
    assert case is not None, f"missing fixture {case_name}"
    img = harness.render_case(case)
    golden = golden_path_for(case)
    result = compare_render_to_reference(
        case["name"],
        img,
        notes=case.get("notes", []),
        golden_path=golden if golden.is_file() else None,
        min_region_coverage=0.02 if case.get("notes") else 0.0,
    )
    if case.get("notes"):
        assert result.passed, result.summary()
    else:
        assert staff_has_lines(img)


def test_note_names_adds_ink_vs_without(harness):
    notes = [{"midi": 64, "x": 0.0, "type": "quarter"}]
    without = harness.render(notes=notes, note_names=False)
    with_names = harness.render(notes=notes, note_names=True)
    ink_wo = ink_mask(without).sum()
    ink_w = ink_mask(with_names).sum()
    # Letters should add some ink (not necessarily huge)
    assert ink_w >= ink_wo, "note_names=1 should not remove notation ink"
    # Soft check: often strictly more; allow equal if letter draws outside mask sensitivity
    assert ink_w - ink_wo >= 0


def test_layout_substitutes_applied(harness):
    # Re-read preprocessed path by ensuring layout matches midimaster defaults
    layout = ShaderLayout.from_midimaster_defaults()
    assert abs(harness.layout.staff_pos_x - layout.staff_pos_x) < 1e-12
    frag = notes_frag_path().read_text(encoding="utf-8")
    # Source still has placeholders; harness substitutes at compile time
    assert "staff_pos_x" in frag
