from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import pandas as pd

from core.schema.project import ProjectSpec


@dataclass
class QueryContext:
    # Future: real filter wiring (date range, channel, state, etc.)
    days: int = 45
    breakdown_limit: int = 20


class DataProvider:
    def kpi(self, project: ProjectSpec, metric_name: str, ctx: QueryContext) -> float:
        raise NotImplementedError

    def trend(self, project: ProjectSpec, metric_name: str, ctx: QueryContext) -> pd.DataFrame:
        raise NotImplementedError

    def breakdown(self, project: ProjectSpec, metric_name: str, dim: str, ctx: QueryContext) -> pd.DataFrame:
        raise NotImplementedError


class MockProvider(DataProvider):
    """
    Mock provider that is deterministic-ish per metric_name across a session.
    """
    def _rng(self, key: str) -> random.Random:
        seed = abs(hash(key)) % (2**32)
        return random.Random(seed)

    def kpi(self, project: ProjectSpec, metric_name: str, ctx: QueryContext) -> float:
        m = next((x for x in project.metrics if x.name == metric_name), None)
        r = self._rng(f"kpi:{metric_name}")
        if m and m.format == "percent":
            return r.uniform(0.2, 0.9)
        return r.uniform(100, 10000)

    def trend(self, project: ProjectSpec, metric_name: str, ctx: QueryContext) -> pd.DataFrame:
        r = self._rng(f"trend:{metric_name}")
        start = date.today() - timedelta(days=ctx.days)
        v = r.uniform(50, 150)
        rows = []
        for i in range(ctx.days):
            # smooth-ish random walk
            v = max(0, v + r.uniform(-8, 8))
            rows.append({"date": start + timedelta(days=i), "value": v})
        return pd.DataFrame(rows)

    def breakdown(self, project: ProjectSpec, metric_name: str, dim: str, ctx: QueryContext) -> pd.DataFrame:
        r = self._rng(f"breakdown:{metric_name}:{dim}")
        n = min(ctx.breakdown_limit, 10)
        labels = [f"{dim}_{i+1}" for i in range(n)]
        values = [r.uniform(10, 100) for _ in labels]
        return pd.DataFrame({"dim": labels, "value": values}).sort_values("value", ascending=False)
