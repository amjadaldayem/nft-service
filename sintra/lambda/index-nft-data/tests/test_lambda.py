# pylint: disable=unused-argument

import time
from typing import Any, Dict, Generator
from unittest.mock import patch

import boto3
import pytest
from src.app import lambda_handler
from src.exception import DecodingException
from src.model import MediaFile, NFTCreator, NFTData


def solana_nft_data() -> NFTData:
    return NFTData(
        blockchain_id=65563,
        blockchain_name="Solana",
        market_id=65792,
        collection_id="bc-65563-M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        collection_name="Example collection",
        collection_name_slug="example collection",
        token_key="9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        owner="5AmZM5qY2LZtBMVSTVzyZmUGFCgiMTD9xaRuLF8XF1hK",
        token_id="bc-65563#9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        token_name="Example NFT",
        token_name_slug="example nft",
        description="Example description",
        symbol="eNFT",
        primary_sale_happened=True,
        last_market_activity="Listing",
        timestamp_of_market_activity="2022-06-02 11:22:22",
        event_timestamp=time.time_ns(),
        metadata_uri="http://example.nft",
        attributes={"background": "blue"},
        transaction_hash="1eE5Sw16rNVg6Z7xWhiQA7Lijp8DDZ2XGoRGK8GR9fCeCA5CYKib3qpQNVYh25hzUaUxhLguGgtdmSFJG13yRsz",
        price=0.07,
        price_currency="Lamport",
        creators=[NFTCreator(address="", verified=True, share=1)],
        edition="",
        external_url="http://external.example.nft",
        media_files=[MediaFile(uri="http://example.nft/image/1.png", file_type=".png")],
    )


def ethereum_nft_data() -> NFTData:
    return NFTData(
        blockchain_id=196608,
        blockchain_name="Ethereum",
        market_id=196865,
        collection_id="bc-196608-M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        collection_name="Example collection",
        collection_name_slug="example collection",
        token_key="0xaf6D892177BBabCD71623f55728eb7bc1E919B8e/15",
        owner="5AmZM5qY2LZtBMVSTVzyZmUGFCgiMTD9xaRuLF8XF1hK",
        token_id="bc-196608#0xaf6D892177BBabCD71623f55728eb7bc1E919B8e/15",
        token_name="Example NFT",
        token_name_slug="example nft",
        description="Example description",
        symbol="eNFT",
        primary_sale_happened=True,
        last_market_activity="Listing",
        timestamp_of_market_activity="2022-06-02 11:22:22",
        event_timestamp=time.time_ns(),
        metadata_uri="http://example.nft",
        attributes={"background": "blue"},
        transaction_hash="0x67e68505498206d75c80c545e6832934082439290649ba59f6efde545c23c77a",
        price=0.23,
        price_currency="Wei",
        creators=[NFTCreator(address="", verified=True, share=1)],
        edition="",
        external_url="http://external.example.nft",
        media_files=[MediaFile(uri="http://example.nft/image/1.png", file_type=".png")],
    )


class TestSolanaIndexNFTData:
    @patch("src.app.get_nft_data")
    def test_lambda_handler(
        self,
        get_nft_data_fn,
        solana_kinesis_input_event: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        get_nft_data_fn.return_value = solana_nft_data()

        response = lambda_handler(event=solana_kinesis_input_event, context={})

        get_nft_data_fn.assert_called_once()
        assert (
            response["message"] == "Successfully processed metadata batch of length: 1."
        )

    def test_lambda_handler_with_invalid_input_event(
        self,
        solana_kinesis_invalid_input_event: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        with pytest.raises(DecodingException):
            lambda_handler(event=solana_kinesis_invalid_input_event, context={})

    def test_lambda_handler_with_unsupported_blockchain(
        self,
        kinesis_input_event_with_fake_blockchain: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        response = lambda_handler(
            event=kinesis_input_event_with_fake_blockchain, context={}
        )

        assert response["message"] == "Resulting batch of events is empty."


class TestEthereumIndexNFTData:
    @patch("src.app.get_nft_data")
    def test_lambda_handler(
        self,
        get_nft_data_fn,
        ethereum_kinesis_input_event: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        get_nft_data_fn.return_value = ethereum_nft_data()

        response = lambda_handler(event=ethereum_kinesis_input_event, context={})

        get_nft_data_fn.assert_called_once()
        assert (
            response["message"] == "Successfully processed metadata batch of length: 1."
        )

    def test_lambda_handler_with_invalid_input_event(
        self,
        ethereum_kinesis_invalid_input_event: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        with pytest.raises(DecodingException):
            lambda_handler(event=ethereum_kinesis_invalid_input_event, context={})

    def test_lambda_handler_with_unsupported_blockchain(
        self,
        kinesis_input_event_with_fake_blockchain: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        response = lambda_handler(
            event=kinesis_input_event_with_fake_blockchain, context={}
        )

        assert response["message"] == "Resulting batch of events is empty."
