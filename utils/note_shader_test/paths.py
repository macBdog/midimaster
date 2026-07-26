"""Resolve midimaster / gamejam roots (utils lives inside the midimaster repo)."""

from __future__ import annotations

import os
from pathlib import Path

# utils/note_shader_test/paths.py → utils/ → midimaster root
_PACKAGE_DIR = Path(__file__).resolve().parent
UTILS_ROOT = _PACKAGE_DIR.parent
MIDIMASTER_ROOT = UTILS_ROOT.parent


def midimaster_root() -> Path:
    env = os.environ.get("MIDIMASTER_ROOT")
    if env:
        return Path(env).resolve()
    return MIDIMASTER_ROOT


def gamejam_root() -> Path:
    env = os.environ.get("GAMEJAM_ROOT")
    if env:
        return Path(env).resolve()
    # Sibling checkout next to midimaster (common local layout)
    return (midimaster_root().parent / "gamejam").resolve()


def notes_frag_path() -> Path:
    return midimaster_root() / "ext" / "shaders" / "notes.frag"


def texture_vert_path() -> Path:
    """Prefer gamejam's texture.vert; fall back to bundled copy."""
    gj = gamejam_root() / "gamejam" / "shaders" / "texture.vert"
    if gj.is_file():
        return gj
    bundled = _PACKAGE_DIR / "shaders" / "texture.vert"
    return bundled


def fixtures_dir() -> Path:
    return _PACKAGE_DIR / "fixtures"


def cases_dir() -> Path:
    return fixtures_dir() / "cases"


def goldens_dir() -> Path:
    return fixtures_dir() / "goldens"


def output_dir() -> Path:
    d = UTILS_ROOT / "output" / "note_shader_test"
    d.mkdir(parents=True, exist_ok=True)
    return d
