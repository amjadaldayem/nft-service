import datetime

from app.models import SMERepository, NFTRepository
from app.tests.mixins import JsonRpcTestMixin, BaseTestCase
from app.tests.shared import load_sme_and_nft_data_list_from_file


class FeedAPITestCase(JsonRpcTestMixin, BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        sme_and_nft_data_list = load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_01.json'
        )
        cls.sme_repo = SMERepository(
            cls.dynamodb_resource
        )
        cls.nft_repo = NFTRepository(
            cls.dynamodb_resource
        )
        # Save data in table for queries.
        cls.sme_repo.save_sme_with_nft_batch(
            sme_and_nft_data_list
        )
        sme_list, nft_data_list = zip(*sme_and_nft_data_list)
        cls.nft_repo.save_nfts(
            list(nft_data_list)
        )
        # Get time range (newest, oldest) from the loaded events.
        latest_ts = -1
        oldest_ts = 99999999999999999
        for sme in sme_list:
            if sme.timestamp > latest_ts:
                latest_ts = sme.timestamp
            if sme.timestamp < oldest_ts:
                oldest_ts = sme.timestamp
        cls.latest_dt = datetime.datetime.fromtimestamp(latest_ts)
        cls.oldest_dt = datetime.datetime.fromtimestamp(oldest_ts)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def test_query_latest(self):
        ...
