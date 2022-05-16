from enum import Enum
import json
from sintra.lambdas.shared.constants import BLOCKCHAIN_SOLANA
from sintra.lambdas.shared.secondary_market_event import SecondaryMarketEvent
from sintra.lambdas.solana.constants import SECONDARY_MARKET_EVENT_SALE, SECONDARY_MARKET_EVENT_SALE_AUCTION, \
    SECONDARY_MARKET_EVENT_BID, SECONDARY_MARKET_EVENT_CANCEL_BIDDING, SECONDARY_MARKET_EVENT_LISTING, \
    SECONDARY_MARKET_EVENT_PRICE_UPDATE, SOLANA_MAGIC_EDEN, SECONDARY_MARKET_EVENT_DELISTING


class TestDataCategory(Enum):
    LISTING = "listing"
    SALE = "sale"
    BID = "bid"
    CANCEL_BIDDING = "cancel_bidding"
    DELISTING = "delisting"
    PRICE_UPDATE = "price_update"
    SALE_AUCTION = "sale_auction"


project_root = "../../../"
magic_eden_test_data_directory = "/app/tests/data/solana/transactions/magic_eden"


def generate_secondary_market_event(market_id, event_type_id, token_key, price, owner_or_buyer, timestamp, signature):
    secondary_market_event = SecondaryMarketEvent(
        blockchain_id=BLOCKCHAIN_SOLANA,
        market_id=market_id,
        event_type=event_type_id,
        timestamp=timestamp,
        token_key=token_key,
        transaction_hash=signature
    )
    if event_type_id in {SECONDARY_MARKET_EVENT_SALE,
                         SECONDARY_MARKET_EVENT_SALE_AUCTION,
                         SECONDARY_MARKET_EVENT_BID,
                         SECONDARY_MARKET_EVENT_CANCEL_BIDDING}:
        secondary_market_event.buyer = owner_or_buyer
        secondary_market_event.price = price
    elif event_type_id in (SECONDARY_MARKET_EVENT_LISTING,
                           SECONDARY_MARKET_EVENT_PRICE_UPDATE):
        secondary_market_event.owner = owner_or_buyer
        secondary_market_event.price = price
    else:
        # Delisting, price update etc
        secondary_market_event.owner = owner_or_buyer
    return secondary_market_event


def load_json(test_category: str, file_name: str):
    test_json_file_path = project_root + magic_eden_test_data_directory + "/" + test_category + "/" + file_name

    return json.loads(open(test_json_file_path, 'r').read())
