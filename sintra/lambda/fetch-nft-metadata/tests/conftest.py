import base64
import json
import os
import time
from typing import Any, Dict, Generator

import boto3
import pytest
from moto import mock_kinesis


@pytest.fixture(scope="session")
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="session")
def solana_kinesis_input_event() -> Dict[str, Any]:
    event = {
        "blockchain_id": 65536,
        "market_id": 65660,
        "blocktime": time.time_ns(),
        "timestamp": time.time_ns(),
        "event_type": 1,
        "token_key": "9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        "price": 100,
        "owner": "5AmZM5qY2LZtBMVSTVzyZmUGFCgiMTD9xaRuLF8XF1hK",
        "buyer": "JBjjW3sHsui7jmq1HDftMxqkG83aW6LuDxGuQHQhaomo",
        "transaction_hash": "1eE5Sw16rNVg6Z7xWhiQA7Lijp8DDZ2XGoRGK8GR9fCeCA5CYKib3qpQNVYh25hzUaUxhLguGgtdmSFJG13yRsz",
    }
    event = json.dumps(event)
    event = event.encode()
    event_data = base64.b64encode(event)

    return {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": event_data,
                    "approximateArrivalTimestamp": 1545084650.987,
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-kinesis-role",
                "awsRegion": "eu-central-1",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
            }
        ]
    }


@pytest.fixture(scope="session")
def ethereum_kinesis_input_event() -> Dict[str, Any]:
    event = {
        "blockchain_id": 196608,
        "market_id": 196865,
        "blocktime": time.time_ns(),
        "timestamp": time.time_ns(),
        "event_type": 1,
        "token_key": "0xaf6D892177BBabCD71623f55728eb7bc1E919B8e/15",
        "price": 6500000000000000000,
        "owner": "0x9A3e204bd2f012122B228FA68Bf97539dA965D3b",
        "buyer": "JBjjW3sHsui7jmq1HDftMxqkG83aW6LuDxGuQHQhaomo",
        "transaction_hash": "0x67e68505498206d75c80c545e6832934082439290649ba59f6efde545c23c77a",
    }
    event = json.dumps(event)
    event = event.encode()
    event_data = base64.b64encode(event)

    return {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": event_data,
                    "approximateArrivalTimestamp": 1545084650.987,
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-kinesis-role",
                "awsRegion": "eu-central-1",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
            }
        ]
    }


@pytest.fixture(scope="session")
def solana_kinesis_invalid_input_event() -> Dict[str, Any]:
    event = {
        "blockchain_id": 65536,
        "blocktime": time.time_ns(),
        "timestamp": time.time_ns(),
        "event_type": 1,
        "price": 100,
    }
    event = json.dumps(event)
    event = event.encode()
    event_data = base64.b64encode(event)

    return {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": event_data,
                    "approximateArrivalTimestamp": 1545084650.987,
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-kinesis-role",
                "awsRegion": "eu-central-1",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
            }
        ]
    }


@pytest.fixture(scope="session")
def ethereum_kinesis_invalid_input_event() -> Dict[str, Any]:
    event = {
        "blockchain_id": 196608,
        "blocktime": time.time_ns(),
        "timestamp": time.time_ns(),
        "event_type": 1,
        "price": 100,
    }
    event = json.dumps(event)
    event = event.encode()
    event_data = base64.b64encode(event)

    return {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": event_data,
                    "approximateArrivalTimestamp": 1545084650.987,
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-kinesis-role",
                "awsRegion": "eu-central-1",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
            }
        ]
    }


@pytest.fixture(scope="session")
def kinesis_non_existing_market_input_event() -> Dict[str, Any]:
    event = {
        "blockchain_id": 123456,
        "market_id": 11111,
        "blocktime": time.time_ns(),
        "timestamp": time.time_ns(),
        "event_type": 1,
        "token_key": "9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        "price": 100,
        "owner": "5AmZM5qY2LZtBMVSTVzyZmUGFCgiMTD9xaRuLF8XF1hK",
        "buyer": "JBjjW3sHsui7jmq1HDftMxqkG83aW6LuDxGuQHQhaomo",
        "transaction_hash": "1eE5Sw16rNVg6Z7xWhiQA7Lijp8DDZ2XGoRGK8GR9fCeCA5CYKib3qpQNVYh25hzUaUxhLguGgtdmSFJG13yRsz",
    }
    event = json.dumps(event)
    event = event.encode()
    event_data = base64.b64encode(event)

    return {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                    "data": event_data,
                    "approximateArrivalTimestamp": 1545084650.987,
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-kinesis-role",
                "awsRegion": "eu-central-1",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
            }
        ]
    }


@pytest.fixture(scope="session")
def kinesis_stream_name() -> str:
    return "nft-metadata-stream"


@pytest.fixture(scope="session")
def kinesis_client(aws_credentials) -> Generator[boto3.client, None, None]:
    with mock_kinesis():
        kinesis = boto3.client("kinesis", region_name="us-east-1")
        yield kinesis


@pytest.fixture(scope="session")
def kinesis_nft_metadata_stream(
    kinesis_client: boto3.client, kinesis_stream_name: str
) -> Generator[boto3.client, None, None]:
    kinesis_client.create_stream(
        StreamName=kinesis_stream_name,
        ShardCount=1,
        StreamModeDetails={"StreamMode": "ON_DEMAND"},
    )

    yield

    kinesis_client.delete_stream(
        StreamName=kinesis_stream_name, EnforceConsumerDeletion=True
    )
