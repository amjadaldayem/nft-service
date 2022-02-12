import dataclasses
from datetime import datetime
from typing import (
    List,
    Optional
)

from app.blockchains import (
    SECONDARY_MARKET_EVENT_UNKNOWN,
    EMPTY_PUBLIC_KEY,
    EMPTY_TRANSACTION_HASH, SECONDARY_MARKET_EVENT_LISTING, SECONDARY_MARKET_EVENT_SALE
)
from app.settings import SME_AGGREGATION_WINDOW


@dataclasses.dataclass
class MediaFile:
    uri: str
    file_type: str = ''


@dataclasses.dataclass
class NftCreator:
    address: str
    verified: bool = False
    share: int = 0


@dataclasses.dataclass
class NftData:
    blockchain_id: int
    token_address: str
    collection_key: str  # Unique address or something that identifies this collection scoped to that chain
    current_owner: str
    name: str
    description: str
    symbol: str
    primary_sale_happened: bool
    metadata_uri: str
    creators: List[NftCreator]
    ext_data: dict = dataclasses.field(default_factory=dict)
    edition: str = ""
    attributes: dict = dataclasses.field(default_factory=dict)
    external_url: str = ""
    files: List[MediaFile] = dataclasses.field(default_factory=List)

    @property
    def collection_id(self):
        return f"bn#{self.blockchain_id}#{self.collection_key}"

    @property
    def nft_id(self):
        return f"bn#{self.blockchain_id}#{self.token_address}"

    @property
    def media_url(self):
        """

        Returns:
            The 1st URL in the files array.
        """
        return self.files[0].uri


@dataclasses.dataclass
class SecondaryMarketEvent:
    blockchain_id: int  # The Index for the blockchain
    market_id: int  # The secondary market ID, e.g. SOLANA_MAGIC_EDEN
    timestamp: int  # Approx. unix timestamp (seconds since epoch)
    event_type: int = SECONDARY_MARKET_EVENT_UNKNOWN  # See above
    token_key: str = ''  # Token address / Mint key
    price: int = 0  # Listing/Sale price in the smallest UNIT. E.g., for Solana this is lamports
    owner: str = EMPTY_PUBLIC_KEY  # Account that owns this piece, who liste / sells this.
    buyer: str = EMPTY_PUBLIC_KEY
    transaction_hash: str = EMPTY_TRANSACTION_HASH
    data: Optional[dict] = None  # Extra information

    @property
    def sme_id(self):
        return f'be#{self.blockchain_id}#{self.transaction_hash}'

    @property
    def w(self) -> str:
        """
        The time window marker
        Returns:
            w#<date-hour-5min_window>
        """

        try:
            dt = datetime.fromtimestamp(self.timestamp)
            minute_marker = dt.minute % SME_AGGREGATION_WINDOW
            s = dt.strftime('%Y-%m-%d-%H-')
            return f"w#{s}{minute_marker:02d}"
        except:
            return 'unknown'

    @property
    def btt(self) -> str:
        """
        Blockchain - timestamp attribute
        Returns:
            bt#<blockchain_id>#<timestamp>#transaction_hash
        """
        return f"btt#{self.blockchain_id}#{self.timestamp}#{self.transaction_hash}"

    @property
    def et(self) -> str:
        """
        Event - timestamp attribiute

        Returns:
            et#<event_type>#<timestamp>
        """
        return f"et#{self.event_type}#{self.timestamp}"

    @property
    def eblt(self) -> Optional[str]:
        """
        Event Buy & Listing

        Returns:
             eblt#<timestamp>
        """
        return (
            f"eblt#{self.timestamp}"
            if self.event_type == SECONDARY_MARKET_EVENT_LISTING
            or self.event_type == SECONDARY_MARKET_EVENT_SALE else None
        )
