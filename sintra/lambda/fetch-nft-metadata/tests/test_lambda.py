# pylint: disable=unused-argument

import time
from typing import Any, Dict, Generator
from unittest.mock import patch

import boto3
import pytest
from src.app import lambda_handler
from src.exception import DecodingException
from src.model import NFTMetadata


def nft_metadata() -> NFTMetadata:
    return NFTMetadata(
        blockchain_id=65536,
        token_key="9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        blocktime=time.time_ns(),
        timestamp=time.time_ns(),
        program_account_key="MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8",
        transaction_hash="1eE5Sw16rNVg6Z7xWhiQA7Lijp8DDZ2XGoRGK8GR9fCeCA5CYKib3qpQNVYh25hzUaUxhLguGgtdmSFJG13yRsz",
        primary_sale_happened=True,
        last_market_activity="Listing",
        is_mutable=False,
        name="Example",
        owner="Example owner",
        symbol="Example",
        uri="http://test.io",
        seller_fee_basis_points="0.5",
        creators=[],
        verified=[],
        share=[],
    )


class TestLambdaFunction:
    @patch("src.app.get_nft_metadata")
    def test_lambda_handler(
        self,
        get_nft_metadata_fn,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        kinesis_input_event: Dict[str, Any],
    ) -> None:
        get_nft_metadata_fn.return_value = nft_metadata()

        response = lambda_handler(kinesis_input_event, context={})

        get_nft_metadata_fn.assert_called_once()
        assert response["message"] == "Successfully processed signature batch."

    def test_lambda_when_invalid_secondary_market_event(
        self,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        kinesis_invalid_input_event: Dict[str, Any],
    ) -> None:
        with pytest.raises(DecodingException):
            lambda_handler(kinesis_invalid_input_event, context={})

    def test_lambda_when_metadata_fetcher_not_implemented(
        self,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        kinesis_non_existing_market_input_event: Dict[str, Any],
    ) -> None:
        response = lambda_handler(kinesis_non_existing_market_input_event, context={})

        assert response["message"] == "Resulting batch of events is empty."
