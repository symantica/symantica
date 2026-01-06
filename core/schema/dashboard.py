from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List


class PageSpec(BaseModel):
    name: str = Field(..., min_length=1)
    include_metrics: List[str] = Field(..., min_length=1)
    views: List[str] = Field(default_factory=lambda: ["kpi", "trend", "breakdown"])
    breakdown_dims: List[str] = Field(default_factory=list)


class DashboardSpec(BaseModel):
    title: str = Field(..., min_length=1)
    pages: List[PageSpec] = Field(..., min_length=1)
