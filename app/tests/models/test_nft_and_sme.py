import unittest
from collections import Counter

import boto3
import moto
from boto3.dynamodb.conditions import Key, Attr

from app.models import (
    SMERepository,
    NFTRepository,
    meta, SecondaryMarketEvent,
)
from ..shared import create_tables, load_sme_and_nft_data_list_from_file
from ...blockchains import SOLANA_MAGIC_EDEN, SOLANA_SOLANART, SOLANA_SOLSEA


class SMESaveTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_dynamo = moto.mock_dynamodb2()
        self.mock_dynamo.start()

        self.resource = boto3.resource(
            'dynamodb',
            # endpoint_url=settings.DYNAMODB_ENDPOINT
        )
        self.client = self.resource.meta.client
        create_tables(self.client)
        self.sme_repo = SMERepository(
            self.resource,
        )
        self.nft_repo = NFTRepository(
            self.resource
        )

    def tearDown(self) -> None:
        self.mock_dynamo.stop()

    def test_save_sme_and_nft_events_solana(self):
        sme_and_nft_data_list = load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_01.json'
        )
        count, failed = self.sme_repo.save_sme_with_nft_batch(
            sme_and_nft_data_list
        )
        self._assert_smes_success(
            sme_and_nft_data_list, count, failed
        )

    def test_save_sme_and_nft_events_solana_dupes(self):
        sme_and_nft_data_list = load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_01.json'
        )
        count, failed = self.sme_repo.save_sme_with_nft_batch(
            sme_and_nft_data_list
        )
        self._assert_smes_success(sme_and_nft_data_list, count, failed)
        # Redo the saving
        count2, failed2 = self.sme_repo.save_sme_with_nft_batch(
            sme_and_nft_data_list
        )
        self.assertFalse(count2)
        # Dupe entries not saved nor get populated to `failed` list.
        self.assertFalse(failed2)
        # The orignial count and failed should hold.
        self._assert_smes_success(sme_and_nft_data_list, count, failed)

    def test_save_nft_data_solana(self):
        sme_and_nft_data_list = load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_01.json'
        )
        _, nft_data_list = zip(*sme_and_nft_data_list)

        count, failed = self.nft_repo.save_nfts(nft_data_list)
        self._assert_nfts_success(nft_data_list, count, failed)

    def test_save_nft_data_solana_dupes(self):
        sme_and_nft_data_list = load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_01.json'
        )
        _, nft_data_list = zip(*sme_and_nft_data_list)

        count, failed = self.nft_repo.save_nfts(nft_data_list)
        self._assert_nfts_success(nft_data_list, count, failed)
        # Again
        count2, failed2 = self.nft_repo.save_nfts(nft_data_list)
        self.assertFalse(count2)
        self.assertFalse(failed2)
        self._assert_nfts_success(nft_data_list, count, failed)

    def _assert_smes_success(self, sme_and_nft_data_list, count, failed):
        """
        `count` and `failed` are from the result from

        count, failed = self.sme_repo.save_sme_with_nft_batch(
            sme_and_nft_data_list
        )

        Args:
            sme_and_nft_data_list:
            count:
            failed:

        Returns:

        """
        table = self.resource.Table(meta.DTSmeMeta.NAME)
        resp = table.scan(
            ProjectionExpression="",
            ConsistentRead=True,
        )
        sme_ids = {
            sme.sme_id for sme, _ in sme_and_nft_data_list
        }
        read_back_sme_ids = {
            r['sme_id'] for r in resp['Items']
        }
        self.assertEqual(count, len(read_back_sme_ids))
        self.assertSetEqual(sme_ids, read_back_sme_ids)
        self.assertFalse(failed)

    def _assert_nfts_success(self, nft_data_list, count, failed):
        """
        Assume that the NFTs in the list appears in chronological order
        where a "current_owner" appeared later in the list will replace
        the previous one for the same NFT (yes, there can be dupes).
        As this nft_data_list, should be extracted from `sme_and_nft_data_list`

        Args:
            nft_data_list:
            count:
            failed:

        Returns:

        """
        # Get the number of unique NFTs in the list
        unique_nft_ids = {
            nft_data.nft_id for nft_data in nft_data_list
        }
        initial_counter = Counter()
        all_qfis = []
        seen = set()
        for nft_data in nft_data_list:
            qfi = self.nft_repo.get_qfi(nft_data)
            if qfi:
                cn = nft_data.collection_name
                if cn not in seen:
                    initial = cn[0].lower()
                    initial_counter[initial] += 1
                    all_qfis.append(qfi)
                    seen.add(cn)

        # Gets the NFT -> owner mapping
        owners = {}
        for nft_data in nft_data_list:  # nft_data_list is in chronological order
            owners[nft_data.nft_id] = nft_data.current_owner_id

        self.assertFalse(failed)
        self.assertEqual(count, len(unique_nft_ids))

        table = self.resource.Table(meta.DTNftMeta.NAME)
        # Scan for NFT items (with 'n')
        resp = table.scan(
            ProjectionExpression="pk,sk,collection_id",
            ConsistentRead=True,
            FilterExpression=Attr(meta.DTNftMeta.SK).eq('n')
        )
        read_back_nft_ids = {
            r['pk'] for r in resp['Items']
        }
        self.assertSetEqual(read_back_nft_ids, unique_nft_ids)
        # Query the count for qfi items
        for c in 'abcvxz0':
            k = f"qfi#{c}"
            resp = table.query(
                KeyConditionExpression=Key(meta.DTNftMeta.PK).eq(k),
                ConsistentRead=True,
            )
            count = resp['Count']
            self.assertEqual(count, initial_counter[c])

        # Checks the owner
        resp = table.scan(
            ConsistentRead=True,
            FilterExpression=Attr(meta.DTNftMeta.SK).eq('co')
        )
        read_back_owners = {
            # nft_id -> current_owner_id
            i['pk']: i['current_owner_id']
            for i in resp['Items']
        }
        self.assertDictEqual(
            read_back_owners,
            owners
        )


class SMEGetTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.mock_dynamo = moto.mock_dynamodb2()
        cls.mock_dynamo.start()

        cls.resource = boto3.resource(
            'dynamodb',
            # endpoint_url=settings.DYNAMODB_ENDPOINT
        )
        cls.client = cls.resource.meta.client
        create_tables(cls.client)
        cls.sme_repo = SMERepository(
            cls.resource,
        )
        cls.nft_repo = NFTRepository(
            cls.resource
        )
        cls.sme_and_nft_data_list = load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_02.json'
        )
        cls.sme_repo.save_sme_with_nft_batch(
            cls.sme_and_nft_data_list
        )
        # Get time range (newest, oldest) from the loaded events.
        latest_ts = -1
        oldest_ts = 99999999999999999
        for sme, _ in cls.sme_and_nft_data_list:
            if sme.timestamp > latest_ts:
                latest_ts = sme.timestamp
            if sme.timestamp < oldest_ts:
                oldest_ts = sme.timestamp
        cls.latest_ts = latest_ts
        cls.oldest_ts = oldest_ts

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mock_dynamo.stop()

    def test_query_all_events_in_time_window(self):
        w = SecondaryMarketEvent.get_time_window_key(self.latest_ts)
        items = self.sme_repo.get_smes_in_time_window(
            w,
        )
        items_in_latest_window = [
            item for item in self.sme_and_nft_data_list
            if SecondaryMarketEvent.get_time_window_key(item[0].timestamp) == w
        ]
        items_in_latest_window.sort(key=lambda o: SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(
            o[0].timestamp, o[0].blockchain_id, o[0].transaction_hash
        ))
        self.assertEqual(len(items), len(items_in_latest_window))

    def test_query_events_in_time_window_after_tbt(self):
        # Picked the 4th transaction
        tbt_lb = "tbt#1645937421#65536#25G6yuKhkZmF1SrqGr5eMYVH1Eeo6zh1i5uxdDZ67Uyep3aiUBkHSuGFTKfQ2fBD153eQkTrTAfhER9zubb38A94"

        w = SecondaryMarketEvent.get_time_window_key(self.latest_ts)
        items = self.sme_repo.get_smes_in_time_window(
            w,
            tbt_lb=tbt_lb,
        )
        items_in_latest_window_after_tbt = [
            item for item in self.sme_and_nft_data_list
            if SecondaryMarketEvent.get_time_window_key(item[0].timestamp) == w
               and item[0].tbt > tbt_lb
        ]
        items_in_latest_window_after_tbt.sort(
            key=lambda o: SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(
                o[0].timestamp, o[0].blockchain_id, o[0].transaction_hash
            ))
        self.assertEqual(len(items), len(items_in_latest_window_after_tbt))

    def test_query_events_in_time_window_before_tbt(self):
        # Picked the 4th transaction
        tbt_ub = "tbt#1645937421#65536#25G6yuKhkZmF1SrqGr5eMYVH1Eeo6zh1i5uxdDZ67Uyep3aiUBkHSuGFTKfQ2fBD153eQkTrTAfhER9zubb38A94"

        w = SecondaryMarketEvent.get_time_window_key(self.latest_ts)
        items = self.sme_repo.get_smes_in_time_window(
            w,
            tbt_ub=tbt_ub,
        )
        items_in_latest_window_before_tbt = [
            item for item in self.sme_and_nft_data_list
            if SecondaryMarketEvent.get_time_window_key(item[0].timestamp) == w
               and item[0].tbt < tbt_ub
        ]
        items_in_latest_window_before_tbt.sort(
            key=lambda o: SecondaryMarketEvent.get_timestamp_blockchain_transaction_key(
                o[0].timestamp, o[0].blockchain_id, o[0].transaction_hash
            ))
        self.assertEqual(len(items), len(items_in_latest_window_before_tbt))

    def test_query_events_in_time_window_between_tbt_one(self):
        # Picked the 4th transaction
        tbt_ub = "tbt#1645937421#65536#25G6yuKhkZmF1SrqGr5eMYVH1Eeo6zh1i5uxdDZ67Uyep3aiUBkHSuGFTKfQ2fBD153eQkTrTAfhER9zubb38A94"
        tbt_lb = "tbt#1645937421#65536#25G6yuKhkZmF1SrqGr5eMYVH1Eeo6zh1i5uxdDZ67Uyep3aiUBkHSuGFTKfQ2fBD153eQkTrTAfhER9zubb38A94"

        w = SecondaryMarketEvent.get_time_window_key(self.latest_ts)
        items = self.sme_repo.get_smes_in_time_window(
            w,
            tbt_lb=tbt_lb,
            tbt_ub=tbt_ub,
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['tbt'], tbt_lb)

    def test_query_events_in_time_window_between_tbt_three(self):
        # Picked the 4th transaction
        tbt_ub = "tbt#1645937464#65536#4QfNqyEuAJJ2ppoGLiCT3Z38V3dQLSX33htERPojsL3Hcv1dhjJG4C9CEY5Xht67KqeFVo1KgP9U4XjZc3XbmngP"
        tbt_lb = "tbt#1645937421#65536#25G6yuKhkZmF1SrqGr5eMYVH1Eeo6zh1i5uxdDZ67Uyep3aiUBkHSuGFTKfQ2fBD153eQkTrTAfhER9zubb38A94"

        w = SecondaryMarketEvent.get_time_window_key(self.latest_ts)
        items = self.sme_repo.get_smes_in_time_window(
            w,
            tbt_lb=tbt_lb,
            tbt_ub=tbt_ub,
        )
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]['tbt'], tbt_ub)
        self.assertEqual(items[-1]['tbt'], tbt_lb)

    def test_query_events_in_time_window_filter_market_id(self):
        w = SecondaryMarketEvent.get_time_window_key(self.latest_ts)
        # Let's find out only Solanart ones
        items = self.sme_repo.get_smes_in_time_window(
            w,
            filter_expression=Attr('market_id').eq(SOLANA_SOLANART)
        )
        items_in_latest_window_filtered = [
            item for item in self.sme_and_nft_data_list
            if SecondaryMarketEvent.get_time_window_key(item[0].timestamp) == w
               and item[0].market_id == SOLANA_SOLANART
        ]
        self.assertEqual(len(items), len(items_in_latest_window_filtered))
        # Only MagicEden ones
        items = self.sme_repo.get_smes_in_time_window(
            w,
            filter_expression=Attr('market_id').eq(SOLANA_MAGIC_EDEN)
        )
        items_in_latest_window_filtered = [
            item for item in self.sme_and_nft_data_list
            if SecondaryMarketEvent.get_time_window_key(item[0].timestamp) == w
               and item[0].market_id == SOLANA_MAGIC_EDEN
        ]
        self.assertEqual(len(items), len(items_in_latest_window_filtered))
        # None MagicEden ones
        items = self.sme_repo.get_smes_in_time_window(
            w,
            filter_expression=Attr('market_id').ne(SOLANA_MAGIC_EDEN)
        )
        items_in_latest_window_filtered = [
            item for item in self.sme_and_nft_data_list
            if SecondaryMarketEvent.get_time_window_key(item[0].timestamp) == w
               and item[0].market_id != SOLANA_MAGIC_EDEN
        ]
        self.assertEqual(len(items), len(items_in_latest_window_filtered))

    def test_query_events_in_time_window_filter_market_id_combo(self):
        w = SecondaryMarketEvent.get_time_window_key(self.latest_ts)
        # Let's find out only Solanart and Solsea ones
        items = self.sme_repo.get_smes_in_time_window(
            w,
            filter_expression=Attr('market_id').is_in(
                [SOLANA_SOLANART, SOLANA_SOLSEA]
            )

        )
        items_in_latest_window_filtered = [
            item for item in self.sme_and_nft_data_list
            if SecondaryMarketEvent.get_time_window_key(item[0].timestamp) == w
               and item[0].market_id in (SOLANA_SOLANART, SOLANA_SOLSEA)
        ]
        self.assertEqual(len(items), len(items_in_latest_window_filtered))
