from typing import Tuple, List, Optional, Union, Set, FrozenSet

from app import settings
from app.blockchains import (
    SECONDARY_MARKET_EVENT_UNKNOWN,
    SECONDARY_MARKET_EVENT_LISTING,
    SECONDARY_MARKET_EVENT_DELISTING,
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_PRICE_UPDATE,
    SECONDARY_MARKET_EVENT_BID,
    SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
    SECONDARY_MARKET_EVENT_SALE_AUCTION,
    SOLANA_DIGITAL_EYES,
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SOLANA_SOLSEA,
    SOLANA_SOLANART
)
from app.blockchains.solana import MARKET_NAME_MAP
from app.models import (
    NFTRepository,
    SMERepository,
    SecondaryMarketEvent, User,
)
from app.models.shared import DataClassBase

SECONDARY_EVENT_NAME_MAP = {
    SECONDARY_MARKET_EVENT_UNKNOWN: 'Unknown',
    SECONDARY_MARKET_EVENT_LISTING: 'Listed',
    SECONDARY_MARKET_EVENT_DELISTING: 'De-Listed',
    SECONDARY_MARKET_EVENT_SALE: 'Sold',
    SECONDARY_MARKET_EVENT_PRICE_UPDATE: 'Price Updated',
    SECONDARY_MARKET_EVENT_BID: 'Bid Placed',
    SECONDARY_MARKET_EVENT_CANCEL_BIDDING: 'Bid Cancelled',
    SECONDARY_MARKET_EVENT_SALE_AUCTION: 'Sold via Auction',
}


class NameUrlPair(DataClassBase):
    name: str
    url: str


