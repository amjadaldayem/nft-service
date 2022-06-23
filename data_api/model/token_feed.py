from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from data_api.utils import solana_market_name_map, solana_market_urls


def _image_url(media_files: List[Dict[str, Any]]) -> str:
    if len(media_files):
        return media_files[0]["uri"]

    return ""


def user_details(user_address: str) -> EntityDetails:
    """
    Use SolScan API for user details.
    Args:
        user_address: Hash value for user address.

    Returns: entity details with address and url.

    """
    return EntityDetails(
        name=user_address,
        url=f"https://solscan.io/account/{user_address}" if user_address else "",
    )


def market_details(market_id: int, token_key: str) -> EntityDetails:
    market_name_map = solana_market_name_map()
    market_urls = solana_market_urls(token_key)

    name = market_name_map.get(market_id, "")
    url = market_urls.get(market_id, "")

    return EntityDetails(name=name, url=url)


class EntityDetails(BaseModel):
    name: str
    url: str


class Token(BaseModel):
    blockchain_id: int
    blockchain_name: Optional[str]
    collection_id: str
    collection_name: str
    collection_slug: str
    token_id: str
    token_key: str
    token_name: str
    token_slug: str
    description: str
    market: EntityDetails
    owner: EntityDetails
    symbol: str
    event: str
    timestamp: str
    transaction_hash: str
    price: float
    price_currency: Optional[str]
    image_url: str
    bookmarked: bool = False

    @classmethod
    def from_dict(cls, token_dict: Dict[str, Any]) -> Token:
        return cls(
            blockchain_id=token_dict["blockchain_id"],
            blockchain_name=token_dict.get("blockchain_name", ""),
            collection_id=token_dict["collection_id"],
            collection_name=token_dict["collection_name"],
            collection_slug=token_dict["collection_name_slug"],
            token_id=token_dict["token_id"],
            token_key=token_dict["token_key"],
            token_name=token_dict["token_name"],
            token_slug=token_dict["token_name_slug"],
            description=token_dict["description"],
            market=market_details(token_dict["market_id"], token_dict["token_key"]),
            owner=user_details(token_dict["owner"]),
            symbol=token_dict["symbol"],
            event=token_dict["last_market_activity"],
            timestamp=token_dict["timestamp_of_market_activity"],
            transaction_hash=token_dict["transaction_hash"],
            price=token_dict["price"],
            price_currency=token_dict.get("price_currency", ""),
            image_url=_image_url(token_dict["media_files"]),
            bookmarked=token_dict.get("bookmarked", False),
        )


class TokenDetails(BaseModel):
    blockchain_id: int
    blockchain_name: Optional[str]
    collection_id: str
    collection_name: str
    token_key: str
    token_id: str
    token_name: str
    owner: EntityDetails
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
            collection_name=token_details["collection_name"],
            token_key=token_details["token_key"],
            token_id=token_details["token_id"],
            token_name=token_details["token_name"],
            owner=user_details(token_details["owner"]),
            description=token_details["description"],
            symbol=token_details["symbol"],
            price=token_details["price"],
            price_currency=token_details.get("price_currency", ""),
            external_url=token_details["external_url"],
            image_url=_image_url(token_details["media_files"]),
            attributes=token_details["attributes"],
        )
