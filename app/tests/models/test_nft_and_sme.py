import os.path
import unittest

import dacite
import moto
import boto3
import orjson

from app.models import SMERepository, SecondaryMarketEvent, NftData
from .shared import create_tables
from app import settings

data_path = os.path.join(os.path.dirname(__file__), 'data')


class SMESaveTestCase(unittest.TestCase):

    @classmethod
    def load_sme_and_nft_data_list_from_file(cls, blockchain, filename):
        """
        Loads a list of (sme, nft_data) pair from a json file.
        Args:
            blockchain:
            filename:

        Returns:

        """
        p = os.path.join(data_path, blockchain, filename)
        ret = []
        with open(p, 'r') as fd:
            data = orjson.loads(fd.read())
            for (p1, p2) in data:
                ret.append(
                    (
                        dacite.from_dict(data_class=SecondaryMarketEvent, data=p1),
                        dacite.from_dict(data_class=NftData, data=p2)
                    )
                )
        return ret

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

    def tearDown(self) -> None:
        self.mock_dynamo.stop()

    def test_save_sme_and_nft_events_solana(self):
        sme_and_nft_data_list = self.load_sme_and_nft_data_list_from_file(
            'solana',
            'sme_nft_01.json'
        )
        count, failed = self.sme_repo.save_sme_with_nft_batch(
            sme_and_nft_data_list
        )
        table = self.resource.Table(settings.DYNAMODB_SME_TABLE)
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
