import unittest

import orjson

from app.blockchains import (
    solana
)


class CollectionFetchingTestCase(unittest.IsolatedAsyncioTestCase):

    @unittest.skip(reason="RPC servers timing out at 60 seconds.")
    def test_get_pandas_collection(self):
        update_authority = 'E6n7aXKC9cJYMLfT1P3GvcdPVQLZZ8g6dUt61GyFM7i4'
        # candy_machine = '2CEU6XpuX5kb2anKzrwvtahZ7t71EWhtStFA9V1XRkE3'
        pdas = solana.nft_get_collection_nfts(
            update_authority
        )
        nft_meta_list = [solana.nft_get_metadata(pda) for pda in pdas]
        with open("pandas.json", 'wb') as c:
            c.write(orjson.dumps(nft_meta_list, option=orjson.OPT_INDENT_2))

    @unittest.skip(reason="RPC servers timing out at 60 seconds.")
    def test_nft_get_metadata_by_token_key(self):
        print(solana.nft_get_metadata_by_token_key('Hzw9pp9WXDKjZ1mczjqGdVzfkKehUjrBP9d6QeRSs2rA'))
