import unittest

import boto3
import moto

from app.utils import streamer


class TestDataStream(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.mock_kinesis = moto.mock_kinesis()
        cls.mock_kinesis.start()
        cls.mock_lambda = moto.mock_lambda()
        cls.mock_lambda.start()

        cls.kinesis = boto3.client('kinesis')
        cls.awslambda = boto3.client('lambda')
        cls.awslambda.create_function(
            FunctionName='Consumer'
        )

        cls.stream_name = 'test-stream'
        cls.region = 'us-west-2'
        cls.data_stream = cls.kinesis.create_stream(
            StreamName=cls.stream_name,
            ShardCount=1,
            StreamModeDetails={
                'StreamMode': 'PROVISIONED'
            }
        )
        cls.producer = streamer.KinesisStreamer(
            cls.stream_name,
            region=cls.region
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mock_lambda.stop()
        cls.mock_kinesis.stop()
