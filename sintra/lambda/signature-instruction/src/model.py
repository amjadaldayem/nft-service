from dataclasses import dataclass
from typing import Any, Optional

import orjson
from humps import camelize
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class DataClassBase(BaseModel):
    class Config:
        extra = "ignore"
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        underscore_attrs_are_private = True
        allow_population_by_field_name = True
        alias_generator = camelize


class SecondaryMarketEvent(DataClassBase):
    blockchain_id: int
    market_id: int
    timestamp: int
    event_type: int = 0
    token_key: Optional[str]
    price: int = 0
    owner: str
    buyer: Optional[str]
    transaction_hash: Optional[str]
    data: Optional[Any] = None


@dataclass
class SignatureEvent:
    """Record representing transaction signature that occurred on the market."""

    market: str
    market_address: int
    market_account: str
    signature: str
    timestamp: int
