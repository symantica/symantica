from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


FieldType = Literal["string", "int", "float", "bool", "date", "timestamp"]


class FieldRefSpec(BaseModel):
    column: str = Field(..., min_length=1)
    type: FieldType = "string"
    description: Optional[str] = None


class ModelSpec(BaseModel):
    """
    Semantic model mapping BI-friendly names -> physical columns.

    MVP: single-table model.
    """
    name: str = Field(..., min_length=1)
    primary_table: str = Field(..., min_length=1)
    primary_key: Optional[str] = None
    time_column: Optional[str] = None

    dimensions: Dict[str, FieldRefSpec] = Field(default_factory=dict)
    measures: Dict[str, FieldRefSpec] = Field(default_factory=dict)
