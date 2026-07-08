from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID
from pydantic.networks import IPvAnyAddress
from pydantic import BaseModel, ConfigDict, model_validator


class Method(str, Enum):
    GET="GET",
    POST="POST",
    PUT="PUT",
    PATCH="PATCH",
    DELETE="DELETE",
    HEAD="HEAD",
    OPTIONS="OPTIONS"


class Log(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    created: datetime | None = None
    ip: IPvAnyAddress
    method: Method
    uri: str
    status_code: int


class LogRequest(BaseModel):
    log: str

class AggregationResult(BaseModel):
    methods: dict[Method, int] | None = None
    status_codes: dict[int, int] | None = None