# pylint: disable=redefined-outer-name

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
def kinesis_stream_name() -> str:
    return "nft-data-stream"


@pytest.fixture(scope="session")
def kinesis_client(aws_credentials) -> Generator[boto3.client, None, None]:
    with mock_kinesis():
        kinesis = boto3.client("kinesis", region_name="us-east-1")
        yield kinesis


@pytest.fixture(scope="session")
def kinesis_index_nft_data_stream(
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


@pytest.fixture(scope="session")
def kinesis_input_event() -> Dict[str, Any]:
    event = {
        "blockchain_id": 65536,
        "token_key": "9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        "blocktime": "2022-06-01 13:15:55",
        "timestamp": "2022-06-03 14:25:30",
        "program_account_key": "M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        "transaction_hash": "1eE5Sw16rNVg6Z7xWhiQA7Lijp8DDZ2XGoRGK8GR9fCeCA5CYKib3qpQNVYh25hzUaUxhLguGgtdmSFJG13yRsz",
        "primary_sale_happened": True,
        "last_market_activity": "Listing",
        "is_mutable": False,
        "name": "Example NFT",
        "symbol": "eNFT",
        "uri": "http://example.nft",
        "owner": "5AmZM5qY2LZtBMVSTVzyZmUGFCgiMTD9xaRuLF8XF1hK",
        "seller_fee_basis_points": "",
        "creators": ["Creator #1", "Creator #2"],
        "verified": ["true", "true"],
        "share": [],
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
def kinesis_input_event_with_fake_blockchain() -> Dict[str, Any]:
    event = {
        "blockchain_id": 000000,
        "token_key": "9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        "blocktime": "2022-06-01 13:15:55",
        "timestamp": "2022-06-03 14:25:30",
        "program_account_key": "M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        "transaction_hash": "1eE5Sw16rNVg6Z7xWhiQA7Lijp8DDZ2XGoRGK8GR9fCeCA5CYKib3qpQNVYh25hzUaUxhLguGgtdmSFJG13yRsz",
        "primary_sale_happened": True,
        "last_market_activity": "Listing",
        "is_mutable": False,
        "name": "Example NFT",
        "symbol": "eNFT",
        "uri": "http://example.nft",
        "owner": "5AmZM5qY2LZtBMVSTVzyZmUGFCgiMTD9xaRuLF8XF1hK",
        "seller_fee_basis_points": "",
        "creators": ["Creator #1", "Creator #2"],
        "verified": ["true", "true"],
        "share": [],
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
def kinesis_invalid_input_event() -> Dict[str, Any]:
    event = {
        "blockchain_id": 65536,
        "program_account_key": "M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        "seller_fee_basis_points": "",
        "creators": ["Creator #1", "Creator #2"],
        "verified": ["true", "true"],
        "share": [],
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
