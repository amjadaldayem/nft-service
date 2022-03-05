from datetime import datetime
from typing import (
    List,
    Optional,
    Any
)

from pydantic import dataclasses

from app.blockchains import (
    SECONDARY_MARKET_EVENT_UNKNOWN,
    EMPTY_PUBLIC_KEY,
    EMPTY_TRANSACTION_HASH
)
from app.models.shared import DataClassBase
from app.settings import SME_AGGREGATION_WINDOW

NO_VALUE = '__NO_VALUE__'


class MediaFile(DataClassBase):
    uri: str
    file_type: str = ''


class NftCreator(DataClassBase):
    address: str
    verified: bool = False
    share: int = 0


class NftData(DataClassBase):
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
    ext_data: dict = dataclasses.Field(default_factory=dict)
    edition: str = ""
    attributes: dict = dataclasses.Field(default_factory=dict)
    external_url: str = ""
    files: List[MediaFile] = dataclasses.Field(default_factory=List)

    @property
    def collection_id(self):
        return f"bc#{self.blockchain_id}#{self.collection_key}"

    @property
    def collection_name(self):
        name = self.name
        if not name:
            collection_name = self.symbol or ""
        else:
            try:
                collection_name, _ = name.rsplit('#', 10)
            except:
                collection_name = name
        collection_name = collection_name.strip()
        return collection_name if collection_name else NO_VALUE

    @property
    def nft_id(self):
        return f"bn#{self.blockchain_id}#{self.token_address}"

    @property
    def current_owner_id(self):
        return f"bo#{self.blockchain_id}#{self.current_owner}"

    @property
    def media_url(self):
        """

        Returns:
            The 1st URL in the files array.
        """
        return self.files[0].uri or ''


class SecondaryMarketEvent(DataClassBase):
    blockchain_id: int  # The Index for the blockchain
    market_id: int  # The secondary market ID, e.g. SOLANA_MAGIC_EDEN
    timestamp: int  # Approx. unix timestamp (seconds since epoch)
    event_type: int = SECONDARY_MARKET_EVENT_UNKNOWN  # See above
    token_key: str = ''  # Token address / Mint key
    price: int = 0  # Listing/Sale price in the smallest UNIT. E.g., for Solana this is lamports
    owner: str = EMPTY_PUBLIC_KEY  # Account that owns this piece, who liste / sells this.
    buyer: str = EMPTY_PUBLIC_KEY
    transaction_hash: str = EMPTY_TRANSACTION_HASH
    data: Optional[Any] = None  # Extra information

    @staticmethod
    def get_time_window_key(timestamp):
        """
        Generates the time window key used as PK in sme table.

        Args:
            timestamp:

        Returns:

        """
        try:
            # By default, on server this should be in UTC always.
            dt = datetime.fromtimestamp(timestamp)
            minute_marker = dt.minute // SME_AGGREGATION_WINDOW
            s = dt.strftime('%Y-%m-%d-%H-')
            return f"w#{s}{minute_marker:02d}"
        except:
            return 'unknown'

    @classmethod
    def get_timestamp_blockchain_transaction_key(cls,
                                                 timestamp,
                                                 blockchain_id,
                                                 transaction_hash):
        blockchain_id = blockchain_id or ''
        transaction_hash = transaction_hash or ''
        return f"tbt#{timestamp}#{blockchain_id}#{transaction_hash}".rstrip('#')

    @classmethod
    def get_blockchain_timestamp_transaction_key(cls,
                                                 blockchain_id,
                                                 timestamp,
                                                 transaction_hash):
        blockchain_id = blockchain_id or ''
        transaction_hash = transaction_hash or ''
        return f"btt#{blockchain_id}#{timestamp}#{transaction_hash}".rstrip('#')

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
        return self.get_time_window_key(self.timestamp)

    @property
    def btt(self) -> str:
        """
        Blockchain - timestamp attribute
        Returns:
            btt#<blockchain_id>#<timestamp>#transaction_hash
        """
        return self.get_blockchain_timestamp_transaction_key(
            self.blockchain_id,
            self.timestamp,
            self.transaction_hash
        )

    @property
    def tbt(self) -> str:
        """
        Timestamp - blockchain id - transaction id
        Returns:
            tbt#<timestamp>#<blockchain_id>#transaction_hash
        """
        return self.get_timestamp_blockchain_transaction_key(
            self.timestamp,
            self.blockchain_id,
            self.transaction_hash
        )

    @property
    def et(self) -> str:
        """
        Event - timestamp attribiute

        Returns:
            et#<event_type>#<timestamp>
        """
        return f"et#{self.event_type}#{self.timestamp}"
