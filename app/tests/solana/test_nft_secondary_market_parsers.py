import orjson
import os
import unittest
from typing import Tuple

from app.blockchains import (
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SOLANA_SOLANART,
    SOLANA_DIGITAL_EYES,
    SOLANA_SOLSEA,
    SecondaryMarketEvent,
    SECONDARY_MARKET_EVENT_LISTING,
    SECONDARY_MARKET_EVENT_DELISTING,
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_PRICE_UPDATE,
)
from app.blockchains.solana import ParsedTransaction

data_basedir = 'data'

market_id_dir_map = {
    SOLANA_MAGIC_EDEN: os.path.join(data_basedir, 'magic_eden'),
    SOLANA_ALPHA_ART: os.path.join(data_basedir, 'alpha_art'),
    SOLANA_SOLANART: os.path.join(data_basedir, 'solanart'),
    SOLANA_DIGITAL_EYES: os.path.join(data_basedir, 'digital_eyes'),
    SOLANA_SOLSEA: os.path.join(data_basedir, 'solsea'),
}

event_type_dir_map = {
    SECONDARY_MARKET_EVENT_LISTING: 'listing',
    SECONDARY_MARKET_EVENT_DELISTING: 'delisting',
    SECONDARY_MARKET_EVENT_SALE: 'sale',
    SECONDARY_MARKET_EVENT_PRICE_UPDATE: 'price_update',
}


async def load_and_parse(market_id, event_type_id, file_name) -> Tuple[SecondaryMarketEvent, int]:
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
    elif event_type_id in (SECONDARY_MARKET_EVENT_LISTING,
                           SECONDARY_MARKET_EVENT_PRICE_UPDATE):
        evt.owner = owner_or_buyer
        evt.price = price
    else:
        # Delisting
        evt.owner = owner_or_buyer
    return evt


async def test_events_for(test_case, market_id, generate_expected=False):
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
            event = await pt.event
            if event:
                results.append(event)

    if generate_expected:
        # This is for generating the expected JSON initially
        # not really doing any assertion in this branch.
        # Normally used to only manually set generate_expected to true
        # only upon initial test run.
        with open(os.path.join(market_id_dir_map[market_id],
                               'txns-expected.json'), 'wb') as fd:
            fd.write(orjson.dumps(results, option=orjson.OPT_INDENT_2))
    else:

        with open(os.path.join(market_id_dir_map[market_id],
                               'txns-expected.json'), 'rb') as fd:
            test_case.assertEqual(
                orjson.dumps(results, option=orjson.OPT_INDENT_2),
                fd.read()
            )


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

    async def test_magic_eden_delisting_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_magic_eden_events(self):
        await test_events_for(self, SOLANA_MAGIC_EDEN)


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

    async def test_alpha_art_listing_event_03(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_delisting_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_delisting_event_02(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_delisting_event_03(self):
        event, timestamp = await load_and_parse(
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

    async def test_alpha_art_sale_event_02(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_alpha_art_events(self):
        await test_events_for(self, SOLANA_ALPHA_ART)


class SolanartTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_solanart_listing_event_01(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_LISTING,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='CjpknwfKuLnJGELurHgioq4FSw1WoBJzZh8rfKtJaMnA',
            price=10000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_delisting_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_sale_event_01(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='2Pw69uefPXeqD2PvLjDMD3CohKWFixKVwkf5yJSzAu5K',
            price=32000000000,
            owner_or_buyer='okkVSrkBXGfMHvEfKGUW73XmJYbP4ojPbWsBXbYjvZf',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_sale_event_02(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            '02.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='nnsyke25QR3yJAmAuQhjESEHHjs93iyUqKaKPhGWtQh',
            price=45000000000,
            owner_or_buyer='2K482avagGyeeRKgymNsfRrR46pWXCTxKFHSZG7zkVpB',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_sale_event_03(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            '03.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='5m4HCYXN4E7hCc8i5ojMRhYAwyv91WQQX58vv3Fggop6',
            price=20000000000,
            owner_or_buyer='DZvw8KcBV4c5KQJY4qmyVBBPutorJtVQZUoHVb7WLPX3',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_sale_event_04(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            '04.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
            price=180000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_sale_event_05(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            '05.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_SALE,
            token_key='CjpknwfKuLnJGELurHgioq4FSw1WoBJzZh8rfKtJaMnA',
            price=1000000,
            owner_or_buyer='BQYdVG7u7YSnKeH65LuQKy8EWUnzC27XUenhV6CmFTtR',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_price_update_event_01(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '01.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='CjpknwfKuLnJGELurHgioq4FSw1WoBJzZh8rfKtJaMnA',
            price=10000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_price_update_event_02(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '02.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='CjpknwfKuLnJGELurHgioq4FSw1WoBJzZh8rfKtJaMnA',
            price=100000000000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_price_update_event_03(self):
        event, timestamp = await load_and_parse(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            '03.json'
        )
        expected = make_expected(
            SOLANA_SOLANART,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            token_key='CjpknwfKuLnJGELurHgioq4FSw1WoBJzZh8rfKtJaMnA',
            price=1000000,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solanart_events(self):
        await test_events_for(self, SOLANA_SOLANART)


class DigitalEyesTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_digital_eyes_listing_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_listing_event_02(self):
        event, timestamp = await load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='9H3ncfCp31nA9bTnaEUezkMGgtc869HCCjF5riH7iWTP',
            price=570000000,
            owner_or_buyer='9qAeEjpQTLtrXcbnPvFwS3nvuApiQNMUauzfYx1CxpU5',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_listing_event_03(self):
        event, timestamp = await load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            '03.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_LISTING,
            token_key='B3yBqWgc7krrUpkGRiZuSQJWrkPCCXpoB3JJPMVmjwC6',
            price=690000000,
            owner_or_buyer='CXXXajBynVVezT4GeAtmjcJojcy4QSb7XqPHYNCa6BsK',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_price_update_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_price_update_event_02(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_price_update_event_03(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_price_update_event_04(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_delisting_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_delisting_event_02(self):
        event, timestamp = await load_and_parse(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            '02.json'
        )
        expected = make_expected(
            SOLANA_DIGITAL_EYES,
            SECONDARY_MARKET_EVENT_DELISTING,
            token_key='5xMBU72azWpXC9VSvrJBBZDTd5F2h6Wztrx386pwr3Uo',
            price=0,
            owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_sale_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_digital_eyes_events(self):
        await test_events_for(self, SOLANA_DIGITAL_EYES)


class SolseaTestCase(unittest.IsolatedAsyncioTestCase):

    async def test_solsea_listing_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solsea_listing_event_02(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solsea_listing_event_03(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solsea_sale_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solsea_delisting_event_01(self):
        event, timestamp = await load_and_parse(
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
            timestamp=timestamp
        )
        self.assertEqual(event, expected)

    async def test_solsea_events(self):
        await test_events_for(self, SOLANA_SOLSEA)