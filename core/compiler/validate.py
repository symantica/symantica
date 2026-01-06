from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from core.schema.project import ProjectSpec


@dataclass
class ValidationIssue:
    level: str  # "ERROR" | "WARN"
    message: str


def _parse_field_ref(expr: str) -> Optional[Tuple[str, str]]:
    """
    MVP parser for expressions like:
      - dimensions.channel
      - measures.is_approved

    Returns (namespace, field_name) or None if not a field-ref.
    """
    if not expr:
        return None
    e = expr.strip()
    if e.startswith("dimensions."):
        return ("dimensions", e.split("dimensions.", 1)[1].strip())
    if e.startswith("measures."):
        return ("measures", e.split("measures.", 1)[1].strip())
    return None


def validate_project(project: ProjectSpec) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    # --- Build lookup maps ---
    metrics_by_name = {m.name: m for m in project.metrics}

    # Aliases map: alias -> canonical metric name
    alias_to_name: Dict[str, str] = {}
    for m in project.metrics:
        for a in m.aliases:
            a = (a or "").strip()
            if not a:
                continue
            # alias shouldn't collide with a real metric name
            if a in metrics_by_name:
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        message=f"Alias '{a}' on metric '{m.name}' conflicts with an existing metric name.",
                    )
                )
            # alias shouldn't be duplicated
            if a in alias_to_name and alias_to_name[a] != m.name:
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        message=f"Alias '{a}' is defined for multiple metrics: '{alias_to_name[a]}' and '{m.name}'.",
                    )
                )
            else:
                alias_to_name[a] = m.name

    def resolve_metric_name(name_or_alias: str) -> Optional[str]:
        if name_or_alias in metrics_by_name:
            return name_or_alias
        if name_or_alias in alias_to_name:
            return alias_to_name[name_or_alias]
        return None

    # Models map
    models_by_name = {m.name: m for m in project.models}

    # If no models provided, we cannot validate field refs
    if not project.models:
        issues.append(
            ValidationIssue(
                level="WARN",
                message=(
                    "No models defined. Field reference validation is skipped.\n"
                    "Add a 'models:' section with dimensions/measures to validate expr like 'dimensions.x'."
                ),
            )
        )

    # --- Rule 1: unique metric names ---
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

    # --- Rule 2: semantic_key conflicts ---
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

    # --- Rule 3: warn on duplicate definitions ---
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

    # --- New: Rule 4: dependency validation ---
    for m in project.metrics:
        if m.type == "ratio":
            if not m.numerator or not m.denominator:
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        message=f"Metric '{m.name}' is type=ratio but is missing numerator/denominator.",
                    )
                )
            else:
                num = resolve_metric_name(m.numerator)
                den = resolve_metric_name(m.denominator)
                if not num:
                    issues.append(
                        ValidationIssue(
                            level="ERROR",
                            message=f"Metric '{m.name}' references numerator '{m.numerator}' which is not defined (including aliases).",
                        )
                    )
                if not den:
                    issues.append(
                        ValidationIssue(
                            level="ERROR",
                            message=f"Metric '{m.name}' references denominator '{m.denominator}' which is not defined (including aliases).",
                        )
                    )

        if m.type == "derived":
            for dep in m.depends_on:
                r = resolve_metric_name(dep)
                if not r:
                    issues.append(
                        ValidationIssue(
                            level="ERROR",
                            message=f"Derived metric '{m.name}' depends_on '{dep}' which is not defined (including aliases).",
                        )
                    )

    # --- New: Rule 5: field reference validation against models ---
    if project.models:
        default_model_name = project.models[0].name if project.models else None

        for m in project.metrics:
            # Only validate expr-based metrics
            if not m.expr:
                continue

            ref = _parse_field_ref(m.expr)
            if not ref:
                # raw SQL or unsupported expression
                issues.append(
                    ValidationIssue(
                        level="WARN",
                        message=(
                            f"Metric '{m.name}' uses expr '{m.expr}' which is not a simple field reference.\n"
                            "MVP supports 'dimensions.<field>' or 'measures.<field>' for strict validation."
                        ),
                    )
                )
                continue

            ns, field = ref
            model_name = m.model or default_model_name

            if not model_name or model_name not in models_by_name:
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        message=(
                            f"Metric '{m.name}' references {ns}.{field} but model '{model_name}' is not defined.\n"
                            "Add the model under 'models:' or set metric.model to a valid model name."
                        ),
                    )
                )
                continue

            model = models_by_name[model_name]
            if ns == "dimensions" and field not in model.dimensions:
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        message=(
                            f"Metric '{m.name}' references dimensions.{field} but it is not defined in model '{model_name}'.\n"
                            f"Defined dimensions: {sorted(list(model.dimensions.keys()))}"
                        ),
                    )
                )
            if ns == "measures" and field not in model.measures:
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        message=(
                            f"Metric '{m.name}' references measures.{field} but it is not defined in model '{model_name}'.\n"
                            f"Defined measures: {sorted(list(model.measures.keys()))}"
                        ),
                    )
                )

    return issues
