# pylint: disable=redefined-outer-name

import os
from typing import Generator

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
    return "project-stats-stream"


@pytest.fixture(scope="session")
def kinesis_client(aws_credentials) -> Generator[boto3.client, None, None]:
    with mock_kinesis():
        kinesis = boto3.client("kinesis", region_name="us-east-1")
        yield kinesis


@pytest.fixture(scope="session")
def kinesis_twitter_trends_stream(
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
