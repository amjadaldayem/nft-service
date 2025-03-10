# pylint: disable=unused-argument

import time
from typing import Any, Dict, Generator
from unittest.mock import patch

import boto3
import pytest
from src.app import lambda_handler
from src.exception import DecodingException, UnableToFetchMetadataException
from src.model import NFTMetadata


def solana_nft_metadata() -> NFTMetadata:
    return NFTMetadata(
        blockchain_id=65536,
        market_id=65792,
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
        price=0.01,
    )


def ethereum_nft_metadata() -> NFTMetadata:
    return NFTMetadata(
        blockchain_id=196608,
        market_id=196865,
        token_key="0xaf6D892177BBabCD71623f55728eb7bc1E919B8e/15",
        blocktime=time.time_ns(),
        timestamp=time.time_ns(),
        program_account_key="MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8",
        transaction_hash="0x67e68505498206d75c80c545e6832934082439290649ba59f6efde545c23c77a",
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
        price=6500000000000000000,
    )


class TestSolanaLambdaFunction:
    @patch("src.app.get_nft_metadata")
    def test_lambda_handler(
        self,
        get_nft_metadata_fn,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        solana_kinesis_input_event: Dict[str, Any],
    ) -> None:
        get_nft_metadata_fn.return_value = solana_nft_metadata()
        response = lambda_handler(solana_kinesis_input_event, context={})

        get_nft_metadata_fn.assert_called_once()
        assert response["message"] == "Successfully processed signature batch."

    def test_lambda_when_invalid_secondary_market_event(
        self,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        solana_kinesis_invalid_input_event: Dict[str, Any],
    ) -> None:
        with pytest.raises(DecodingException):
            lambda_handler(solana_kinesis_invalid_input_event, context={})

    def test_lambda_when_metadata_fetcher_not_implemented(
        self,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        kinesis_non_existing_market_input_event: Dict[str, Any],
    ) -> None:
        response = lambda_handler(kinesis_non_existing_market_input_event, context={})

        assert response["message"] == "Resulting batch of events is empty."

    @patch("src.app.get_nft_metadata")
    def test_lambda_when_metadata_cannot_be_fetched(
        self,
        get_nft_metadata_fn,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        solana_kinesis_input_event: Dict[str, Any],
    ) -> None:
        get_nft_metadata_fn.side_effect = UnableToFetchMetadataException(
            "Unable to fetch metadata."
        )
        response = lambda_handler(solana_kinesis_input_event, context={})

        get_nft_metadata_fn.assert_called_once()
        assert response["message"] == "Resulting batch of events is empty."


class TestEthereumLambdaFunction:
    @patch("src.app.get_nft_metadata")
    def test_lambda_handler(
        self,
        get_nft_metadata_fn,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        ethereum_kinesis_input_event: Dict[str, Any],
    ) -> None:
        get_nft_metadata_fn.return_value = ethereum_nft_metadata()
        response = lambda_handler(ethereum_kinesis_input_event, context={})

        get_nft_metadata_fn.assert_called_once()
        assert response["message"] == "Successfully processed signature batch."

    def test_lambda_when_invalid_secondary_market_event(
        self,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        ethereum_kinesis_invalid_input_event: Dict[str, Any],
    ) -> None:
        with pytest.raises(DecodingException):
            lambda_handler(ethereum_kinesis_invalid_input_event, context={})

    def test_lambda_when_metadata_fetcher_not_implemented(
        self,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        kinesis_non_existing_market_input_event: Dict[str, Any],
    ) -> None:
        response = lambda_handler(kinesis_non_existing_market_input_event, context={})

        assert response["message"] == "Resulting batch of events is empty."

    @patch("src.app.get_nft_metadata")
    def test_lambda_when_metadata_cannot_be_fetched(
        self,
        get_nft_metadata_fn,
        kinesis_nft_metadata_stream: Generator[boto3.client, None, None],
        ethereum_kinesis_input_event: Dict[str, Any],
    ) -> None:
        get_nft_metadata_fn.side_effect = UnableToFetchMetadataException(
            "Unable to fetch metadata."
        )
        response = lambda_handler(ethereum_kinesis_input_event, context={})

        get_nft_metadata_fn.assert_called_once()
        assert response["message"] == "Resulting batch of events is empty."
