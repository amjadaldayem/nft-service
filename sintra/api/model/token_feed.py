from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _image_url(media_files: List[Dict[str, Any]]) -> str:
    if len(media_files):
        return media_files[0]["uri"]

    return ""


class Token(BaseModel):
    blockchain_id: int
    blockchain_name: Optional[str]
    collection_id: str
    token_id: str
    token_name: str
    description: str
    owner: str
    symbol: str
    event: str
    timestamp: str
    transaction_hash: str
    price: float
    price_currency: Optional[str]
    image_url: str

    @classmethod
    def from_dict(cls, token_dict: Dict[str, Any]) -> Token:
        return cls(
            blockchain_id=token_dict["blockchain_id"],
            blockchain_name=token_dict.get("blockchain_name", ""),
            collection_id=token_dict["collection_id"],
            token_id=token_dict["token_id"],
            token_name=token_dict["token_name"],
            description=token_dict["description"],
            owner=token_dict["owner"],
            symbol=token_dict["symbol"],
            event=token_dict["last_market_activity"],
            timestamp=token_dict["timestamp_of_market_activity"],
            transaction_hash=token_dict["transaction_hash"],
            price=token_dict["price"],
            price_currency=token_dict.get("price_currency", ""),
            image_url=_image_url(token_dict["media_files"]),
        )


class TokenDetails(BaseModel):
    blockchain_id: int
    blockchain_name: Optional[str]
    collection_id: str
    token_key: str
    token_id: str
    token_name: str
    owner: str
    description: str
    symbol: str
    price: float
    price_currency: Optional[str]
    external_url: Optional[str]
    image_url: str
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, token_details: Dict[str, Any]) -> TokenDetails:
        return cls(
            blockchain_id=token_details["blockchain_id"],
            blockchain_name=token_details.get("blockchain_name", ""),
            collection_id=token_details["collection_id"],
            token_key=token_details["token_key"],
            token_id=token_details["token_id"],
            token_name=token_details["token_name"],
            owner=token_details["owner"],
            description=token_details["description"],
            symbol=token_details["symbol"],
            price=token_details["price"],
            price_currency=token_details.get("price_currency", ""),
            external_url=token_details["external_url"],
            image_url=_image_url(token_details["media_files"]),
            attributes=token_details["attributes"],
        )
