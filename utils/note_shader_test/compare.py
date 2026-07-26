"""Image and region-based comparison of rendered notation vs references."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from note_shader_test.staff_layout import note_head_pixel_region, rest_glyph_pixel_region


@dataclass
class RegionCheck:
    name: str
    passed: bool
    coverage: float
    min_coverage: float
    box: Tuple[int, int, int, int]
    message: str = ""


@dataclass
class CompareResult:
    name: str
    passed: bool
    mean_abs_diff: float = 0.0
    max_abs_diff: float = 0.0
    pixel_fail_ratio: float = 0.0
    region_checks: List[RegionCheck] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    diff_image: Optional[np.ndarray] = None

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"[{status}] {self.name}"]
        if self.mean_abs_diff or self.pixel_fail_ratio:
            lines.append(
                f"  image: mean_abs={self.mean_abs_diff:.3f} "
                f"max_abs={self.max_abs_diff:.1f} "
                f"fail_ratio={self.pixel_fail_ratio:.4f}"
            )
        for r in self.region_checks:
            mark = "ok" if r.passed else "!!"
            lines.append(
                f"  region[{mark}] {r.name}: coverage={r.coverage:.3f} "
                f"(min {r.min_coverage:.3f}) box={r.box}"
            )
            if r.message:
                lines.append(f"           {r.message}")
        for m in self.messages:
            lines.append(f"  {m}")
        return "\n".join(lines)


def load_rgba(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGBA")
    return np.asarray(img, dtype=np.uint8)


def save_rgba(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image, mode="RGBA").save(path)


def ink_mask(image: np.ndarray, threshold: int = 240) -> np.ndarray:
    """
    Boolean mask of 'drawn ink' on a near-white background.

    Notation shader draws dark grey strokes; background is white when we clear to white.
    """
    rgb = image[..., :3].astype(np.int16)
    # Darker than near-white counts as ink
    return np.any(rgb < threshold, axis=-1)


def region_coverage(image: np.ndarray, box: Tuple[int, int, int, int], threshold: int = 240) -> float:
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return 0.0
    patch = image[y0:y1, x0:x1]
    mask = ink_mask(patch, threshold=threshold)
    return float(mask.mean()) if mask.size else 0.0


def compare_images(
    actual: np.ndarray,
    expected: np.ndarray,
    *,
    mean_abs_max: float = 12.0,
    pixel_fail_ratio_max: float = 0.02,
    per_channel_tol: float = 30.0,
) -> Tuple[bool, float, float, float, np.ndarray]:
    """
    Return (passed, mean_abs, max_abs, fail_ratio, diff_rgb_u8).

    Diff image: abs difference amplified for visual inspection.
    """
    if actual.shape != expected.shape:
        # Resize expected to actual for tolerant compare when regenerating sizes
        exp_img = Image.fromarray(expected, mode="RGBA").resize(
            (actual.shape[1], actual.shape[0]), Image.Resampling.BILINEAR
        )
        expected = np.asarray(exp_img, dtype=np.uint8)

    a = actual.astype(np.float32)
    e = expected.astype(np.float32)
    diff = np.abs(a - e)
    mean_abs = float(diff.mean())
    max_abs = float(diff.max())
    # Pixel fails if any RGB channel exceeds tol
    fail = np.any(diff[..., :3] > per_channel_tol, axis=-1)
    fail_ratio = float(fail.mean())

    vis = np.clip(diff[..., :3] * 4.0, 0, 255).astype(np.uint8)
    # highlight fail pixels in red-ish
    vis_img = np.zeros((*vis.shape[:2], 4), dtype=np.uint8)
    vis_img[..., :3] = vis
    vis_img[..., 3] = 255

    passed = mean_abs <= mean_abs_max and fail_ratio <= pixel_fail_ratio_max
    return passed, mean_abs, max_abs, fail_ratio, vis_img


def check_note_regions(
    image: np.ndarray,
    notes: Sequence[dict],
    *,
    min_coverage: float = 0.04,
    radius_px: int = 18,
) -> List[RegionCheck]:
    """Assert each pitched note has ink near its expected head position."""
    h, w = image.shape[:2]
    results: List[RegionCheck] = []
    for i, n in enumerate(notes):
        ntype = str(n.get("type", "quarter")).lower()
        if ntype.startswith("rest"):
            x = float(n.get("x", n.get("pos_x", 0.0)))
            # Rest glyphs are placed from staff_pos_y (not pitch); use drawRest centres
            box = rest_glyph_pixel_region(
                ntype, x, w, h, radius_px=max(radius_px + 6, 22)
            )
            cov = region_coverage(image, box)
            # Whole/half rests are small blocks; allow slightly lower coverage
            rest_min = min_coverage * (0.35 if "whole" in ntype or "half" in ntype else 0.5)
            ok = cov >= rest_min
            results.append(
                RegionCheck(
                    name=f"rest[{i}] {ntype}",
                    passed=ok,
                    coverage=cov,
                    min_coverage=rest_min,
                    box=box,
                    message="" if ok else "expected rest glyph ink at staff rest position",
                )
            )
            continue

        midi = n.get("midi", n.get("pitch"))
        if midi is None:
            results.append(
                RegionCheck(
                    name=f"note[{i}]",
                    passed=False,
                    coverage=0.0,
                    min_coverage=min_coverage,
                    box=(0, 0, 0, 0),
                    message="fixture note missing midi/pitch",
                )
            )
            continue

        x = float(n.get("x", n.get("pos_x", 0.0)))
        box = note_head_pixel_region(int(midi), x, w, h, radius_px=radius_px)
        cov = region_coverage(image, box)
        ok = cov >= min_coverage
        results.append(
            RegionCheck(
                name=f"note[{i}] midi={midi} {ntype}",
                passed=ok,
                coverage=cov,
                min_coverage=min_coverage,
                box=box,
                message="" if ok else "insufficient ink in expected note-head region",
            )
        )
    return results


def compare_render_to_reference(
    name: str,
    actual: np.ndarray,
    *,
    notes: Sequence[dict] | None = None,
    golden_path: Optional[Path] = None,
    require_golden: bool = False,
    min_region_coverage: float = 0.04,
) -> CompareResult:
    """
    Full comparison: optional golden image + structural note-region checks.
    """
    messages: List[str] = []
    region_checks: List[RegionCheck] = []
    image_ok = True
    mean_abs = max_abs = fail_ratio = 0.0
    diff_img = None

    if notes:
        region_checks = check_note_regions(actual, notes, min_coverage=min_region_coverage)
        if not any(r.passed for r in region_checks) and region_checks:
            messages.append("no note regions passed coverage check")

    if golden_path is not None and golden_path.is_file():
        expected = load_rgba(golden_path)
        image_ok, mean_abs, max_abs, fail_ratio, diff_img = compare_images(actual, expected)
        if not image_ok:
            messages.append(f"golden mismatch: {golden_path.name}")
    elif require_golden:
        image_ok = False
        messages.append(f"missing golden image: {golden_path}")
    else:
        messages.append("no golden image (region checks only)")

    regions_ok = all(r.passed for r in region_checks) if region_checks else True
    # If we have goldens, image compare is authoritative; regions are diagnostic
    if golden_path is not None and golden_path.is_file():
        passed = image_ok
    else:
        passed = regions_ok

    return CompareResult(
        name=name,
        passed=passed,
        mean_abs_diff=mean_abs,
        max_abs_diff=max_abs,
        pixel_fail_ratio=fail_ratio,
        region_checks=region_checks,
        messages=messages,
        diff_image=diff_img,
    )


def staff_has_lines(image: np.ndarray, min_horizontal_ink_rows: int = 3) -> bool:
    """Quick sanity: staff draws several horizontal dark bands."""
    mask = ink_mask(image)
    # Count rows with substantial horizontal ink (staff lines span width)
    row_frac = mask.mean(axis=1)
    return int(np.sum(row_frac > 0.05)) >= min_horizontal_ink_rows
