import json
import os
import unittest
from typing import Tuple

from app.blockchains import (
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SECONDARY_MARKET_EVENT_LISTING
)
from app.blockchains import SecondaryMarketEvent, SECONDARY_MARKET_EVENT_UNLISTING, SECONDARY_MARKET_EVENT_SALE
from app.blockchains.solana import ParsedTransaction

data_basedir = 'data'

market_id_dir_map = {
    SOLANA_MAGIC_EDEN: os.path.join(data_basedir, 'magic_eden'),
    SOLANA_ALPHA_ART: os.path.join(data_basedir, 'alpha_art'),
}

event_type_dir_map = {
    SECONDARY_MARKET_EVENT_LISTING: 'listing',
    SECONDARY_MARKET_EVENT_UNLISTING: 'unlisting',
    SECONDARY_MARKET_EVENT_SALE: 'sale'
}


async def load_and_parse(market_id, event_type_id, file_name) -> Tuple[SecondaryMarketEvent, int]:
    with open(
            os.path.join(
                market_id_dir_map[market_id],
                event_type_dir_map[event_type_id],
                file_name
            ), 'rb'
    ) as c:
        transaction_dict = json.load(c)
    timestamp = transaction_dict['blockTime']
    pt = ParsedTransaction.from_transaction_dict(transaction_dict)
    event = await pt.event
    return event, timestamp


def make_expected(market_id, event_type_id, token_key, price, owner_or_buyer, timestamp):
    evt = SecondaryMarketEvent(
        market_id=market_id,
        event_type=event_type_id,
        timestamp=timestamp,
        token_key=token_key,
    )
    if event_type_id == SECONDARY_MARKET_EVENT_SALE:
        evt.buyer = owner_or_buyer
        evt.price = price
    elif event_type_id == SECONDARY_MARKET_EVENT_LISTING:
        evt.owner = owner_or_buyer
        evt.price = price
    else:
        # Unlisting
        evt.owner = owner_or_buyer
    return evt


class MagicEdenTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_magic_eden_listing_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_listing_event_02(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_listing_event_03(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_listing_event_04(self):
        event, timestamp = await load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '04.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='CiF2QP7NUfz3t7ZpoTavtRvZRdWadxaUFQKZK6EA6Tjm',
            price=3990000000,
            owner_or_buyer='2b9MDayv83BYeuChcrD1CJuQMxzcd1ALSXiRQ6o4YgGF',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_listing_event_05(self):
        event, timestamp = await load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            '05.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='5jcY8Ekvi8frZVPy9rHTtaNBzDvKNb94L9xH7bGJR68b',
            price=800000000,
            owner_or_buyer='4rfMxcVTKwsx8jexi52nSQG8eCtr8B9yAjcormoVwGFL',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_sale_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_sale_event_02(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_sale_event_03(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_sale_event_04(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_sale_event_05(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_unlisting_event(self):
        event, timestamp = await load_and_parse(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_UNLISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_MAGIC_EDEN,
            SECONDARY_MARKET_EVENT_UNLISTING,
            token_key='rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)


class AlphaArtTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_alpha_art_listing_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_listing_event_02(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_unlisting_event_01(self):
        event, timestamp = await load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_UNLISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_UNLISTING,
            token_key='2Pw69uefPXeqD2PvLjDMD3CohKWFixKVwkf5yJSzAu5K',
            price=0,
            owner_or_buyer='okkVSrkBXGfMHvEfKGUW73XmJYbP4ojPbWsBXbYjvZf',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_unlisting_event_02(self):
        event, timestamp = await load_and_parse(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_UNLISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_ALPHA_ART,
            SECONDARY_MARKET_EVENT_UNLISTING,
            token_key='EekTeMw2boaBjEX9PSRV9P9wz4CRZGAYEkz456M3juX2',
            price=0,
            owner_or_buyer='3iMNngRUK8W1Pfrsj3gAxbPuQXmcb3QJtHzDtdH811Qj',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_sale_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)
