from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional

from .dataset import DatasetSpec
from .model import ModelSpec
from .metric import MetricSpec
from .behavior import BehaviorSpec
from .dashboard import DashboardSpec


class ProjectSpec(BaseModel):
    dataset: DatasetSpec

    # MVP: allow 1+ models; metric.model chooses one. If omitted, we default later.
    models: List[ModelSpec] = Field(default_factory=list)

    metrics: List[MetricSpec] = Field(..., min_length=1)
    behaviors: BehaviorSpec
    dashboard: DashboardSpec
