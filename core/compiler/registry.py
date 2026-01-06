from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.schema.project import ProjectSpec


@dataclass(frozen=True)
class RegistryMetric:
    name: str
    semantic_key: str
    definition_hash: str
    definition: Dict[str, Any]

    # metadata (not part of hash)
    format: Optional[str]
    owner: Optional[str]
    tags: List[str]
    aliases: List[str]


def build_registry(project: ProjectSpec) -> Dict[str, Any]:
    """
    Create a registry artifact suitable for:
    - diffing in PRs
    - publishing internally as a single source of truth

    Determinism:
    - metrics sorted by semantic_key then name
    - definition_hash derived from canonical_definition
    """
    metrics: List[RegistryMetric] = []
    for m in project.metrics:
        metrics.append(
            RegistryMetric(
                name=m.name,
                semantic_key=m.semantic_key,
                definition_hash=m.definition_hash(),
                definition=m.canonical_definition(),
                format=m.format,
                owner=m.owner,
                tags=sorted(list(m.tags)),
                aliases=sorted(list(m.aliases)),
            )
        )

    metrics_sorted = sorted(metrics, key=lambda x: (x.semantic_key, x.name))

    artifact = {
        "schema": "symantica.registry.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": project.dataset.name,
            "table": project.dataset.table,
            "time_column": project.dataset.time_column,
            "default_grain": project.dataset.default_grain,
        },
        "metrics": [asdict(m) for m in metrics_sorted],
    }
    return artifact


def write_registry(registry: Dict[str, Any], out_path: str | Path) -> Path:
    import json

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p
