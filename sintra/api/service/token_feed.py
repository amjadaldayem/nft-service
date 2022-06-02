import os
from typing import Any, Dict, List, Tuple

from sintra.api.config import settings
from sintra.api.exception import ResourceNotFoundException
from sintra.api.model.token_feed import Token, TokenDetails
from sintra.api.open_search.client import OpenSearchClient
from sintra.api.repository.token_feed import TokenFeedRepository


class TokenFeedService:
    def __init__(self) -> None:
        domain, host, index = self._opensearch_params()

        open_search_client = OpenSearchClient(
            os.getenv("AWS_ACCESS_KEY_ID"),
            os.getenv("AWS_SECRET_ACCESS_KEY"),
            os.getenv("AWS_REGION"),
            domain,
            host,
            index,
        )
        self.token_feed_repository = TokenFeedRepository(open_search_client)

    def read_token(self, token_id: str) -> TokenDetails:
        json_response = self.token_feed_repository.read_token(token_id)

        hits: List[Dict[str, Any]] = json_response["hits"]
        if hits:
            token_hit = hits[0]
            token_dict = token_hit["_source"]
            token_details = TokenDetails.from_dict(token_dict)

            return token_details

        raise ResourceNotFoundException(f"Token with id: {token_id} not found.")

    def read_tokens(self) -> List[Token]:
        json_response = self.token_feed_repository.read_tokens()
        token_hits: List[Dict[str, Any]] = json_response["hits"]

        tokens: List[Token] = [
            Token.from_dict(token_hit["_source"]) for token_hit in token_hits
        ]

        return tokens

    def _opensearch_params(self) -> Tuple[str, str, str]:
        hostname = settings.opensearch.host
        port = settings.opensearch.port
        domain = settings.opensearch.domain
        index = settings.opensearch.token_feed_index

        host = f"{hostname}:{port}"

        return domain, host, index
