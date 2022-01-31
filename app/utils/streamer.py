import logging
from typing import List, Mapping, Union

import boto3
import orjson

from app.utils import full_stacktrace

logger = logging.getLogger(__name__)


class KinesisStreamer:

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
