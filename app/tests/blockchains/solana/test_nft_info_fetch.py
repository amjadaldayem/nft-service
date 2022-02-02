import unittest

import orjson

from app.blockchains import (
    solana
)


class CollectionFetchingTestCase(unittest.IsolatedAsyncioTestCase):

    def test_get_all_mints(self):
        # 2CEU6XpuX5kb2anKzrwvtahZ7t71EWhtStFA9V1XRkE3
        # Get Candy machine
        pass

    # @unittest.skip(reason="Temp")
    # def test_get_pandas_collection(self):
    #     update_authority = 'E6n7aXKC9cJYMLfT1P3GvcdPVQLZZ8g6dUt61GyFM7i4'
    #     # candy_machine = '2CEU6XpuX5kb2anKzrwvtahZ7t71EWhtStFA9V1XRkE3'
    #     pdas = solana.nft_get_collection_mint_addresses(
    #         update_authority
    #     )
    #     nft_meta_list = [solana.nft_get_metadata(pda) for pda in pdas]
    #     with open("pandas.json", 'wb') as c:
    #         c.write(orjson.dumps(nft_meta_list, option=orjson.OPT_INDENT_2))

    # def test_get_pesk_penguines_collection(self):
    #     update_authority = 'pEsKYABNARLiDFYrjbjHDieD5h6gHrvYf9Vru62NX9k'
    #     pdas = solana.nft_get_collection_pdas(
    #         update_authority
    #     )
    #     nft_meta_list = [solana.nft_get_metadata(pda) for pda in pdas]
    #     with open("pesky.json", 'wb') as c:
    #         c.write(orjson.dumps(nft_meta_list, option=orjson.OPT_INDENT_2))
    #
    # def test_nft_get_metadata_by_pda_key(self):
    #     print(solana.nft_get_metadata_by_pda_key('6yyBTAQSR5x6yyWHtLACF63BbZ4LwPYoxMsmEnn1erjb'))
    #
    # def test_nft_get_metadata_by_token_key(self):
    #     print(solana.nft_get_metadata_by_token_key('Vdax9bbGgrtDqprCPXZ2dDgcTGZxhGUaUgTRMqGVYm6'))
