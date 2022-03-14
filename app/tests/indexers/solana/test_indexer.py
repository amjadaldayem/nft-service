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
        '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'
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
