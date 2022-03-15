import asyncio
import time
import unittest
import uuid
import moto
import boto3


from app.indexers.solana import sme_indexer
from app.models.shared import meta
from app.tests.shared import create_tables
from app.utils import setup_logging
from app.utils.streamer import KinesisStreamRecord

setup_logging()


class ConsumerTestCase(unittest.TestCase):
    transaction_hashes = [
        '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',
    ]

    def setUp(self) -> None:
        self.mock_dynamo = moto.mock_dynamodb2()
        self.mock_dynamo.start()
        self.resource = boto3.resource(
            'dynamodb',
        )
        self.client = self.resource.meta.client
        create_tables(self.client)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.stop()
        self.loop.close()
        self.mock_dynamo.stop()

    def generate_kinesis_record_inputs(self, transaction_hashes):
        records = []
        for t in transaction_hashes:
            records.append(
                KinesisStreamRecord(
                    partition_key=uuid.uuid1(),
                    data=(t, 0),
                    timestamp=time.time(),
                    sequence_number=1
                )
            )
        return records

    def test_indexer_consumer(self):
        input_records = self.generate_kinesis_record_inputs(self.transaction_hashes)
        self.loop.run_until_complete(
            sme_indexer.handle_transactions(
                input_records,
                self.loop,
                self.resource
            )
        )
        # Should be done within 30 seconds.
        # Read back from dynamo
        sme_table = self.resource.Table(meta.DTSmeMeta.NAME)
        resp = sme_table.scan(
            ProjectionExpression="",
            ConsistentRead=True,
        )
        readback_smes = resp['Items']
        read_back_transaction_ids = {
            r['sme_id'].rsplit('#', 1)[-1] for r in readback_smes
        }
        nft_table = self.resource.Table(meta.DTNftMeta.NAME)
        resp = nft_table.scan(
            ProjectionExpression="",
            ConsistentRead=True,
        )
        readback_nfts = [n for n in resp['Items'] if n['pk'].startswith('bn') and n['sk'] == 'n']
        read_back_nft_ids = {
            r['pk'].rsplit('#', 1)[-1] for r in readback_nfts
        }
        self.assertSetEqual(set(self.transaction_hashes), read_back_transaction_ids)
