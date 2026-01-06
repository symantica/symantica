from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List

from .dataset import DatasetSpec
from .metric import MetricSpec
from .behavior import BehaviorSpec
from .dashboard import DashboardSpec


class ProjectSpec(BaseModel):
    dataset: DatasetSpec
    metrics: List[MetricSpec] = Field(..., min_length=1)
    behaviors: BehaviorSpec
    dashboard: DashboardSpec
