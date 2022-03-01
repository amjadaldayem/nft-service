import datetime
import functools
from unittest import mock

import pytz
from starlette.testclient import TestClient

from app.models import SMERepository, NFTRepository
from app.tests.mixins import JsonRpcTestMixin, BaseTestCase
from app.tests.shared import load_sme_and_nft_data_list_from_file
from app.web import services
from app.web.api import app


class FeedAPITestCase(JsonRpcTestMixin, BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        sme_and_nft_data_list = load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_02.json'
        )

        cls.email = 'jeff@example.com'
        cls.nickname = 'jeff'
        cls.password = '123456'
        cls.user = services.user_service.sign_up(
            email=cls.email,
            nickname=cls.nickname,
            password=cls.password
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
        cls.latest_dt = datetime.datetime.fromtimestamp(latest_ts, tz=pytz.utc)
        cls.oldest_dt = datetime.datetime.fromtimestamp(oldest_ts, tz=pytz.utc)
        cls.latest_ts = latest_ts
        cls.oldest_ts = oldest_ts

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.rpc = functools.partial(
            self.jsonrpc,
            self.client,
            path='/v1/rpc'
        )
        self._rpc = functools.partial(
            self.jsonrpc,
            self.client,
            path='/v1/_rpc'
        )

    def test_query_latest_public(self):
        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.latest_ts
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={}
            )
            self.assertFalse(err)
            self.assertEqual(len(result), 2)
            self.assertListEqual(
                result,
                [
                    {
                        'tokenKey': '9DA8FjMqV1jxznVAV3SBKqkMHxh3RyorBTJAFqRvT4SV',
                        'thumbnailUrl': 'https://arweave.net/CZV-Djosta22IzziOuLgdWOfyIaUMtrRqDCF3LNKtJM',
                        'mediaUrl': 'https://arweave.net/CZV-Djosta22IzziOuLgdWOfyIaUMtrRqDCF3LNKtJM',
                        'name': 'Mutant Doodle Apes #8256',
                        'nftId': 'bn#65536#9DA8FjMqV1jxznVAV3SBKqkMHxh3RyorBTJAFqRvT4SV',
                        'collectionId': 'bc#65536#8GwuM2Ax188oZ26SAiHNC6n5fZR9DkKsUCTbLpN6Zt9f',
                        'market': {'name': 'Solsea',
                                   'url': 'https://solsea.io/nft/9DA8FjMqV1jxznVAV3SBKqkMHxh3RyorBTJAFqRvT4SV'},
                        'buyer': {'name': '8e4TgoZq6pyjQze9goeuWujmXmRYf6zLhKY7bxpAioTn',
                                  'url': 'https://solscan.io/account/8e4TgoZq6pyjQze9goeuWujmXmRYf6zLhKY7bxpAioTn'},
                        'owner': {'name': '', 'url': ''}, 'price': '0.14', 'event': 'Sold', 'timestamp': 1645937474,
                        'blockchainId': 65536,
                        'transactionHash': 'oB3LDdMHuWjHxV4n3QotRtaj55RAK1xwU47P2beBNRxsj29pVugnTRaAFBcgu6oRbMtrasoLLYbfV1gkAbxuNM2',
                        'bookmarked': False
                    },
                    {
                        'tokenKey': 'AoPoZCsVZufPYBQFzYp6sesp4Yjf4FKLuiCdF75RJLNx',
                        'thumbnailUrl': 'https://www.arweave.net/dVmp2V5RmOKd-tv4D9thH5hm_iDXbNiZrMEMnHWuNok?ext=png',
                        'mediaUrl': 'https://www.arweave.net/dVmp2V5RmOKd-tv4D9thH5hm_iDXbNiZrMEMnHWuNok?ext=png',
                        'name': 'SKYLINE #3323',
                        'nftId': 'bn#65536#AoPoZCsVZufPYBQFzYp6sesp4Yjf4FKLuiCdF75RJLNx',
                        'collectionId': 'bc#65536#skyxstP4JfVoAuuGUkPC6M25hoQiafcZ8dUvsoBNmuY',
                        'market': {'name': 'Solanart',
                                   'url': 'https://solanart.io/nft/AoPoZCsVZufPYBQFzYp6sesp4Yjf4FKLuiCdF75RJLNx'},
                        'buyer': {'name': '', 'url': ''},
                        'owner': {'name': 'AYfUa1MUjjivuDKDuXhY5rHCaDBvyAQrNh3XD6bYX8Ty',
                                  'url': 'https://solscan.io/account/AYfUa1MUjjivuDKDuXhY5rHCaDBvyAQrNh3XD6bYX8Ty'},
                        'price': '0.19', 'event': 'Price Updated', 'timestamp': 1645937464,
                        'blockchainId': 65536,
                        'transactionHash': '4QfNqyEuAJJ2ppoGLiCT3Z38V3dQLSX33htERPojsL3Hcv1dhjJG4C9CEY5Xht67KqeFVo1KgP9U4XjZc3XbmngP',
                        'bookmarked': False
                    }
                ]
            )
