# pylint: disable=no-value-for-parameter

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


class MediaFile(DataClassBase):
    uri: str
    file_type: Optional[str]


class NFTCreator(DataClassBase):
    address: str
    verified: bool = False
    share: int = 0


@dataclass
class NFTData(DataClassBase):
    blockchain_id: int
    collection_id: str
    token_address: str
    owner: str
    token_name: str
    description: str
    symbol: str
    primary_sale_happened: bool
    last_market_activity: str
    timestamp_of_market_activity: int
    metadata_uri: str
    attributes: dict = dataclasses.Field(default_factory=dict)
    transaction_hash: str
    price: float
    price_currency: Optional[str]
    creators: List[NFTCreator]
    edition: Optional[str]
    external_url: Optional[str]
    media_files: List[MediaFile] = dataclasses.Field(default_factory=List)
    extra_data: Dict[str, Any] = dataclasses.Field(default_factory=dict)

    def to_dikt(self) -> Dict[str, Any]:
        return {
            "blockchain_id": self.blockchain_id,
            "collection_id": self.collection_id,
            "token_address": self.token_address,
            "owner": self.owner,
            "token_name": self.token_name,
            "description": self.description,
            "symbol": self.symbol,
            "primary_sale_happened": self.primary_sale_happened,
            "last_market_activity": self.last_market_activity,
            "timestamp_of_market_activity": self.timestamp_of_market_activity,
            "metadata_uri": self.metadata_uri,
            "attributes": self.attributes,
            "transaction_hash": self.transaction_hash,
            "price": self.price,
            "price_currency": ""
            if self.price_currency is None
            else self.price_currency,
            "creators": self.creators,
            "edition": "" if self.edition is None else self.edition,
            "external_url": "" if self.external_url is None else self.external_url,
            "media_files": self.media_files,
            "extra_data": self.extra_data,
        }


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

    @classmethod
    def from_dict(cls, metadata_dict: Dict[str, Any]) -> NFTMetadata:
        return cls(
            blockchain_id=metadata_dict["blockchain_id"],
            token_key=metadata_dict["token_key"],
            timestamp=metadata_dict["timestamp"],
            program_account_key=metadata_dict["program_account_key"],
            primary_sale_happened=metadata_dict["primary_sale_happened"],
            is_mutable=metadata_dict["is_mutable"],
            name=metadata_dict.get("name", None),
            symbol=metadata_dict.get("symbol", None),
            uri=metadata_dict.get("uri", None),
            owner=metadata_dict.get("owner", None),
            seller_fee_basis_points=metadata_dict["seller_fee_basis_points"],
            creators=metadata_dict["creators"],
            verified=metadata_dict["verified"],
            share=metadata_dict["share"],
            ext_data=metadata_dict["ext_data"],
        )
