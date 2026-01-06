from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from core.schema.project import ProjectSpec


@dataclass
class ValidationIssue:
    level: str  # "ERROR" | "WARN"
    message: str


def validate_project(project: ProjectSpec) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    # Rule 1: unique metric names
    name_counts: Dict[str, int] = {}
    for m in project.metrics:
        name_counts[m.name] = name_counts.get(m.name, 0) + 1

    for name, count in name_counts.items():
        if count > 1:
            issues.append(
                ValidationIssue(
                    level="ERROR",
                    message=f"Duplicate metric name '{name}'. Metric names must be unique. Found {count} definitions.",
                )
            )

    # Rule 2: same semantic_key => same definition
    key_to_hash: Dict[str, str] = {}
    key_to_names: Dict[str, List[str]] = {}

    for m in project.metrics:
        h = m.definition_hash()
        key_to_names.setdefault(m.semantic_key, []).append(m.name)

        if m.semantic_key not in key_to_hash:
            key_to_hash[m.semantic_key] = h
        else:
            if key_to_hash[m.semantic_key] != h:
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        message=(
                            "Conflicting metric definitions for the same business concept.\n"
                            f"semantic_key: '{m.semantic_key}'\n"
                            f"metrics: {sorted(key_to_names[m.semantic_key])}\n"
                            "Fix by: (1) make the definitions identical, or (2) use a different semantic_key."
                        ),
                    )
                )

    # Rule 3: warn on duplicate definitions with different names
    hash_to_names: Dict[str, List[str]] = {}
    for m in project.metrics:
        hash_to_names.setdefault(m.definition_hash(), []).append(m.name)

    for h, names in hash_to_names.items():
        if len(names) > 1:
            issues.append(
                ValidationIssue(
                    level="WARN",
                    message=(
                        "Possible duplicate metrics: multiple metric names share the same definition.\n"
                        f"metrics: {sorted(names)}\n"
                        f"definition_hash: {h[:12]}…\n"
                        "Consider using one canonical metric name and listing others as aliases."
                    ),
                )
            )

    return issues
