import asyncio
import logging
import pybase64 as base64
from collections import namedtuple
from typing import List, Mapping, Union, Callable, Any, Optional, Coroutine

import boto3
import orjson

from app.utils import full_stacktrace

logger = logging.getLogger(__name__)

KinesisStreamRecord = namedtuple(
    'KinesisStreamRecord',
    ["partition_key", "data", "timestamp", "sequence_number"]
)


class KinesisStreamer:
    """

    Input format from Lambda
        {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": "SGVsbG8sIHRoaXMgaXMgYSB0ZXN0Lg==",
                    "approximateArrivalTimestamp": 1545084650.987
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
                "awsRegion": "us-east-2",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
            },
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692540925702759324208523137515618",
                    "data": "VGhpcyBpcyBvbmx5IGEgdGVzdC4=",
                    "approximateArrivalTimestamp": 1545084711.166
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692540925702759324208523137515618",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
                "awsRegion": "us-east-2",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
            }
        ]
    }

    """

    def __init__(self, stream_name, region, endpoint_url=None, dummy=False):
        """

        Args:
            stream_name:
            region:
            endpoint_url:
            dummy: If set, will only log to STDOUT the information instead of
                sending to Kinesis data stream.
        """
        self.stream_name = stream_name
        self.region = region
        if dummy:
            self.put = self._put_log
        else:
            self.put = self._put_kinesis
            self.client = boto3.client('kinesis', endpoint_url=endpoint_url)
            self.waiter = self.client.get_waiter('stream_exists')
            self.waiter.wait(
                StreamName=self.stream_name,
                WaiterConfig={
                    'Delay': 5,
                    'MaxAttempts': 3
                }
            )
        self.loop = asyncio.new_event_loop()

    def _put_log(self, records: List[Union[Mapping, str]]) -> List[Mapping]:
        for record in records:
            logger.info(
                orjson.dumps(
                    {
                        'stream_name': self.stream_name,
                        'record': record
                    }
                )
            )
        return []

    def _put_kinesis(self, records: List[Union[Mapping, str]]) -> List[Mapping]:
        """

        Args:
            records:

        Returns:
            A list of failed records. May need to re-put. Success if empty.
        """
        failed_records = []
        try:
            resp = self.client.put_records(
                Records=[
                    {
                        'Data': orjson.dumps(rec),
                        'PartitionKey': str(i)
                    } for i, rec in enumerate(records)
                ],
                StreamName=self.stream_name
            )
            failed_count = resp['FailedRecordCount']
            if failed_count:
                result_records = resp['Records']
                for i, result_record in enumerate(result_records):
                    if 'ShardId' not in result_record:
                        # TODO: Verify this!
                        failed_records.append(records[i])
        except Exception as e:
            logger.error(str(e))
            logger.error(full_stacktrace())

        return failed_records

    def wrap_handler(self,
                     func: Coroutine[List[KinesisStreamRecord], Any, KinesisStreamRecord]
                     ) -> Callable[[Mapping, Mapping], Mapping]:
        """
        Wraps a callable to get the Handler the conforms with Lambda Input for
        Kinesis data stream.

        The callable returns None if the batch processing succeeds; otherwise,
        return the first failed KinesisStreamRecord, and it will bisect the records
        and only retry the failed ones next.

        Args:
            func:

        Returns:

        """

        def _handler(event, context):
            transformed = []
            for r in event['Records']:
                t = r['kinesis']

                #                     "kinesisSchemaVersion": "1.0",
                #                     "partitionKey": "1",
                #                     "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                #                     "data": "SGVsbG8sIHRoaXMgaXMgYSB0ZXN0Lg==",
                #                     "approximateArrivalTimestamp": 1545084650.987
                transformed.append(
                    KinesisStreamRecord(
                        partition_key=t['partitionKey'],
                        data=base64.urlsafe_b64decode(t['data']),
                        timestamp=t['approximateArrivalTimestamp'],
                        sequence_number=t['sequenceNumber']
                    )
                )
            failed_record = self.loop.run_until_complete(
                func(transformed, self.loop)
            )
            if failed_record:
                return {
                    "batchItemFailures": [
                        {"itemIdentifier": failed_record.sequence_number}
                    ]
                }
            else:
                return {"batchItemFailures": []}

        return _handler
