import unittest

import orjson
from solana.rpc.api import Client

from app import settings
from app.blockchains import solana


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

    async def test_magic_eden_transactions(self):
        client = Client(settings.SOLANA_RPC_ENDPOINT)
        resp = client.get_confirmed_signature_for_address2("BoBpB1xnnBbo9fJBpkirVFvKPdxuLtf7u8W3K1n9q5zv")
        print(resp)