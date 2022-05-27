import json
import logging
from typing import Any, List

import boto3

from sintra.config import settings
from sintra.exception import (
    EnvironmentVariableMissingException,
    ProduceRecordFailedException,
)
from sintra.kinesis.record import KinesisRecord

logger = logging.getLogger(__name__)


class KinesisProducer:
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str,
    ) -> None:
        if settings.localstack.active:
            self.client = boto3.client(
                "kinesis",
                region_name=settings.localstack.region,
                endpoint_url=settings.localstack.endpoint,
            )
        else:
            if access_key_id is not None or secret_access_key is not None:
                self.client = boto3.client(
                    "kinesis",
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    region_name=region,
                )
            else:
                raise EnvironmentVariableMissingException("Missing AWS credentials.")

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
