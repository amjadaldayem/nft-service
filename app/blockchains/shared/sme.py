# sme - Secondary Market Event
# Event constants
import dataclasses
from typing import Optional

SECONDARY_MARKET_EVENT_UNKNOWN = 0
SECONDARY_MARKET_EVENT_LISTING = 1
SECONDARY_MARKET_EVENT_DELISTING = 2
SECONDARY_MARKET_EVENT_SALE = 3
SECONDARY_MARKET_EVENT_PRICE_UPDATE = 4

EMPTY_PUBLIC_KEY = ''


@dataclasses.dataclass
class SecondaryMarketEvent:
    market_id: int  # The secondary market ID, e.g. SOLANA_MAGIC_EDEN
    timestamp: int  # Approx. unix timestamp
    event_type: int = SECONDARY_MARKET_EVENT_UNKNOWN  # See above
    token_key: str = ''  # Token address / Mint key
    price: int = 0  # Listing/Sale price in the smallest UNIT. E.g., for Solana this is lamports
    owner: str = EMPTY_PUBLIC_KEY  # Account that owns this piece, who liste / sells this.
    buyer: str = EMPTY_PUBLIC_KEY
    data: Optional[dict] = None  # Extra information
