"""Load / discover JSON notation fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from note_shader_test.paths import cases_dir, goldens_dir


def load_case(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("name", path.stem)
    data["_path"] = str(path)
    return data


def iter_cases(
    directory: Path | None = None,
    *,
    atomic_only: bool = False,
    group: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Load fixture JSON files (recursive under fixtures/cases/).

    Filters:
      atomic_only — cases with atomic: true (or name starting with atom_)
      group — exact match on case["group"]
      tags — case must include all listed tags
    """
    d = directory or cases_dir()
    paths = sorted(d.rglob("*.json"))
    cases = [load_case(p) for p in paths]

    if atomic_only:
        cases = [
            c
            for c in cases
            if c.get("atomic") is True or str(c.get("name", "")).startswith("atom_")
        ]
    if group is not None:
        cases = [c for c in cases if c.get("group") == group]
    if tags:
        want = set(tags)
        cases = [c for c in cases if want.issubset(set(c.get("tags") or []))]
    return cases


def golden_path_for(case: Dict[str, Any]) -> Path:
    name = case.get("golden", case.get("name", "case"))
    if not str(name).endswith(".png"):
        name = f"{name}.png"
    return goldens_dir() / name
