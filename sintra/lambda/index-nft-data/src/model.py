# pylint: disable=no-value-for-parameter

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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


class MediaFile(DataClassBase):
    uri: str
    file_type: Optional[str]


class NFTCreator(DataClassBase):
    address: str
    verified: bool = False
    share: int = 0


@dataclass
class NFTData:
    blockchain_id: int
    blockchain_name: Optional[str]
    collection_id: str
    token_key: str
    owner: str
    token_id: str
    token_name: str
    description: str
    symbol: str
    primary_sale_happened: bool
    last_market_activity: str
    timestamp_of_market_activity: int
    event_timestamp: int
    metadata_uri: str
    transaction_hash: str
    price: float
    price_currency: Optional[str]
    creators: List[NFTCreator]
    edition: Optional[str]
    external_url: Optional[str]
    media_files: List[MediaFile] = field(default_factory=List)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dikt(self) -> Dict[str, Any]:
        return {
            "blockchain_id": self.blockchain_id,
            "blockchain_name": self.blockchain_name,
            "collection_id": self.collection_id,
            "token_id": self.token_id,
            "token_key": self.token_key,
            "owner": self.owner,
            "token_name": self.token_name,
            "description": self.description,
            "symbol": self.symbol,
            "primary_sale_happened": self.primary_sale_happened,
            "last_market_activity": self.last_market_activity,
            "timestamp_of_market_activity": self.timestamp_of_market_activity,
            "event_timestamp": self.event_timestamp,
            "metadata_uri": self.metadata_uri,
            "attributes": self.attributes,
            "transaction_hash": self.transaction_hash,
            "price": self.price,
            "price_currency": ""
            if self.price_currency is None
            else self.price_currency,
            "creators": [
                {
                    "address": creator.address,
                    "verified": creator.verified,
                    "share": creator.share,
                }
                for creator in self.creators
            ],
            "edition": "" if self.edition is None else self.edition,
            "external_url": "" if self.external_url is None else self.external_url,
            "media_files": [
                {
                    "uri": media_file.uri,
                    "file_type": media_file.file_type if not None else "",
                }
                for media_file in self.media_files
            ],
        }


@dataclass
class NFTMetadata:
    blockchain_id: Optional[int]
    token_key: str
    blocktime: int
    timestamp: int
    program_account_key: str
    transaction_hash: str
    primary_sale_happened: bool
    last_market_activity: str
    is_mutable: bool
    name: Optional[str]
    symbol: Optional[str]
    uri: Optional[str]
    owner: Optional[str]
    seller_fee_basis_points: str
    creators: List[str]
    verified: List[str]
    share: List[str]

    @classmethod
    def from_dict(cls, metadata_dict: Dict[str, Any]) -> NFTMetadata:
        return cls(
            blockchain_id=metadata_dict["blockchain_id"],
            token_key=metadata_dict["token_key"],
            blocktime=metadata_dict["blocktime"],
            timestamp=metadata_dict["timestamp"],
            program_account_key=metadata_dict["program_account_key"],
            transaction_hash=metadata_dict["transaction_hash"],
            primary_sale_happened=metadata_dict["primary_sale_happened"],
            last_market_activity=metadata_dict["last_market_activity"],
            is_mutable=metadata_dict["is_mutable"],
            name=metadata_dict.get("name", None),
            symbol=metadata_dict.get("symbol", None),
            uri=metadata_dict.get("uri", None),
            owner=metadata_dict.get("owner", None),
            seller_fee_basis_points=metadata_dict["seller_fee_basis_points"],
            creators=metadata_dict["creators"],
            verified=metadata_dict["verified"],
            share=metadata_dict["share"],
        )
