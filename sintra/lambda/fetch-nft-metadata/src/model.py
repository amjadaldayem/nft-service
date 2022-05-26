from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

import orjson
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


class SecondaryMarketEvent(DataClassBase):
    """Market event data extracted from transaction signature."""

    blockchain_id: int
    market_id: int
    blocktime: int
    timestamp: int
    event_type: int = 0
    token_key: Optional[str]
    price: int = 0
    owner: Optional[str]
    buyer: Optional[str]
    transaction_hash: str
    data: Optional[Any] = None

    @classmethod
    def from_dict(cls, market_dict: Dict[str, Any]) -> SecondaryMarketEvent:
        return cls(
            blockchain_id=market_dict["blockchain_id"],
            market_id=market_dict["market_id"],
            blocktime=market_dict["blocktime"],
            timestamp=market_dict["timestamp"],
            event_type=market_dict["event_type"],
            token_key=market_dict.get("token_key", None),
            price=market_dict["price"],
            owner=market_dict.get("owner", None),
            buyer=market_dict.get("buyer", None),
            transaction_hash=market_dict["transaction_hash"],
            data=market_dict.get("data", None),
        )


@dataclass
class NFTMetadata:
    blockchain_id: Optional[int]
    token_key: str
    timestamp: int
    program_account_key: str
    primary_sale_happened: bool
    is_mutable: bool
    name: Optional[str]
    symbol: Optional[str]
    uri: Optional[str]
    owner: Optional[str]
    seller_fee_basis_points: str
    creators: List[str]
    verified: List[str]
    share: List[str]
    ext_data: Mapping = dataclasses.field(default_factory=dict)

    @property
    def creators_info(self) -> List[Mapping]:
        creators = self.creators
        verified = self.verified
        share = self.share
        lc = len(creators)
        lv = len(verified)
        ls = len(share)

        if not (lc == lv == ls):
            return []

        return [
            {
                "creator": creators[i],
                "share": share[i],
                "verified": verified[i],
            }
            for i in range(lc)
        ]

    def to_dikt(self) -> Dict[str, Any]:
        return {
            "blockchain_id": self.blockchain_id,
            "token_key": self.token_key,
            "timestamp": self.timestamp,
            "program_account_key": self.program_account_key,
            "primary_sale_happened": self.primary_sale_happened,
            "is_mutable": self.is_mutable,
            "name": "" if self.name is None else self.name,
            "symbol": "" if self.symbol is None else self.symbol,
            "uri": "" if self.uri is None else self.uri,
            "owner": "" if self.owner is None else self.owner,
            "seller_fee_basis_points": self.seller_fee_basis_points,
            "creators": self.creators,
            "verified": self.verified,
            "share": self.share,
            "ext_data": self.ext_data,
        }
