import unittest

import orjson

from app.blockchains import (
    solana
)


class CollectionFetchingTestCase(unittest.IsolatedAsyncioTestCase):

    @unittest.skip(reason="This takes too long to finish. And only works with QuickNode.")
    async def test_get_radrug_collection(self):
        first_creator = "6j4fFSZAETzj1qgFUq7BDdz37muA49tKoWrY7dPduYH2"
        pdas = await solana.nft_get_mint_list(
            first_creator
        )
        nft_meta_list = [solana.nft_get_metadata(pda) for pda in pdas]
        with open("azure_dao (rug).json", 'wb') as c:
            c.write(orjson.dumps(nft_meta_list, option=orjson.OPT_INDENT_2))

