
from __future__ import annotations

import hashlib
import json
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

MetricType = Literal["count", "sum", "avg", "distinct_count", "ratio", "derived"]


class MetricSpec(BaseModel):
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    semantic_key: str = Field(..., min_length=3, description="Stable business concept key")
    type: MetricType

    expr: Optional[str] = None
    numerator: Optional[str] = None
    denominator: Optional[str] = None
    formula: Optional[str] = None

    description: Optional[str] = None
    format: Optional[str] = None
    owner: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)

    @field_validator("semantic_key")
    @classmethod
    def _semantic_key_format(cls, v: str) -> str:
        if " " in v:
            raise ValueError("semantic_key must not contain spaces")
        return v.strip()

    def canonical_definition(self) -> dict:
        return {
            "type": self.type,
            "expr": (self.expr or "").strip() or None,
            "numerator": (self.numerator or "").strip() or None,
            "denominator": (self.denominator or "").strip() or None,
            "formula": (self.formula or "").strip() or None,
        }

    def definition_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_definition(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

