import datetime
import functools
from unittest import mock

import pytz
from starlette.testclient import TestClient

from app import settings
from app.models import SMERepository, NFTRepository, SecondaryMarketEvent
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
        cls.sme_list, nft_data_list = zip(*sme_and_nft_data_list)
        cls.nft_repo.save_nfts(
            list(nft_data_list)
        )
        # Get time range (newest, oldest) from the loaded events.
        latest_ts = -1
        oldest_ts = 99999999999999999
        for sme in cls.sme_list:
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
        expected = [
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
            },

        ]

        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.latest_ts
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={
                    'data': {}
                }
            )
            self.assertFalse(err)
            self.assertEqual(len(expected), len(result))
            self.assertListEqual(
                expected,
                result
            )

    def test_query_all_public(self):
        with mock.patch('time.time') as mock_time:
            mock_time.return_value = self.latest_ts
            esk = None
            all_items = []
            while True:
                result, err = self.rpc(
                    method='getSecondaryMarketEvents',
                    params={
                        'data': {
                            "exclusiveStartKey": esk,
                            "timespan": 60
                        }
                    }
                )
                if not result:
                    break
                all_items.extend(result)
                last_item = result[-1]
                esk = (
                    last_item['timestamp'],
                    last_item['blockchainId'],
                    last_item['transactionHash'],
                )
            read = [i['transactionHash'] for i in all_items]
            expected = [
                s.transaction_hash for s in sorted(self.sme_list, key=lambda o: o.tbt, reverse=True)
                if s.timestamp < self.latest_ts - settings.SME_FETCH_DEFAULT_LAG
            ]
            self.assertListEqual(expected, read)

    def test_query_chunk_01_public(self):
        starting_esk = esk = (1645936713, 65536, "K171Q5gFxDjJairJrfWbTQGR66NgLyrcLGNZyVUvww6NL6etD6w8cmrv4EBma2H3v37yVXxkMPN1ANDMEfo36hT")
        etk = (1645936711, 65536, "4qEE7Ez6SdhkNxwX5dwxsqebWuQty9diufpF5bz5MvfGNDkbbtbibVYegWcDADsPa1ZMP4uuFYkbNqkvsnndDYYc")

        all_items = []
        while True:
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={
                    'data': {
                        "exclusiveStartKey": esk,
                        "exclusiveStopKey": etk
                    }
                }
            )
            if not result:
                break
            else:
                last_item = result[-1]
                esk = (last_item['timestamp'], last_item['blockchainId'], last_item['transactionHash'])
                all_items.extend(result)
        read = [i['transactionHash'] for i in all_items]
        starting_esk_s = SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(*starting_esk)
        etk_s = SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(*etk)
        expected = [
            s.transaction_hash for s in sorted(self.sme_list, key=lambda o: o.tbt, reverse=True)
            if starting_esk_s > s.tbt > etk_s
        ]
        self.assertListEqual(expected, read)

    def test_query_chunk_02_public(self):
        starting_esk = esk = (1645936713, 65536, "K171Q5gFxDjJairJrfWbTQGR66NgLyrcLGNZyVUvww6NL6etD6w8cmrv4EBma2H3v37yVXxkMPN1ANDMEfo36hT")
        etk = (1645936716, 65536, "4c3UgmLLTsfxGP85ZdTY6jNRUskVnKDmKwCzhtkMV4UAoJ1otA731RH7nWErHcBsCmWK5bvndCUZtKq5ptr9zU5K")

        all_items = []
        while True:
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={
                    'data': {
                        "exclusiveStartKey": esk,
                        "exclusiveStopKey": etk
                    }
                }
            )
            if not result:
                break
            else:
                last_item = result[-1]
                esk = (last_item['timestamp'], last_item['blockchainId'], last_item['transactionHash'])
                all_items.extend(result)
        read = [i['transactionHash'] for i in all_items]
        starting_esk_s = SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(*starting_esk)
        etk_s = SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(*etk)
        expected = [
            s.transaction_hash for s in sorted(self.sme_list, key=lambda o: o.tbt, reverse=True)
            if starting_esk_s > s.tbt > etk_s
        ]
        self.assertListEqual(expected, read)

    def test_query_chunk_03_public(self):
        # Return none
        esk = (1645936713, 65536, "2cjHFTya76r4BiVxWjW1nUWMoAPGEmhqwuG5rXUt5a9zkADXymNrQJX23vKj2M2g2csrbcS3W2Ggto7ZbBnWivju")
        etk = (1645936713, 65536, "2HrSaT3w9iXkMJDaJQNoKifkxeXHJQa1amQNEFkorah2sYaDbxZQ3MJGKXZzS2WCoLiMqwgSPXrbNVF3HPK4bQVs")

        all_items = []
        while True:
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={
                    'data': {
                        "exclusiveStartKey": esk,
                        "exclusiveStopKey": etk
                    }
                }
            )
            if not result:
                break
            else:
                last_item = result[-1]
                esk = (last_item['timestamp'], last_item['blockchainId'], last_item['transactionHash'])
                all_items.extend(result)
        self.assertFalse(result)
        self.assertFalse(all_items)

    def test_query_chunk_04_public(self):
        # Return very few entry
        esk = (1645936715, 65536, "QShKBVd4FjtKnKEEhxAx98fpWvpF81fx1eNmsDQgVxLD1jT7DA1KiScogfcP3sRenUDSAV6Dh5zxzeXVu27gr5e")
        etk = (1645936713, 65536, "2HrSaT3w9iXkMJDaJQNoKifkxeXHJQa1amQNEFkorah2sYaDbxZQ3MJGKXZzS2WCoLiMqwgSPXrbNVF3HPK4bQVs")
        expected = [
            'PMdycz4BAfnZYcLSZwkTpBa98XADar1verGGQfavWBReEK47c3ESCDEbtSpSxSef5dK3g8yQLH78vqyxYPSXp1h',
            '4D7B5osUVLhBRPfYw2EaB4XWdZbNYFgmqQFRL2rk8PhrLYV9NEQv8HW1T4RLRGsebHMEU6BPx4BBTgwkhkfgJtKu',
            '47U7btHuWJj6nF8D4mveZ7x1wE8ku8X4Xsq1KHBRKeEQEGzz9n85kyMCjdc9fPPda6N8VXvNdEUNKurXGd7BXac',
            '2Ezn9kn6D4CJodDovNZpBy39ZeDGKu1HrvXNFxZcGcj4ixqt4tfNez1kQkZMRgkWdu7HpmwmC1nTd28gH3T6LhBY',
            'K171Q5gFxDjJairJrfWbTQGR66NgLyrcLGNZyVUvww6NL6etD6w8cmrv4EBma2H3v37yVXxkMPN1ANDMEfo36hT',
            '5vQwHStG6ZoeJoVubYa1a1jzACtJW7WHvv7f679mUGvngo8HVqSvYTSnSZBX7MZWRZFt2SavmzD5UmejD1ZAQnCK',
            '3ENAiMz8RRLEoXhhYGXzwR54jU6cfuMRsXhfYTx6ztrZgAMfVp26zrTjJN7hwWUE558hdM63SMycdQEpuVEemAir',
            '2cjHFTya76r4BiVxWjW1nUWMoAPGEmhqwuG5rXUt5a9zkADXymNrQJX23vKj2M2g2csrbcS3W2Ggto7ZbBnWivju',
        ]
        all_items = []
        while True:
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={
                    'data': {
                        "exclusiveStartKey": esk,
                        "exclusiveStopKey": etk
                    }
                }
            )
            if not result:
                break
            else:
                last_item = result[-1]
                esk = (last_item['timestamp'], last_item['blockchainId'], last_item['transactionHash'])
                all_items.extend(result)
        self.assertEqual(expected, [i['transactionHash'] for i in all_items])

    def test_query_chunk_flipped_esk_and_etk_public(self):
        # Return very few entry
        esk = (1645936713, 65536, "2HrSaT3w9iXkMJDaJQNoKifkxeXHJQa1amQNEFkorah2sYaDbxZQ3MJGKXZzS2WCoLiMqwgSPXrbNVF3HPK4bQVs")
        etk = (1645936715, 65536, "QShKBVd4FjtKnKEEhxAx98fpWvpF81fx1eNmsDQgVxLD1jT7DA1KiScogfcP3sRenUDSAV6Dh5zxzeXVu27gr5e")
        all_items = []
        while True:
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={
                    'data': {
                        "exclusiveStartKey": esk,
                        "exclusiveStopKey": etk
                    }
                }
            )
            if not result:
                break
            else:
                last_item = result[-1]
                esk = (last_item['timestamp'], last_item['blockchainId'], last_item['transactionHash'])
                all_items.extend(result)
        self.assertFalse(all_items)

    def test_query_limit_public(self):
        # Starting with this exclusive start key and travelling back
        starting_esk = esk = (1645936735, 65536,
                              '5bh3ApUcotAEUbmxBTQT1YpH7XuFFZYNZFzfCs3YqnRjXsCQFFwJrZwSaUHj7N1mSYz4dkeXVKySXs7wv4nYwER1')

        all_items = []
        while True:
            result, err = self.rpc(
                method='getSecondaryMarketEvents',
                params={
                    'data': {
                        "exclusiveStartKey": esk,
                        "timespan": 360
                    }
                }
            )
            self.assertLessEqual(len(result), settings.SME_FETCH_PAGE_SIZE)
            if not result:
                break
            all_items.extend(result)
            last_item = result[-1]
            esk = (
                last_item['timestamp'],
                last_item['blockchainId'],
                last_item['transactionHash'],
            )
        read = [i['transactionHash'] for i in all_items]
        starting_esk_s = SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(*starting_esk)
        expected = [
            s.transaction_hash for s in sorted(self.sme_list, key=lambda o: o.tbt, reverse=True)
            if s.tbt < starting_esk_s
        ]
        self.assertListEqual(expected, read)

    def test_query_limit_protected(self):
        esk = (1645936735, 65536,
               '5bh3ApUcotAEUbmxBTQT1YpH7XuFFZYNZFzfCs3YqnRjXsCQFFwJrZwSaUHj7N1mSYz4dkeXVKySXs7wv4nYwER1')

        auth, _ = services.user_service.login(
            self.email, self.password
        )

        result, err = self._rpc(
            method='getSecondaryMarketEvents',
            params={
                'data': {
                    "exclusiveStartKey": esk,
                    "timespan": 360,
                    "page_size": 50
                }
            },
            authorization=auth
        )
        read = [i['transactionHash'] for i in result]
        expected = [
            s.transaction_hash for s in sorted(self.sme_list, key=lambda o: o.tbt, reverse=True)
            if 1645936735 > s.timestamp > 1645936375
        ][:50]
        self.assertListEqual(expected, read)
