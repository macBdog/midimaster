"""
Staff geometry matching midimaster Staff / NoteRender.

Kept independent of gamejam/GUI so the harness can compute note Y positions
and shader preprocessor substitutes without launching the game.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# Mirrors staff.py / key_signature.py constants
STAFF_WIDTH = 1.85
STAFF_POS = (-1.0 + (2.0 - STAFF_WIDTH), 0.0)  # (-0.85, 0.0)
NOTE_SPACING = 0.055
STAFF_SPACING = NOTE_SPACING * 2
ORIGIN_NOTE = 40  # E2
NUM_NOTES_RANGE = 48  # E2 .. G5-ish
NOTE_WIDTH_32ND = 0.025

# Black-key pitch classes (MIDI % 12)
SHARPS_AND_FLATS = {1, 3, 6, 8, 10}

NUM_NOTES_SLOTS = 32  # NoteRender.NumNotes
NUM_KEY_SIG = 14


@dataclass(frozen=True)
class ShaderLayout:
    """Values injected into notes.frag via the same substitutions as NoteRender."""

    num_notes: int = NUM_NOTES_SLOTS
    num_key_sig: int = NUM_KEY_SIG
    staff_pos_x: float = 0.0
    staff_pos_y: float = 0.5
    staff_width: float = 1.0
    staff_note_spacing: float = 0.03

    @classmethod
    def from_midimaster_defaults(cls) -> "ShaderLayout":
        # Same formulas as note_render.py shader_substitutes
        return cls(
            num_notes=NUM_NOTES_SLOTS,
            num_key_sig=NUM_KEY_SIG,
            staff_pos_x=0.5 + STAFF_POS[0] * 0.5,
            staff_pos_y=0.5 + STAFF_POS[1] * 0.5,
            staff_width=STAFF_WIDTH * 0.5,
            staff_note_spacing=NOTE_SPACING * 0.5,
        )

    def substitutes(self) -> dict:
        # Format floats compactly so shader source stays readable and tests are stable
        def f(v: float) -> str:
            return f"{v:.6g}"

        return {
            "NUM_NOTES": self.num_notes,
            "NUM_KEY_SIG": self.num_key_sig,
            "#define staff_pos_x 0.0": f"#define staff_pos_x {f(self.staff_pos_x)}",
            "#define staff_pos_y 0.5": f"#define staff_pos_y {f(self.staff_pos_y)}",
            "#define staff_width 1.0": f"#define staff_width {f(self.staff_width)}",
            "#define staff_note_spacing 0.03": f"#define staff_note_spacing {f(self.staff_note_spacing)}",
        }


def compute_note_positions() -> Dict[int, float]:
    """
    Absolute NDC-Y positions keyed by MIDI note id.

    Replicates Staff.prepare() tone_count walk without GUI widgets.
    White keys step the staff; black keys share vertical slots between whites.
    """
    note_positions: Dict[int, float] = {}
    tone_count = 0
    note_start_y = STAFF_POS[1] - NOTE_SPACING * (12 + 2)

    for i in range(NUM_NOTES_RANGE):
        note = ORIGIN_NOTE + i
        note_lookup = note % 12
        black_key = note_lookup in SHARPS_AND_FLATS
        note_pos = note_start_y + (tone_count * NOTE_SPACING)
        note_positions[note] = note_pos
        if not black_key:
            tone_count += 1

    return note_positions


def midi_to_staff_uv_y(midi_note: int, layout: ShaderLayout | None = None) -> float:
    """Map MIDI note → shader UV-space Y used by notes.frag (after (ndc+1)*0.5)."""
    layout = layout or ShaderLayout.from_midimaster_defaults()
    positions = compute_note_positions()
    if midi_note not in positions:
        raise KeyError(f"MIDI note {midi_note} outside playable range {ORIGIN_NOTE}..{ORIGIN_NOTE + NUM_NOTES_RANGE - 1}")
    ndc_y = positions[midi_note]
    return (ndc_y + 1.0) * 0.5


def _uv_to_pixel_box(
    uv_x: float,
    uv_y: float,
    width: int,
    height: int,
    radius_px: int,
) -> Tuple[int, int, int, int]:
    """Shader UV (origin bottom-left after main() flip) → image pixel AABB."""
    img_x = int(round(uv_x * (width - 1)))
    img_y = int(round((1.0 - uv_y) * (height - 1)))
    x0 = max(0, img_x - radius_px)
    y0 = max(0, img_y - radius_px)
    x1 = min(width, img_x + radius_px)
    y1 = min(height, img_y + radius_px)
    return x0, y0, x1, y1


def note_head_pixel_region(
    midi_note: int,
    ndc_x: float,
    width: int,
    height: int,
    radius_px: int = 18,
) -> Tuple[int, int, int, int]:
    """
    Axis-aligned pixel box (x0,y0,x1,y1) around the expected note head centre.

    Shader: note_pos = (NotePositions + 1) * 0.5 in UV; main() flips V so
    image row 0 is top of screen while UV y increases upward in draw space.
    """
    positions = compute_note_positions()
    ndc_y = positions[midi_note]
    u = (ndc_x + 1.0) * 0.5
    v = (ndc_y + 1.0) * 0.5
    return _uv_to_pixel_box(u, v, width, height, radius_px)


def rest_glyph_uv_y(rest_type: str, layout: ShaderLayout | None = None) -> float:
    """
    Approximate centre Y in shader UV for a rest glyph.

    Mirrors notes.frag drawRest() placement (uses staff_pos_*, not note pitch).
    """
    layout = layout or ShaderLayout.from_midimaster_defaults()
    sp = layout.staff_pos_y
    sn = layout.staff_note_spacing
    t = rest_type.lower()
    if not t.startswith("rest_"):
        t = f"rest_{t}"
    if t == "rest_whole":
        return sp + sn * 5.0 + 0.012
    if t == "rest_half":
        return sp + sn * 4.0 + 0.015
    if t == "rest_quarter":
        return sp + 0.13
    # eighth / sixteenth / thirtysecond share one glyph cluster
    return sp + 0.115


def rest_glyph_pixel_region(
    rest_type: str,
    ndc_x: float,
    width: int,
    height: int,
    radius_px: int = 22,
    layout: ShaderLayout | None = None,
) -> Tuple[int, int, int, int]:
    """Pixel box around expected rest ink (horizontal from note slot X)."""
    u = (ndc_x + 1.0) * 0.5
    v = rest_glyph_uv_y(rest_type, layout)
    return _uv_to_pixel_box(u, v, width, height, radius_px)


# Note type / decoration enums matching note.py and notes.frag
NOTE_TYPE = {
    "none": 0,
    "whole": 1,
    "half": 2,
    "quarter": 3,
    "eighth": 4,
    "sixteenth": 5,
    "thirtysecond": 6,
    "rest_whole": 7,
    "rest_half": 8,
    "rest_quarter": 9,
    "rest_eighth": 10,
    "rest_sixteenth": 11,
    "rest_thirtysecond": 12,
}

NOTE_DECORATION = {
    "none": 0,
    "flat": 1,
    "natural": 2,
    "sharp": 3,
    "dotted": 4,
    "dotted_flat": 5,
    "dotted_natural": 6,
    "dotted_sharp": 7,
}


def empty_uniform_buffers(num_notes: int = NUM_NOTES_SLOTS) -> dict:
    """Zeroed GPU uniform arrays matching NoteRender.reset() layout."""
    return {
        "positions": [0.0] * (num_notes * 2),
        "colours": [0.0] * (num_notes * 4),
        "types": [0] * num_notes,
        "decoration": [0] * num_notes,
        "hats": [0.0] * (num_notes * 2),
        "ties": [0.0] * num_notes,
        "extra": [0.0] * (num_notes * 2),
        "key_positions": [0.0] * (NUM_KEY_SIG * 2),
    }


def pack_notes(notes: List[dict], num_notes: int = NUM_NOTES_SLOTS) -> dict:
    """
    Build uniform arrays from a list of note dicts.

    Each note dict may include:
      midi / pitch: int (MIDI number) — used for Y if pos_y not set
      x / pos_x: float NDC x (default 0.0)
      y / pos_y: float NDC y (optional override)
      type: str or int
      decoration: str or int
      colour: [r,g,b,a] (default dark grey opaque)
      hat: [length, y_delta]
      tie: float
      extra: [force_stem, stalk_extra]
    """
    buf = empty_uniform_buffers(num_notes)
    positions = compute_note_positions()

    for i, n in enumerate(notes[:num_notes]):
        midi = n.get("midi", n.get("pitch"))
        x = float(n.get("x", n.get("pos_x", 0.0)))
        if "y" in n or "pos_y" in n:
            y = float(n.get("y", n.get("pos_y")))
        elif midi is not None:
            y = float(positions[int(midi)])
        else:
            y = 0.0

        ntype = n.get("type", "quarter")
        if isinstance(ntype, str):
            ntype = NOTE_TYPE[ntype.lower()]
        dec = n.get("decoration", "none")
        if isinstance(dec, str):
            dec = NOTE_DECORATION[dec.lower()]

        col = n.get("colour", [0.11, 0.11, 0.11, 1.0])
        hat = n.get("hat", [0.0, 0.0])
        tie = float(n.get("tie", 0.0))
        extra = n.get("extra", [0.0, 0.0])

        npos = i * 2
        cpos = i * 4
        buf["positions"][npos] = x
        buf["positions"][npos + 1] = y
        buf["colours"][cpos : cpos + 4] = list(col)
        buf["types"][i] = int(ntype)
        buf["decoration"][i] = int(dec)
        buf["hats"][npos] = float(hat[0])
        buf["hats"][npos + 1] = float(hat[1])
        buf["ties"][i] = tie
        buf["extra"][npos] = float(extra[0])
        buf["extra"][npos + 1] = float(extra[1])

    return buf
