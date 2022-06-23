from typing import List
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from data_api.exception import DataClientException, ResourceNotFoundException
from data_api.main import app
from data_api.model.token_feed import Token, TokenDetails


@pytest.fixture(scope="module")
def router_endpoint() -> str:
    return "/v1/nft"


class TestTokenFeedRouter:
    @pytest.mark.anyio
    @patch("data_api.service.token_feed.TokenFeedService.read_token")
    async def test_read_token(
        self,
        read_token_fn,
        base_url: str,
        router_endpoint: str,
        token_details: TokenDetails,
    ) -> None:
        read_token_fn.return_value = token_details
        async with AsyncClient(app=app, base_url=base_url) as client:
            response = await client.get(
                url=f"{router_endpoint}/{token_details.blockchain_name}/{token_details.collection_name}/{token_details.token_name}"
            )

        assert response.status_code == 200
        assert response.json() == token_details.__dict__

    @pytest.mark.anyio
    @patch("data_api.service.token_feed.TokenFeedService.read_token")
    async def test_read_token_when_token_doesnt_exists(
        self,
        read_token_fn,
        base_url: str,
        router_endpoint: str,
        token_details: TokenDetails,
    ) -> None:
        read_token_fn.side_effect = ResourceNotFoundException(
            f"Token with id: {token_details.token_id} not found."
        )
        async with AsyncClient(app=app, base_url=base_url) as client:
            response = await client.get(
                url=f"{router_endpoint}/{token_details.blockchain_name}/{token_details.collection_name}/{token_details.token_name}"
            )

        assert response.status_code == 404
        assert response.json() == {"detail": "Token does not exist."}

    @pytest.mark.anyio
    @patch("data_api.service.token_feed.TokenFeedService.read_token")
    async def test_read_token_when_exception_occurs(
        self,
        read_token_fn,
        base_url: str,
        router_endpoint: str,
        token_details: TokenDetails,
    ) -> None:
        read_token_fn.side_effect = DataClientException(
            "Problems with client querying data store."
        )

        async with AsyncClient(app=app, base_url=base_url) as client:
            response = await client.get(
                url=f"{router_endpoint}/{token_details.blockchain_name}/{token_details.collection_name}/{token_details.token_name}"
            )

        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error."}

    @pytest.mark.anyio
    @patch("data_api.service.token_feed.TokenFeedService.read_tokens")
    async def test_read_tokens(
        self,
        read_tokens_fn,
        base_url: str,
        router_endpoint: str,
        tokens: List[Token],
    ) -> None:
        read_tokens_fn.return_value = tokens

        async with AsyncClient(app=app, base_url=base_url) as client:
            response = await client.get(url=f"{router_endpoint}/tokens")

        assert response.status_code == 200
        response_tokens = response.json()
        assert all(
            [
                response_token == token.__dict__
                for response_token, token in zip(response_tokens, tokens)
            ]
        )

    @pytest.mark.anyio
    @patch("data_api.service.token_feed.TokenFeedService.read_tokens_from")
    async def test_read_tokens_with_timestamp(
        self,
        read_tokens_from_fn,
        base_url: str,
        router_endpoint: str,
        tokens: List[Token],
    ) -> None:
        read_tokens_from_fn.return_value = tokens

        async with AsyncClient(app=app, base_url=base_url) as client:
            response = await client.get(
                url=f"{router_endpoint}/tokens?timestamp=2022-02-02T15:05:45"
            )

        assert response.status_code == 200
        response_tokens = response.json()
        assert all(
            [
                response_token == token.__dict__
                for response_token, token in zip(response_tokens, tokens)
            ]
        )
