from __future__ import annotations

from pathlib import Path
import yaml

from core.schema.project import ProjectSpec


def load_project(path: str | Path) -> ProjectSpec:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Project file not found: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return ProjectSpec.model_validate(data)
