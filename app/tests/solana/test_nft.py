import json
import unittest

import orjson

from app.blockchains import SecondaryMarketEvent, SECONDARY_MARKET_EVENT_UNLISTING, SECONDARY_MARKET_EVENT_SALE
from app.blockchains import (
    solana,
    SOLANA_MAGIC_EDEN,
    SECONDARY_MARKET_EVENT_LISTING
)
from app.blockchains.solana import ParsedTransaction, MAGIC_EDEN_ADDRESS


class SolanaNftTestCase(unittest.IsolatedAsyncioTestCase):
    @unittest.skip(reason="Temp")
    async def test_get_collection_accounts(self):
        update_authority = 'E6n7aXKC9cJYMLfT1P3GvcdPVQLZZ8g6dUt61GyFM7i4'
        # update_authority = 'ByuUyvzDF6LyAJsBDxd9HuD2wmkbGc2hdam3Z7Ku45Hp'
        # update_authority = 'ByuUyvzDF6LyAJsBDxd9HuD2wmkbGc2hdam3Z7Ku45Hp'
        pdas = await solana.nft_get_collection_pdas(
            update_authority
        )
        nft_meta_list = [await solana.nft_get_metadata(pda) for pda in pdas]
        with open("pandas.json", 'wb') as c:
            c.write(orjson.dumps(nft_meta_list, option=orjson.OPT_INDENT_2))

    @unittest.skip(reason="1")
    async def test_nft_get_metadata_by_pda_key(self):
        print(await solana.nft_get_metadata_by_pda_key('6yyBTAQSR5x6yyWHtLACF63BbZ4LwPYoxMsmEnn1erjb'))

    @unittest.skip(reason="2")
    async def test_nft_get_metadata_by_token_key(self):
        print(await solana.nft_get_metadata_by_token_key('Vdax9bbGgrtDqprCPXZ2dDgcTGZxhGUaUgTRMqGVYm6'))

    async def test_magic_eden_listing_event(self):
        with open('data/magiceden_listing.json', 'rb') as c:
            transaction_dict = json.load(c)
            timestamp = transaction_dict['blockTime']
        pt = ParsedTransaction.from_transaction_dict(transaction_dict)
        event = await pt.event
        self.assertEqual(
            event,
            SecondaryMarketEvent(
                market_id=SOLANA_MAGIC_EDEN,
                event_type=SECONDARY_MARKET_EVENT_LISTING,
                timestamp=timestamp,
                token_key='rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk',
                price=4000000000,
                owner='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            )
        )

    async def test_magic_eden_unlisting_event(self):
        with open('data/magiceden_unlisting.json', 'rb') as c:
            transaction_dict = json.load(c)
            timestamp = transaction_dict['blockTime']
        pt = ParsedTransaction.from_transaction_dict(transaction_dict)
        event = await pt.event
        self.assertEqual(
            event,
            SecondaryMarketEvent(
                market_id=SOLANA_MAGIC_EDEN,
                event_type=SECONDARY_MARKET_EVENT_UNLISTING,
                timestamp=timestamp,
                token_key='rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk',
                price=0,
                owner='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
            )
        )

    async def test_magic_eden_sale_event(self):
        with open('data/magiceden_sale.json', 'rb') as c:
            transaction_dict = json.load(c)
            timestamp = transaction_dict['blockTime']
        pt = ParsedTransaction.from_transaction_dict(transaction_dict)
        event = await pt.event
        self.assertEqual(
            event,
            SecondaryMarketEvent(
                market_id=SOLANA_MAGIC_EDEN,
                event_type=SECONDARY_MARKET_EVENT_SALE,
                timestamp=timestamp,
                token_key='8ag4raw8snR6GbM6znQYv9k4845zs5NYrDZdoxnxaNwK',
                price=10000000000,
                buyer='BXxoKHT6CYtRTboZDaJee1ahrHoQSN6RJk3HAKpUWGHa',
            )
        )