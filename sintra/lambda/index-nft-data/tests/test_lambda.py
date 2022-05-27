# pylint: disable=unused-argument

import time
from typing import Any, Dict, Generator
from unittest.mock import patch

import boto3
import pytest
from src.app import lambda_handler
from src.exception import DecodingException
from src.model import MediaFile, NFTCreator, NFTData


def nft_data() -> NFTData:
    return NFTData(
        blockchain_id=65563,
        blockchain_name="Solana",
        collection_id="bc#65563#M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        token_key="9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        owner="5AmZM5qY2LZtBMVSTVzyZmUGFCgiMTD9xaRuLF8XF1hK",
        token_id="bc#65563#9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        token_name="Example NFT",
        description="Example description",
        symbol="eNFT",
        primary_sale_happened=True,
        last_market_activity="Listing",
        timestamp_of_market_activity=time.time_ns(),
        metadata_uri="http://example.nft",
        attributes={"background": "blue"},
        transaction_hash="1eE5Sw16rNVg6Z7xWhiQA7Lijp8DDZ2XGoRGK8GR9fCeCA5CYKib3qpQNVYh25hzUaUxhLguGgtdmSFJG13yRsz",
        price=0.07,
        price_currency="SOL",
        creators=[NFTCreator(address="", verified=True, share=1)],
        edition="",
        external_url="http://external.example.nft",
        media_files=[MediaFile(uri="http://example.nft/image/1.png", file_type=".png")],
    )


class TestIndexNFTData:
    @patch("src.app.get_nft_data")
    def test_lambda_handler(
        self,
        get_nft_data_fn,
        kinesis_input_event: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        get_nft_data_fn.return_value = nft_data()

        response = lambda_handler(event=kinesis_input_event, context={})

        get_nft_data_fn.assert_called_once()
        assert response["message"] == "Successfully processed metadata batch."

    def test_lambda_handler_with_invalid_input_event(
        self,
        kinesis_invalid_input_event: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        with pytest.raises(DecodingException):
            lambda_handler(event=kinesis_invalid_input_event, context={})

    def test_lambda_handler_with_unsupported_blockchain(
        self,
        kinesis_input_event_with_fake_blockchain: Dict[str, Any],
        kinesis_index_nft_data_stream: Generator[boto3.client, None, None],
    ) -> None:
        response = lambda_handler(
            event=kinesis_input_event_with_fake_blockchain, context={}
        )

        assert response["message"] == "Resulting batch of events is empty."
