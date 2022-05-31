from typing import List, Optional

from pydantic import BaseModel


class TokenFeed(BaseModel):
    blockchain_id: int
    blockchain_name: Optional[str]
    collection_id: str
    token_key: str
    owner: str
    token_id: str
    token_name: str
    description: str
    symbol: str
    market_activity: str
    timestamp: int
    metadata_uri: str
    transaction_hash: str
    price: float
    price_currency: Optional[str]
    creators: List[str]
    external_url: Optional[str]
