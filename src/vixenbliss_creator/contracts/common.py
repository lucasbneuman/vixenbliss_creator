from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_utc_datetime(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value)


JsonObject: TypeAlias = dict[str, Any]


class ContractBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, use_enum_values=True)
