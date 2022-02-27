import os
import unittest
from typing import Tuple

import orjson

from app.blockchains import (
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SOLANA_SOLANART,
    SOLANA_DIGITAL_EYES,
    SOLANA_SOLSEA,
    SECONDARY_MARKET_EVENT_LISTING,
    SECONDARY_MARKET_EVENT_DELISTING,
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_PRICE_UPDATE,
    SECONDARY_MARKET_EVENT_BID,
    SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
    SECONDARY_MARKET_EVENT_SALE_AUCTION,
    BLOCKCHAIN_SOLANA,
)
from app.blockchains.solana import ParsedTransaction
from app.models import SecondaryMarketEvent
from app.tests.shared import get_data_path

market_id_dir_map = {
    SOLANA_MAGIC_EDEN: get_data_path('solana', 'transactions', 'magic_eden'),
    SOLANA_ALPHA_ART: get_data_path('solana', 'transactions', 'alpha_art'),
    SOLANA_SOLANART: get_data_path('solana', 'transactions', 'solanart'),
    SOLANA_DIGITAL_EYES: get_data_path('solana', 'transactions', 'digital_eyes'),
    SOLANA_SOLSEA: get_data_path('solana', 'transactions', 'solsea'),
}

event_type_dir_map = {
    SECONDARY_MARKET_EVENT_LISTING: 'listing',
    SECONDARY_MARKET_EVENT_DELISTING: 'delisting',
    SECONDARY_MARKET_EVENT_SALE: 'sale',
    SECONDARY_MARKET_EVENT_PRICE_UPDATE: 'price_update',
    SECONDARY_MARKET_EVENT_BID: 'bid',
    SECONDARY_MARKET_EVENT_CANCEL_BIDDING: 'cancel_bidding',
    SECONDARY_MARKET_EVENT_SALE_AUCTION: 'sale_auction',
}


def load_and_parse(market_id, event_type_id, file_name) -> Tuple[SecondaryMarketEvent, int, str]:
    with open(
            os.path.join(
                market_id_dir_map[market_id],
                event_type_dir_map[event_type_id],
                file_name
            ), 'rb'
    ) as c:
        transaction_dict = orjson.loads(c.read())
    timestamp = transaction_dict['blockTime']
    pt = ParsedTransaction.from_transaction_dict(transaction_dict)
    event = pt.event
    return event, timestamp, pt.signature


