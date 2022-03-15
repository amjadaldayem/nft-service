import asyncio
import logging
import time
import uuid
from collections import namedtuple
from typing import List, Mapping, Union, Callable, Any, Coroutine

import boto3
import multiprocess as mp
import orjson
import pybase64 as base64

from app.utils import full_stacktrace

logger = logging.getLogger(__name__)

KinesisStreamRecord = namedtuple(
    'KinesisStreamRecord',
    ["partition_key", "data", "timestamp", "sequence_number"]
)

END_MARKER = '_EnD_983RRd73s652f__'


def _poller(q, handler):
    loop = asyncio.new_event_loop()
    while True:
        try:
            event = q.get(True, 1)
        except mp.queues.Empty:
            continue
        if event == END_MARKER:
            break
        handler(event, None, loop)


def _setup_local_consumer_poller(q, handler):
    p = mp.Process(target=_poller, args=(q, handler), daemon=True)
    p.start()
    return p


def _lambda_wrapper(coro, event, loop):
    """
    Logic for parsing Lambda event and invoking Async handler
    Args:
        coro:
        event:
        loop:

    Returns:

    """
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
                data=orjson.loads(base64.urlsafe_b64decode(t['data'])),
                timestamp=t['approximateArrivalTimestamp'],
                sequence_number=t['sequenceNumber']
            )
        )
    failed_records = loop.run_until_complete(
        coro(transformed, loop)
    )
    if failed_records:
        return {
            "batchItemFailures": [
                {"itemIdentifier": failed_record.sequence_number}
                for failed_record in failed_records
            ]
        }
    else:
        return {"batchItemFailures": []}


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

    PRODUCER_NORMAL = 0
    PRODUCER_LOG_ONLY = 1
    PRODUCER_LOCAL_CONSUMER = 2

    def __init__(self, stream_name, region, endpoint_url=None, producer_mode=0, handler=None):
        """

        Args:
            stream_name:
            region:
            endpoint_url:
            producer_mode: What level the Streamer Producer works on.
                0 - For normal Kinesis Producer
                1 - Only logs to console the produced data
                2 - Locally simulates Lambda invocation to invoke the consumer.
            handler: Consumer function that follows the Lambda Kinesis contract
                to receive messages for local run. Only meaningful when producer_mode = 2.
        """
        self.stream_name = stream_name
        self.region = region
        if producer_mode == self.PRODUCER_LOCAL_CONSUMER:
            # Use local handler directly (if one is wrapped)
            logger.info("Using local consumer.")
            self.put = self._put_local_handler
            self.queue = mp.Queue()
            self.poller = _setup_local_consumer_poller(self.queue, handler)
            # def signal_handler(sig, frame):
            #     self.kill_local_poller()
            #
            # for s in (signal.SIGINT, signal.SIGTERM):
            #     signal.signal(s, signal_handler)

        elif producer_mode == self.PRODUCER_LOG_ONLY:
            self.put = self._put_log
        else:
            # Pushes transaction hashes to Kinesis DataStream
            # and let consumer handle them
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

    def kill_local_poller(self):
        if hasattr(self, 'queue'):
            q = self.queue
            while True:
                # Exhausts the queue, best effort
                try:
                    q.get_nowait()
                except mp.queues.Empty:
                    break
            q.put_nowait(END_MARKER)
            if self.poller.is_alive():
                self.poller.join()

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

    def _put_local_handler(self, records: List[Union[Mapping, str]]) -> List[Mapping]:
        if hasattr(self, 'queue'):
            if not hasattr(self, '_current_batch'):
                self._current_batch = []

            records = [
                {
                    'kinesis': {
                        'partitionKey': uuid.uuid1(),
                        'data': base64.urlsafe_b64encode(orjson.dumps(record)),
                        'approximateArrivalTimestamp': time.time(),
                        'sequenceNumber': i
                    }
                } for i, record in enumerate(records)
            ]
            self._current_batch.extend(records)
            # Batched every 30 events: note might be starving if events number too low
            # but this is only for local testing
            if len(self._current_batch) == 30:
                evt = {
                    'Records': self._current_batch
                }
                self.queue.put_nowait(evt)
                self._current_batch = []

    @classmethod
    def wrap_local_handler(cls,
                           coro: Coroutine[List[KinesisStreamRecord], Any, KinesisStreamRecord],
                           ) -> Callable[[Mapping, Mapping, asyncio.BaseEventLoop], Mapping]:
        """

        Args:
            coro:

        Returns:
            a function handler(event, context, loop) for local consumer
        """

        def _handler(event, context, loop):
            return _lambda_wrapper(coro, event, loop)

        return _handler

    @classmethod
    def wrap_handler(cls,
                     coro: Coroutine[List[KinesisStreamRecord], Any, Any]
                     ) -> Callable[[Mapping, Mapping], Mapping]:
        """
        Wraps a callable to get the Handler the conforms with Lambda Input for
        Kinesis data stream.

        The callable returns None if the batch processing succeeds; otherwise,
        return the first failed KinesisStreamRecord, and it will bisect the records
        and only retry the failed ones next.

        Args:
            coro:

        Returns:
            a function handler(event, context) that meets Lambda contract
        """
        loop = asyncio.new_event_loop()

        def _handler(event, context):
            return _lambda_wrapper(coro, event, loop)

        return _handler
