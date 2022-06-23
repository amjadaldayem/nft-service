from typing import List

import pytest

from data_api.model.token_feed import EntityDetails, Token, TokenDetails


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://test"


@pytest.fixture(scope="session")
def token_details() -> TokenDetails:
    return TokenDetails(
        blockchain_id=65536,
        blockchain_name="Solana",
        collection_id="bc-65563-M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K",
        collection_name="Example collection",
        token_key="9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        token_id="bc-65563-9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
        token_name="Example NFT",
        owner=EntityDetails(name="Owner", url=""),
        description="Example description",
        symbol="eNFT",
        price=0.01,
        price_currency="Lamport",
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
            collection_name="Example collection",
            collection_slug="example collection",
            token_key="9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
            token_id="bc-65563-9djKfEoRp4pZf8YHDYLBXgd84cGiHBbhjh5mHF8e9Vvy",
            token_name="Example NFT",
            token_slug="example nft",
            description="Example description",
            market=EntityDetails(name="Digital Eyes", url="http://digitaleyes.test"),
            owner=EntityDetails(name="Owner", url=""),
            buyer=EntityDetails(name="", url=""),
            symbol="eNFT",
            timestamp="2022-01-01 13:16:29",
            transaction_hash="",
            event="Listing",
            price=0.01,
            price_currency="Lamport",
            image_url="http://example.nft/image/1.png",
            bookmarked=False,
        )
    ]
