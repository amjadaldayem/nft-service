from typing import Tuple

from app.blockchains import (
    SECONDARY_MARKET_EVENT_UNKNOWN,
    SECONDARY_MARKET_EVENT_LISTING,
    SECONDARY_MARKET_EVENT_DELISTING,
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_PRICE_UPDATE,
)

from app.models import (
    NFTRepository,
    SMERepository,
    SecondaryMarketEvent,
)
from app.models.shared import DataClassBase

SECONDARY_EVENT_NAME_MAP = {
    SECONDARY_MARKET_EVENT_UNKNOWN: 'Unknown',
    SECONDARY_MARKET_EVENT_LISTING: 'Listed',
    SECONDARY_MARKET_EVENT_DELISTING: 'De-Listed',
    SECONDARY_MARKET_EVENT_SALE: 'Sold',
    SECONDARY_MARKET_EVENT_PRICE_UPDATE: 'Price Updated',
}


class SmeNftResponseModel(DataClassBase):
    """
    DigitalEyes Link format
    https://digitaleyes.market/item/_/<token_key>
    """
    token_key: str  # Mint/token address
    market: Tuple[str, str]  # name, link
    buyer: Tuple[str, str]  # name, link
    owner: Tuple[str, str]  # name, link
    price: str
    timestamp: int  # Seconds since Epoch
    event: str
    # Opaque key used for pagination
    e_key: str
    # User bookmark info
    bookmarked: bool = False


class NFTService:

    def __init__(self, *, dynamodb_resource):
        self.nft_repository = NFTRepository(
            dynamodb_resource=dynamodb_resource,
        )
        self.sme_repository = SMERepository(
            dynamodb_resource=dynamodb_resource
        )

    @classmethod
    def make_opaque_key(cls, sme: SecondaryMarketEvent):
        """
        A key derived from `w` and `tbt` that uniquely identifies an event.
        This key is opaque to users and client side can use it as the
        exclusive start/stop key.

        Returns:

        """


