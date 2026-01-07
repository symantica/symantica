from __future__ import annotations

from typing import Dict, Optional

from core.schema.project import ProjectSpec
from core.schema.metric import MetricSpec


_GRAIN_TO_BQ = {"day": "DAY", "week": "WEEK", "month": "MONTH"}


def _bq_ident(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("`") and s.endswith("`"):
        return s
    return f"`{s}`"


def _metric_map(project: ProjectSpec) -> Dict[str, MetricSpec]:
    return {m.name: m for m in project.metrics}


def _get_model(project: ProjectSpec, model_name: Optional[str]):
    name = (model_name or "").strip() or project.dataset.name
    for m in project.models:
        if m.name == name:
            return m
    raise ValueError(f"Unknown model '{name}'.")


def _field_sql(project: ProjectSpec, metric: MetricSpec, ref: str) -> str:
    model = _get_model(project, metric.model)
    ref = (ref or "").strip()
    if ref.startswith("dimensions."):
        key = ref.split(".", 1)[1]
        return _bq_ident(model.dimensions[key].column)
    if ref.startswith("measures."):
        key = ref.split(".", 1)[1]
        return _bq_ident(model.measures[key].column)
    return _bq_ident(ref)


def _agg_expr(project: ProjectSpec, metric: MetricSpec) -> str:
    t = metric.type
    if t == "count":
        return f"COUNT({_field_sql(project, metric, metric.expr or '')})"
    if t == "distinct_count":
        return f"COUNT(DISTINCT {_field_sql(project, metric, metric.expr or '')})"
    if t == "sum":
        return f"SUM({_field_sql(project, metric, metric.expr or '')})"
    if t == "avg":
        return f"AVG({_field_sql(project, metric, metric.expr or '')})"
    if t == "ratio":
        mm = _metric_map(project)
        num = mm[metric.numerator]
        den = mm[metric.denominator]
        return f"SAFE_DIVIDE({_agg_expr(project, num)}, NULLIF({_agg_expr(project, den)}, 0))"
    raise ValueError(f"Unsupported metric type '{t}'.")


def _where_days(project: ProjectSpec, days: int) -> str:
    time_col = _bq_ident(project.dataset.time_column)
    return f"DATE({time_col}) >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)"


def compile_kpi_sql(project: ProjectSpec, metric_name: str, *, days: int) -> str:
    metric = _metric_map(project)[metric_name]
    model = _get_model(project, metric.model)
    return (
        "SELECT\n"
        f"  {_agg_expr(project, metric)} AS value\n"
        f"FROM {_bq_ident(model.primary_table)}\n"
        f"WHERE {_where_days(project, days)}\n"
    )


def compile_trend_sql(project: ProjectSpec, metric_name: str, *, days: int) -> str:
    metric = _metric_map(project)[metric_name]
    model = _get_model(project, metric.model)

    grain = (project.dataset.default_grain or "day").lower()
    bq_grain = _GRAIN_TO_BQ.get(grain, "DAY")

    time_col = _bq_ident(project.dataset.time_column)
    bucket = f"DATE_TRUNC(DATE({time_col}), {bq_grain})"

    return (
        "SELECT\n"
        f"  {bucket} AS date,\n"
        f"  {_agg_expr(project, metric)} AS value\n"
        f"FROM {_bq_ident(model.primary_table)}\n"
        f"WHERE {_where_days(project, days)}\n"
        "GROUP BY date\n"
        "ORDER BY date\n"
    )


def compile_breakdown_sql(
    project: ProjectSpec,
    metric_name: str,
    dim: str,
    *,
    days: int,
    limit: int = 20,
) -> str:
    metric = _metric_map(project)[metric_name]
    model = _get_model(project, metric.model)

    dim_col = _bq_ident(model.dimensions[dim].column)

    return (
        "SELECT\n"
        f"  {dim_col} AS dim,\n"
        f"  {_agg_expr(project, metric)} AS value\n"
        f"FROM {_bq_ident(model.primary_table)}\n"
        f"WHERE {_where_days(project, days)}\n"
        "GROUP BY dim\n"
        "ORDER BY value DESC\n"
        f"LIMIT {int(limit)}\n"
    )
