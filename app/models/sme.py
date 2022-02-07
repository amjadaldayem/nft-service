import dataclasses
from typing import Optional

from app import settings
from app.blockchains import (
    SECONDARY_MARKET_EVENT_UNKNOWN,
    EMPTY_PUBLIC_KEY,
    EMPTY_TRANSACTION_HASH
)
from app.models.dynamo import DynamoDBRepositoryBase


@dataclasses.dataclass
class SecondaryMarketEvent:
    blockchain_id: int  # The Index for the blockchain
    market_id: int  # The secondary market ID, e.g. SOLANA_MAGIC_EDEN
    timestamp: int  # Approx. unix timestamp
    event_type: int = SECONDARY_MARKET_EVENT_UNKNOWN  # See above
    token_key: str = ''  # Token address / Mint key
    price: int = 0  # Listing/Sale price in the smallest UNIT. E.g., for Solana this is lamports
    owner: str = EMPTY_PUBLIC_KEY  # Account that owns this piece, who liste / sells this.
    buyer: str = EMPTY_PUBLIC_KEY
    transaction_hash: str = EMPTY_TRANSACTION_HASH
    data: Optional[dict] = None  # Extra information

    @property
    def dedupe_key(self):
        return f'{self.blockchain_id}-{self.transaction_hash}'


class SMERepository(DynamoDBRepositoryBase):
    """
    pk                                         sk

    b#<blockchain_id>#transaction_hash         'e'   event data
                                               'n'   NFT Metadata
    """

    def __init__(self, dynamodb_resource):
        super().__init__(
            settings.DYNAMODB_SME_TABLE,
            dynamodb_resource,
        )
