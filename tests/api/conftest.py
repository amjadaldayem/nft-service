from typing import List

import pytest

from sintra.api.model.token_feed import Token, TokenDetails


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://test"


@pytest.fixture(scope="session")
def token_details() -> TokenDetails:
    return TokenDetails(
        blockchain_id=65536,
        blockchain_name="Solana",
        collection_id="bc-65563-M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        token_key="9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        token_id="bc-65563-9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        token_name="Example NFT",
        owner="Owner",
        description="Example description",
        symbol="eNFT",
        price=0.01,
        price_currency="SOL",
        external_url="http://external.example.nft",
        image_url="http://example.nft/image/1.png",
        attributes={"background": "blue"},
    )


@pytest.fixture(scope="session")
def tokens() -> List[Token]:
    return [
        Token(
            blockchain_id=65536,
            blockchain_name="Solana",
            collection_id="bc-65563-M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
            token_key="9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
            token_id="bc-65563-9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
            token_name="Example NFT",
            owner="Owner",
            description="Example description",
            symbol="eNFT",
            timestamp="2022-01-01 13:16:29",
            transaction_hash="",
            event="Listing",
            price=0.01,
            price_currency="SOL",
            image_url="http://example.nft/image/1.png",
        )
    ]
