import json
import logging
from typing import Any, Dict, List

import boto3
from src.exception import (
    EnvironmentVariableMissingException,
    ProduceRecordFailedException,
)
from src.model import SecondaryMarketEvent

logger = logging.getLogger(__name__)


class KinesisProducer:
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str,
        localstack_active: bool
    ) -> None:
        if localstack_active:
            if access_key_id is None or secret_access_key is None:
                raise EnvironmentVariableMissingException("Missing AWS credentials.")

            self.client = boto3.client(
                "kinesis",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
            )
        else:
            self.client = boto3.client("kinesis")

    def produce_record(
        self, stream_name: str, record: SecondaryMarketEvent, partition_key: Any
    ) -> None:
        record_dikt: str = json.dumps(record.to_dict())
        record_to_send = record_dikt.encode()

        try:
            self.client.put_record(
                StreamName=stream_name, Data=record_to_send, PartitionKey=partition_key
            )
        except Exception as error:
            logger.error(error)
            raise ProduceRecordFailedException from error

    def produce_records(
        self, stream_name: str, records: List[SecondaryMarketEvent]
    ) -> None:
        records_to_send: List[Dict[str, Any]] = [
            {
                "Data": json.dumps(record.to_dict()).encode(),
                "PartitionKey": record.transaction_hash,
            }
            for record in records
        ]

        self.client.put_records(StreamName=stream_name, Records=records_to_send)
