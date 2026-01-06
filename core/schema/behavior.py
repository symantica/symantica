from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


class ComparePeriodSpec(BaseModel):
    enabled: bool = False
    modes: List[str] = Field(default_factory=lambda: ["previous_period"])


class DrilldownSpec(BaseModel):
    enabled: bool = False
    max_rows: int = 5000


class BehaviorSpec(BaseModel):
    global_filters: List[str] = Field(default_factory=list)
    compare_period: Optional[ComparePeriodSpec] = None
    drilldown: Optional[DrilldownSpec] = None
    export_formats: List[str] = Field(default_factory=lambda: ["csv"])
