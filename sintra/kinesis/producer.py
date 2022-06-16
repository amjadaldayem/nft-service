import json
import logging
from typing import Any, List

import boto3

from sintra.config import settings
from sintra.exception import ProduceRecordFailedException
from sintra.kinesis.record import KinesisRecord

logger = logging.getLogger(__name__)


class KinesisProducer:
    def __init__(self) -> None:
        active_var = str(settings.localstack.active).lower()
        active = active_var == "true"

        if active:
            self.client = boto3.client(
                "kinesis",
                region_name=settings.localstack.region,
                endpoint_url=settings.localstack.endpoint,
            )
        else:
            self.client = boto3.client("kinesis")

    def produce_record(
        self, stream_name: str, record: KinesisRecord, partition_key: Any
    ) -> None:
        record_dikt: str = json.dumps(record.to_dikt())
        record_to_send = record_dikt.encode()

        try:
            self.client.put_record(
                StreamName=stream_name, Data=record_to_send, PartitionKey=partition_key
            )
        except Exception as error:
            logger.error(error)
            raise ProduceRecordFailedException from error

    def produce_records(
        self, stream_name: str, records: List[KinesisRecord], partition_key: Any
    ) -> None:
        records_to_send: List[bytes] = [
            json.dumps(record.to_dikt()).encode() for record in records
        ]

        try:
            self.client.put_records(
                StreamName=stream_name, Data=records_to_send, PartitionKey=partition_key
            )
        except Exception as error:
            raise ProduceRecordFailedException from error