class SmeNftResponseModel(DataClassBase):
    """
    """
    token_key: str  # Mint/token address
    media_url: str  # The actua link to the assets for the corresponding NFT
    name: str  # Name of the NFT
    collection_name: str
    description: str
    nft_id: str  # Unique identifier of the NFT
    collection_id: str  # Unique identifier of the Collection
    market: NameUrlPair  # name, link
    buyer: NameUrlPair  # name, link
    owner: NameUrlPair  # name, link
    price: str
    event: str
    # The following 3 fields forms the [timestamp, blockchain_id, transaction_hash]
    # key, which can be used for pagination.
    timestamp: int  # Seconds since Epoch
    blockchain_id: int  # The internal ID (int) of the blockchain
    transaction_hash: str  # The transaction ID / signature
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

    def get_secondary_market_events(self, exclusive_start_key: Tuple[int, int, str],
                                    exclusive_stop_key: Optional[Tuple[int, int, str]],
                                    limit=50,
                                    user: Optional[User] = None,
                                    blockchain_ids=frozenset(),
                                    event_types=frozenset()) -> List[SmeNftResponseModel]:
        """

        Args:
            exclusive_start_key:
            exclusive_stop_key:
            limit:
            user:
            blockchain_ids:
            event_types:

        Returns:

        """
        start_timstamp = exclusive_start_key[0]
        fn_get_time_window_key = SecondaryMarketEvent.get_time_window_key
        fn_get_tbt_key = SecondaryMarketEvent.get_timestamp_blockchain_transaction_key

        w_start = fn_get_time_window_key(exclusive_start_key[0])
        tbt_start = fn_get_tbt_key(*exclusive_start_key)

        stop_timestamp = exclusive_stop_key[0]
        w_stop = fn_get_time_window_key(exclusive_stop_key[0])
        tbt_stop = fn_get_tbt_key(*exclusive_stop_key)

        start_params_name = 'tbt_ub'
        stop_params_name = 'tbt_lb'

        if w_stop > w_start or tbt_stop > tbt_start:
            return []

        ws_in_between = [
            fn_get_time_window_key(w)
            for w in range(start_timstamp, stop_timestamp, settings.SME_AGGREGATION_WINDOW)
        ]
        # Fetching from the following partitions
        #  - w_start
        #  - ws_in_between ...
        #  - w_stop

        # TODO: Later add int the filter expression here
        filter_expression = None

        items = []

        kwargs = {
            'w': w_start,
            start_params_name: tbt_start,
            'tbt_lb_exclusive': True,
            'tbt_ub_exclusive': True,
        }
        if w_start == w_stop:
            kwargs[stop_params_name] = tbt_stop

        skip_next_queries = False
        curr_items = self.sme_repository.get_smes_in_time_window(
            **kwargs,
            filter_expression=filter_expression
        )

        if not curr_items:
            return []

        items.extend(curr_items)

        if len(items) >= limit:
            skip_next_queries = True

        if not skip_next_queries and w_start != w_stop:
            for w in ws_in_between:
                curr_items = self.sme_repository.get_smes_in_time_window(
                    w=w,
                    filter_expression=filter_expression
                )
                items.extend(curr_items)
                if len(items) > limit:
                    skip_next_queries = True
                    break
            if not skip_next_queries:
                kwargs = {
                    'w': w_stop,
                    stop_params_name: tbt_stop,
                }
                curr_items = self.sme_repository.get_smes_in_time_window(
                    **kwargs,
                    filter_expression=filter_expression
                )
                items.extend(curr_items)

        items = items[:limit]

        if not items:
            return []
        # TODO: Later retreives the user_bookmarked_set.
        bookmarked_nft_ids = set() if not user else user.bookmarked_nft_ids

        return [
            self.dynamo_to_sme_nft_response_model(item, bookmarked_nft_ids)
            for item in items
        ]

    @classmethod
    def dynamo_to_sme_nft_response_model(cls, item_dict,
                                         bookmarked_nft_ids: Union[Set, FrozenSet] = frozenset()):
        markte_id = item_dict['market_id']
        token_key = item_dict['token_key']
        nft_id = item_dict['nft_id']
        return SmeNftResponseModel(
            token_key=token_key,
            name=item_dict['name'],
            event=SECONDARY_EVENT_NAME_MAP[item_dict['event_type']],
            description=item_dict['description'],
            collection_name=item_dict['collection_name'],
            media_url=item_dict['media_url'],
            nft_id=nft_id,
            collection_id=item_dict['collection_id'],
            market=cls.get_market_name_url_pair(markte_id, token_key),
            owner=cls.get_account_name_url_pair(item_dict['owner']),
            buyer=cls.get_account_name_url_pair(item_dict['buyer']),
            price=f"{item_dict['price'] / 1000000000:.2f}",
            # The 3 important pieces,
            timestamp=item_dict['timestamp'],
            blockchain_id=item_dict['blockchain_id'],
            transaction_hash=item_dict['transaction_hash'],
            bookmarked=nft_id in bookmarked_nft_ids
        )

    @classmethod
    def get_market_name_url_pair(cls, market_id, token_key):
        name = MARKET_NAME_MAP[market_id]
        if market_id == SOLANA_DIGITAL_EYES:
            url = f"https://digitaleyes.market/item/_/{token_key}"
        elif market_id == SOLANA_MAGIC_EDEN:
            url = f"https://www.magiceden.io/item-details/{token_key}"
        elif market_id == SOLANA_ALPHA_ART:
            url = f"https://www.alpha.art/t/{token_key}"
        elif market_id == SOLANA_SOLANART:
            url = f"https://solanart.io/nft/{token_key}"
        elif market_id == SOLANA_SOLSEA:
            url = f"https://solsea.io/nft/{token_key}"
        else:
            url = ''
        return NameUrlPair(
            name=name,
            url=url
        )

    @classmethod
    def get_account_name_url_pair(cls, account_address):
        """
        Let's user SolScan now.
        Args:
            account_address:

        Returns:

        """
        return NameUrlPair(
            name=account_address,
            url=f"https://solscan.io/account/{account_address}" if account_address else ''
        )
