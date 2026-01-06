from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class DatasetSpec(BaseModel):
    name: str = Field(..., min_length=1)
    table: str = Field(..., min_length=1)
    time_column: str = Field(..., min_length=1)

    description: Optional[str] = None
    default_grain: str = "day"
