import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Generator

import boto3
import pytest
from moto import mock_kinesis
from src.parser.alpha_art import AlphaArtParser
from src.parser.exchange_art import (
    ExchangeArtParserAuction,
    ExchangeArtParserV1,
    ExchangeArtParserV2,
)
from src.parser.magic_eden import (
    MagicEdenAuctionParser,
    MagicEdenParserV1,
    MagicEdenParserV2,
)
from src.parser.monkey_business import MonkeyBusinessParserV2
from src.parser.solanart import SolanartParser
from src.parser.solsea import SolseaParser
from src.parser.digital_eyes import DigitalEyesParserV1, DigitalEyesParserV2
from src.parser.open_sea import OpenSeaParser, OpenSeaParserAuction
from src.parser.ethereum.open_sea import EthereumOpenSeaParser


@pytest.fixture(scope="session")
def data_path() -> Path:
    return Path(__file__).absolute().parent / "data"


@pytest.fixture(scope="session")
def magic_eden_v1_transaction_path(data_path: Path) -> Path:
    return data_path / "magic_eden_v1"


@pytest.fixture(scope="session")
def magic_eden_v2_transaction_path(data_path: Path) -> Path:
    return data_path / "magic_eden_v2"


@pytest.fixture(scope="session")
def magic_eden_auction_transaction_path(data_path: Path) -> Path:
    return data_path / "magic_eden_auction"


@pytest.fixture(scope="session")
def monkey_business_v2_transaction_path(data_path: Path) -> Path:
    return data_path / "monkey_business_v2"


@pytest.fixture(scope="session")
def alpha_art_transaction_path(data_path: Path) -> Path:
    return data_path / "alpha_art"


@pytest.fixture(scope="session")
def solsea_transaction_path(data_path: Path) -> Path:
    return data_path / "solsea"


@pytest.fixture(scope="session")
def solanart_transaction_path(data_path: Path) -> Path:
    return data_path / "solanart"


@pytest.fixture(scope="session")
def exchange_art_transaction_path(data_path: Path) -> Path:
    return data_path / "exchange_art"


@pytest.fixture(scope="session")
def digital_eyes_v1_transaction_path(data_path: Path) -> Path:
    return data_path / "digital_eyes_v1"


@pytest.fixture(scope="session")
def digital_eyes_v2_transaction_path(data_path: Path) -> Path:
    return data_path / "digital_eyes_v2"


@pytest.fixture(scope="session")
def open_sea_transaction_path(data_path: Path) -> Path:
    return data_path / "open_sea"


@pytest.fixture(scope="session")
def open_sea_auction_transaction_path(data_path: Path) -> Path:
    return data_path / "open_sea_auction"


@pytest.fixture(scope="session")
def ethereum_open_sea_transaction_path(data_path: Path) -> Path:
    return data_path / "ethereum" / "open_sea"


@pytest.fixture(scope="session")
def magic_eden_v1_parser() -> MagicEdenParserV1:
    return MagicEdenParserV1()


@pytest.fixture(scope="session")
def magic_eden_v2_parser() -> MagicEdenParserV2:
    return MagicEdenParserV2()


@pytest.fixture(scope="session")
def magic_eden_auction_parser() -> MagicEdenAuctionParser:
    return MagicEdenAuctionParser()


@pytest.fixture(scope="session")
def alpha_art_parser() -> AlphaArtParser:
    return AlphaArtParser()


@pytest.fixture(scope="session")
def solsea_parser() -> SolseaParser:
    return SolseaParser()


@pytest.fixture(scope="session")
def solanart_parser() -> SolanartParser:
    return SolanartParser()


@pytest.fixture(scope="session")
def exchange_art_v1_parser() -> ExchangeArtParserV1:
    return ExchangeArtParserV1()


@pytest.fixture(scope="session")
def exchange_art_v2_parser() -> ExchangeArtParserV2:
    return ExchangeArtParserV2()


@pytest.fixture(scope="session")
def exchange_art_auction_parser() -> ExchangeArtParserAuction:
    return ExchangeArtParserAuction()


@pytest.fixture(scope="session")
def monkey_business_v2_parser() -> MonkeyBusinessParserV2:
    return MonkeyBusinessParserV2()


@pytest.fixture(scope="session")
def digital_eyes_v1_parser() -> DigitalEyesParserV1:
    return DigitalEyesParserV1()


@pytest.fixture(scope="session")
def digital_eyes_v2_parser() -> DigitalEyesParserV2:
    return DigitalEyesParserV2()


@pytest.fixture(scope="session")
def open_sea_parser() -> OpenSeaParser:
    return OpenSeaParser()


@pytest.fixture(scope="session")
def open_sea_parser_auction() -> OpenSeaParserAuction:
    return OpenSeaParserAuction()


@pytest.fixture(scope="session")
def ethereum_open_sea_parser() -> EthereumOpenSeaParser:
    return EthereumOpenSeaParser()


@pytest.fixture(scope="session")
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="session")
def kinesis_input_event() -> Dict[str, Any]:
    event = {
        "market": "Magic Eden",
        "market_address": "GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp",
        "market_account": "MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8",
        "signature": "3CUHXfnkBW96F7Ae8jSsntDZ2NX8XCgrMHfFq8XnmE2nVBotP2DxycbtCFeZk3tQPk5tw87ZufJGS3gRDr9QE1QQ",
        "timestamp": 1652888535.860566,
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
        "market": "Non-existing market",
        "market_address": "95B0BXJlba9Fy7HyDBZyR587eZYjUlLexTvduce0va1",
        "market_account": "lCcoFtZMKdqf58WcpkM9EbLhVjk4f6Y2aw8R0H6G9tp",
        "signature": "3CUHXfnkBW96F7Ae8jSsntDZ2NX8XCgrMHfFq8XnmE2nVBotP2DxycbtCFeZk3tQPk5tw87ZufJGS3gRDr9QE1QQ",
        "timestamp": 1652888535.860566,
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
    return "secondary-market"


@pytest.fixture(scope="session")
def kinesis_client(aws_credentials) -> Generator[boto3.client, None, None]:
    with mock_kinesis():
        kinesis = boto3.client("kinesis", region_name="us-east-1")
        yield kinesis


@pytest.fixture(scope="session")
def kinesis_secondary_market_stream(
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