def make_expected(market_id, event_type_id, token_key, price, owner_or_buyer, timestamp, signature):
    evt = SecondaryMarketEvent(
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
        evt.buyer = owner_or_buyer
        evt.price = price
    elif event_type_id in (SECONDARY_MARKET_EVENT_LISTING,
                           SECONDARY_MARKET_EVENT_PRICE_UPDATE):
        evt.owner = owner_or_buyer
        evt.price = price
    else:
        # Delisting, price update etc
        evt.owner = owner_or_buyer
    return evt


def assert_events_for(test_case, market_id, generate_expected=False):
    """
    Conventions:
        - a txns.json file containing a list of transactions under the respective
        secondary market data directory (data/<market_name>/txns.json)

    Args:
        test_case:
        market_id:
        generate_expected:

    Returns:

    """
    with open(os.path.join(market_id_dir_map[market_id],
                           'txns.json'), 'rb') as fd:
        transactions = orjson.loads(fd.read())

    results = []

    for transaction in transactions:
        pt = ParsedTransaction.from_transaction_dict(transaction)
        if pt:
            event = pt.event
            if event:
                results.append(event)

    if generate_expected:
        # This is for generating the expected JSON initially
        # not really doing any assertion in this branch.
        # Normally used to only manually set generate_expected to true
        # only upon initial test run.
        with open(os.path.join(market_id_dir_map[market_id],
                               'txns-expected.json'), 'wb') as fd:
            fd.write(orjson.dumps([r.dict() for r in results], option=orjson.OPT_INDENT_2))
    else:

        with open(os.path.join(market_id_dir_map[market_id],
                               'txns-expected.json'), 'rb') as fd:
            test_case.assertEqual(
                results,
                orjson.loads(fd.read())
            )


class MagicEdenTestCase(unittest.TestCase):

    def test_magic_eden_listing_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk',
            price=4000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_listing_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='6NUbZ3cDbf2jMcbhZC6spNgD4TgMkh9g93Vmot5Rx1u7',
            price=350000000,
            owner_or_buyer='A8p1JpCvrbUDvU1RQREc47sjnJataHV7cZaGeBUjdtLP',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_listing_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '03.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='ELZfkWWG6R2LzYPj7Ei7z2ui2dS732xbEexf1SRVnFoY',
            price=60000000,
            owner_or_buyer='3DBVvW16wtGhUDr7uN83ftCe6QbPihm6jESssuZa1rzf',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_listing_event_04(self):
        # V2
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '04.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='As1cySAyfeesM4MBrYZhs46DFMfnHH3ySU32C2xfSgPv',
            price=8000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_listing_event_05(self):
        # V2
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '05.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='CX1uZr5eLcjD4vkcW158TZeAb7sgceYoHDGYwTpqNvSN',
            price=2500000000,
            owner_or_buyer='Hm7DNow95Ln5NYkTVb6WK4jprcxhZxrdzAnNEqRCRxtx',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_listing_event_06(self):
        # V2
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '06.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='8qhdQC6pS7GjvAMA2xWV4EPsQkHPuDeei2UWPJSZ4CYD',
            price=2250000000,
            owner_or_buyer='7kyRyzHy1jdXKoGHsgbLSdAGdbKmw2hsSvEGNAfG8qBh',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_price_update_event_01(self):
        # V2
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
            price=50000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_bid_event_01(self):
        # V2 - Direct Sell offering
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_BID,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_BID,
            token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
            price=30000000,
            owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_auction_event_01(self):
        # V1 auction settle
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            token_key='DgQB3MHh4vr4tK876zv91Zd7GittRwCEJdKpjikRShvF',
            price=700000000,
            owner_or_buyer='52srbq1g4zKyUftKcWngzpFkNmwvUVJW5KG1GwZZL21J',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_auction_event_02(self):
        # V2 auction settle
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            '02.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            token_key='HSJiW3MPPg5PrUg4qdo9jXxiTkX7WZ9tTt5JFUdDXgUp',
            price=121000000000,
            owner_or_buyer='ppTeamTpw1cbC8ybJpppbnoL7xXD9froJNFb5uvoPvb',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_auction_event_03(self):
        # V2 auction settle
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            '03.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            token_key='8qdn8Ft3gD146eY5UCetbpsaXGj4QXb8V1oJw2ycGzjV',
            price=51750000000,
            owner_or_buyer='daoXo7FeRBb4gonerEKhGB5X8rkC9ag16s7cspLYR9g',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='8ag4raw8snR6GbM6znQYv9k4845zs5NYrDZdoxnxaNwK',
            price=10000000000,
            owner_or_buyer='BXxoKHT6CYtRTboZDaJee1ahrHoQSN6RJk3HAKpUWGHa',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '02.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='CiF2QP7NUfz3t7ZpoTavtRvZRdWadxaUFQKZK6EA6Tjm',
            price=2000000000,
            owner_or_buyer='2b9MDayv83BYeuChcrD1CJuQMxzcd1ALSXiRQ6o4YgGF',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '03.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='5jcY8Ekvi8frZVPy9rHTtaNBzDvKNb94L9xH7bGJR68b',
            price=1100000000,
            owner_or_buyer='4rfMxcVTKwsx8jexi52nSQG8eCtr8B9yAjcormoVwGFL',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_04(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '04.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='AF5i9bGy8f7bwfidwEPxjfB6qTzpWzGh3kqxwJpSAirH',
            price=3880000000,
            owner_or_buyer='6ddfgCBy9UzFFkr918FsnLvduA2gXsdEDZxxDyMMWtYk',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_05(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '05.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='AddspwH8RRsS8Z3r3gzzPWw2YeYjC5rRk9cnzxfajcGX',
            price=1400000000,
            owner_or_buyer='8hqVU9JpMykEGv1cfVkvDr2hzhDHrHa89mk1hQchDmrR',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_06(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '06.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
            price=30000000,
            owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_07(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '07.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='BLPdBeUbVD4pX6H9kURxyhgaJR9XHFRWB3WixwwKqRm3',
            price=12300000000,
            owner_or_buyer='5MtT8THrJYLNbxgbpPZUjZchMdmvMTkCT8VR8TQzorMk',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_08(self):
        # V2, sale from an accepted offer.
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '08.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
            price=30000000,
            owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_sale_event_09(self):
        # V1, sale from an accepted offer.
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            '09.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='2EvZ77q5ot3e63nUpGkZaCFKZaQm4u2ciWyRwiKMF1rX',
            price=3400000000,
            owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_delisting_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_DELISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_delisting_event_02(self):
        # V2
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_DELISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='As1cySAyfeesM4MBrYZhs46DFMfnHH3ySU32C2xfSgPv',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_cancel_bidding_event_01(self):
        # V2
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
            token_key='8hUyid6kgBRwTe54wBmQEEGZpbdneWei6e3ZXJcN6oRb',
            price=0,
            owner_or_buyer='75EAivjBWfHZ5LnM1VfqqMZCsgeiAAWZQiqgFQkQQUwm',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_cancel_bidding_event_02(self):
        # V2
        event, timestamp, signature = load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
            token_key='52tS6BhUM4eFKHm6TJuemVU1QLmmocZ1JQNQiNojE8GH',
            price=0,
            owner_or_buyer='4PaeHjgX7nKUYpRhE7eb2TChkxQYDwKXs8wgYsJ7xxUV',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_magic_eden_events(self):
        assert_events_for(self, SOLANA_MAGIC_EDEN)


class AlphaArtTestCase(unittest.TestCase):

    def test_alpha_art_listing_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_LISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='2Pw69uefPXeqD2PvLjDMD3CohKWFixKVwkf5yJSzAu5K',
            price=38000000000,
            owner_or_buyer='okkVSrkBXGfMHvEfKGUW73XmJYbP4ojPbWsBXbYjvZf',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_listing_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_LISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='9FFa3TxK27TfsU5D2iLHt4uT6PM3G3z72NQ48bQ2KT1A',
            price=25980000000,
            owner_or_buyer='6DSC8YifXyMtARzHBo4xMVWhRH3jFjVUwxdvEFux3G7e',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_listing_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_LISTING,
            '03.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='DXnyp6qLf5bBj1vHedTCJPDVQ1fvcAPYWGB6BGNU6oSz',
            price=4750000000,
            owner_or_buyer='HNdsxRZ39ygCpWPMn96hSC2dLiLjRgbHCZ8XDbA6Qw8r',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_delisting_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_DELISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='2Pw69uefPXeqD2PvLjDMD3CohKWFixKVwkf5yJSzAu5K',
            price=0,
            owner_or_buyer='okkVSrkBXGfMHvEfKGUW73XmJYbP4ojPbWsBXbYjvZf',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_delisting_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_DELISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='EekTeMw2boaBjEX9PSRV9P9wz4CRZGAYEkz456M3juX2',
            price=0,
            owner_or_buyer='3iMNngRUK8W1Pfrsj3gAxbPuQXmcb3QJtHzDtdH811Qj',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_delisting_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_DELISTING,
            '03.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='Fqc4ts9nN1Hp1mZR6CEx6yG7T4eZH8FN39ruAGc2fTuC',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_sale_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_SALE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='Fqc4ts9nN1Hp1mZR6CEx6yG7T4eZH8FN39ruAGc2fTuC',
            price=950000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_sale_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_SALE,
            '02.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='EFyoruiPbLG2YdKDAd3Hrtcm7cWGbMf2yutZq86Sovvz',
            price=45000000000,
            owner_or_buyer='DVTbtaDpvEePdsojdWzFe2N1GNUkQMfweT5ReMyK7TW9',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_alpha_art_events(self):
        assert_events_for(self, SOLANA_ALPHA_ART)


class SolanartTestCase(unittest.TestCase):

    def test_solanart_bid_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_BID,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_BID,
            token_key='8hbco5nJC1tSXgkk2XoA94YqaV7w5Y77XETEt6i1AsVC',
            price=187500000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_bid_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_BID,
            '02.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_BID,
            token_key='8hbco5nJC1tSXgkk2XoA94YqaV7w5Y77XETEt6i1AsVC',
            price=190000000,
            owner_or_buyer='HvpKPZE423dAscvC48kMW2hbWR8xXthZzYT2hHnh93w',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_listing_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_LISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='5xMBU72azWpXC9VSvrJBBZDTd5F2h6Wztrx386pwr3Uo',
            price=1000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_delisting_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_DELISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='5xMBU72azWpXC9VSvrJBBZDTd5F2h6Wztrx386pwr3Uo',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_sale_event_01(self):
        # Buy now
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='8hbco5nJC1tSXgkk2XoA94YqaV7w5Y77XETEt6i1AsVC',
            price=375000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_sale_auction_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            token_key='HD4oEubiYoiGwkp2kMxpqMYcQfh4EFuW3viTJVZv6Pec',
            price=175000000000,
            owner_or_buyer='7sb2osoKiUNSPQzpU4SK8J5HnVmKRf9UWj5y8ZUjTNL1',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_sale_auction_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            '02.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            token_key='2UGFEiGEBXTELtZ8qXXMuEPhZ2Z8oXTGpxz6cQigtKrX',
            price=200000000,
            owner_or_buyer='6UKxMPEQRSS99Gc2TDoigbrSfJY5hnnzRGBEANY6y4Y',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_price_update_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='qrxtayzUUVh3iQXGUskzXapokkoLBEsBirxBpssL2g8',
            price=20000000,
            owner_or_buyer='DQ9C6V1RAaUJd9EbLyomgH3bqS7rpJD8AgwkBcpndGFP',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_cancel_bidding_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
            token_key='8hbco5nJC1tSXgkk2XoA94YqaV7w5Y77XETEt6i1AsVC',
            price=0,
            owner_or_buyer='HvpKPZE423dAscvC48kMW2hbWR8xXthZzYT2hHnh93w',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solanart_events(self):
        assert_events_for(self, SOLANA_SOLANART)


class DigitalEyesTestCase(unittest.TestCase):

    def test_digital_eyes_listing_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='DZFnfQzVJtukamiUDaB82r95iDnkCB7uYPoxcAFyJ7Dz',
            price=100000000,
            owner_or_buyer='EzvdttH8j8LmrpBzx8vK73rBuYBJy3ggJ1taA1mwe69o',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_listing_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='872JekNfK9MtsKs28XBNfkHxg5GwzqNXyWWt6mhex7RH',
            price=90000000,
            owner_or_buyer='2F4yS8odiuQMk94zfx548h7RJiD5NUwbYsBbfmcc8Rff',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_listing_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            '03.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='Kyt8aPm6xEWHv4KxcgPJZzYYhqGL3NLJ4YjG2ip8Pfx',
            price=33000000000,
            owner_or_buyer='6EeR8NS7zFCWAspSKVcE6UcEj4TZH4wpEtC6Pd9CffEP',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_price_update_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='Cbvj3kCDfiqX8ZdQFch1xfZvBWKhuG7tzTX7wLAUZ4fn',
            price=400000000,
            owner_or_buyer='77vqf9kk2JbMAjNkGf7Au2HwQ8K9fMyi5FLEgbbQwDXD',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_price_update_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '02.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='FKEA7tLr4AFQarvDVDv378xggFyST2y1wU3gTZ8y7ute',
            price=994000000,
            owner_or_buyer='9ttHMahsRUDuLapa8gRJrQVyjLXfC4QUDpgWQ3g9pGkv',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_price_update_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '03.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='CuTQhEBTtKf6TEp6kTgHRuG9an2RexW9WzUeGY2jcuzj',
            price=12000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_price_update_event_04(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '04.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='5xMBU72azWpXC9VSvrJBBZDTd5F2h6Wztrx386pwr3Uo',
            price=12500000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_delisting_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='CuTQhEBTtKf6TEp6kTgHRuG9an2RexW9WzUeGY2jcuzj',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_delisting_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='Kyt8aPm6xEWHv4KxcgPJZzYYhqGL3NLJ4YjG2ip8Pfx',
            price=0,
            owner_or_buyer='6EeR8NS7zFCWAspSKVcE6UcEj4TZH4wpEtC6Pd9CffEP',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_delisting_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            '03.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='BQzHuj5uyUEXDsK4GGQPA25pXudGhoKhFeqvnhLcbeuB',
            price=0,
            owner_or_buyer='5dq2T5Zx3jU9n1Ja9rrUzCGfybcrAYgGKCA7uf45Wqqs',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_sale_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_SALE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='HVqyPbQp7J1FncpshWvPuau3TspjF7ZfRHc67xVuAiFS',
            price=190000000,
            owner_or_buyer='GnsvipETHL3eWp1VZ8Pu9TvbtYFtiTqNQDoH61ms6dPj',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_sale_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_SALE,
            '02.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='872JekNfK9MtsKs28XBNfkHxg5GwzqNXyWWt6mhex7RH',
            price=90000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_digital_eyes_events(self):
        assert_events_for(self, SOLANA_DIGITAL_EYES, generate_expected=True)


class SolseaTestCase(unittest.TestCase):

    def test_solsea_listing_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_LISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='kBxi6eRWQ6Dpep3RWmLKMqr31hZ2PqQYeSCB6RhyzmH',
            price=20000000000,
            owner_or_buyer='BsQCB43M56mqevXEXFFijgt97dv9BeDwEK1yHyV8z1H6',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solsea_listing_event_02(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_LISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='39oQZUjoLJXjW8EbNvFFnydLjsCmChsB66YvnnxGxYpe',
            price=200000000000,
            owner_or_buyer='9u9AyWvf3q7PUYNV7dxQ5SSSTJbFP9LtH574wrGW7s2V',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solsea_listing_event_03(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_LISTING,
            '03.json'
        )
        expected = make_expected(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='HB7szWRJB9VjvgPCq6o4DNyhZp9dytKodYBMqEQdU7df',
            price=35000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solsea_sale_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_SALE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='39oQZUjoLJXjW8EbNvFFnydLjsCmChsB66YvnnxGxYpe',
            price=80000000,
            owner_or_buyer='9u9AyWvf3q7PUYNV7dxQ5SSSTJbFP9LtH574wrGW7s2V',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solsea_delisting_event_01(self):
        event, timestamp, signature = load_and_parse(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_DELISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLSEA,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='HB7szWRJB9VjvgPCq6o4DNyhZp9dytKodYBMqEQdU7df',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp,
            signature=signature
        )
        self.assertEqual(event, expected)

    def test_solsea_events(self):
        assert_events_for(self, SOLANA_SOLSEA)
