"""
Atomic GPU tests: each rest type, note duration, and mixed sequence is its own case.

A failure names the exact fixture (atom_*) so you can re-render and fix that
glyph/sequence in isolation without noise from unrelated notation.
"""

from __future__ import annotations

import pytest

from note_shader_test.atomic_catalog import atomic_case_names, build_catalog, cases_by_group
from note_shader_test.compare import compare_render_to_reference, save_rgba
from note_shader_test.fixtures_io import golden_path_for, iter_cases
from note_shader_test.paths import output_dir


pytestmark = pytest.mark.gpu

# Region coverage floor for atomic cases (single glyphs / short sequences)
_MIN_COVERAGE = 0.025


def _cases_from_disk_or_catalog():
    """Prefer written JSON fixtures; fall back to in-memory catalog."""
    disk = {c["name"]: c for c in iter_cases(atomic_only=True)}
    if disk:
        return disk
    return {c["name"]: c for c in build_catalog()}


@pytest.fixture(scope="module")
def atomic_map():
    return _cases_from_disk_or_catalog()


def test_atomic_catalog_nonempty():
    names = atomic_case_names()
    assert len(names) >= 40
    assert len(names) == len(set(names))


def test_atomic_groups_cover_rests_and_durations():
    groups = cases_by_group()
    for required in (
        "rest_solo",
        "note_solo",
        "seq_note_rest_same",
        "seq_rest_note_same",
        "seq_note_rest_cross",
        "seq_rest_note_cross",
        "seq_note_note_cross",
    ):
        assert required in groups, f"missing group {required}"
        assert len(groups[required]) >= 1


def test_atomic_fixtures_on_disk(atomic_map):
    """JSON files under fixtures/cases/atomic/ match the catalog (after write)."""
    catalog_names = set(atomic_case_names())
    # If fixtures were written, every catalog case should exist
    disk_atomic = iter_cases(atomic_only=True)
    if not disk_atomic:
        pytest.skip("atomic fixtures not written yet — run: python -m note_shader_test.atomic_catalog write")
    disk_names = {c["name"] for c in disk_atomic}
    missing = catalog_names - disk_names
    assert not missing, f"catalog cases missing on disk: {sorted(missing)[:10]}..."


@pytest.mark.parametrize("case_name", atomic_case_names())
def test_atomic_case(harness, atomic_map, case_name):
    """
    One assertion chain per atomic fixture.

    Failures are independent: re-run with
      pytest -k atom_seq_note_quarter_rest_eighth
    or
      python -m note_shader_test render atom_seq_note_quarter_rest_eighth -o out.png
    """
    assert case_name in atomic_map, f"fixture not loaded: {case_name}"
    case = atomic_map[case_name]
    notes = case.get("notes") or []
    assert notes, f"{case_name} has no notes"

    img = harness.render_case(case)
    golden = golden_path_for(case)
    result = compare_render_to_reference(
        case_name,
        img,
        notes=notes,
        golden_path=golden if golden.is_file() else None,
        min_region_coverage=_MIN_COVERAGE,
    )

    if not result.passed:
        # Write actual + optional diff for this case only
        out = output_dir()
        save_rgba(out / f"{case_name}_actual.png", img)
        if result.diff_image is not None:
            save_rgba(out / f"{case_name}_diff.png", result.diff_image)

    assert result.passed, result.summary()
    for rc in result.region_checks:
        assert rc.passed, f"{case_name}: {rc}"


# Filter examples (no extra runs — use -k against case names / groups in ids):
#   pytest -k atom_rest_only
#   pytest -k atom_seq_note_quarter_rest
#   pytest -k stem_up
