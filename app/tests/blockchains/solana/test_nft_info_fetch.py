import unittest

import orjson

from app.blockchains import (
    solana
)


class CollectionFetchingTestCase(unittest.IsolatedAsyncioTestCase):

    @unittest.skip(reason="Temp")
    def test_get_collection_accounts(self):
        update_authority = 'E6n7aXKC9cJYMLfT1P3GvcdPVQLZZ8g6dUt61GyFM7i4'
        # update_authority = 'ByuUyvzDF6LyAJsBDxd9HuD2wmkbGc2hdam3Z7Ku45Hp'
        # update_authority = 'ByuUyvzDF6LyAJsBDxd9HuD2wmkbGc2hdam3Z7Ku45Hp'
        pdas = solana.nft_get_collection_pdas(
            update_authority
        )
        nft_meta_list = [solana.nft_get_metadata(pda) for pda in pdas]
        with open("pandas.json", 'wb') as c:
            c.write(orjson.dumps(nft_meta_list, option=orjson.OPT_INDENT_2))

    @unittest.skip(reason="1")
    def test_nft_get_metadata_by_pda_key(self):
        print(solana.nft_get_metadata_by_pda_key('6yyBTAQSR5x6yyWHtLACF63BbZ4LwPYoxMsmEnn1erjb'))

    @unittest.skip(reason="2")
    def test_nft_get_metadata_by_token_key(self):
        print(solana.nft_get_metadata_by_token_key('Vdax9bbGgrtDqprCPXZ2dDgcTGZxhGUaUgTRMqGVYm6'))
