import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

from data_api.config import settings
from data_api.exception import DataClientException, ResourceNotFoundException
from data_api.model.token_feed import Token, TokenDetails
from data_api.open_search.client import OpenSearchClient
from data_api.repository.token_feed import TokenFeedRepository


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

    def read_token(
        self, blockchain_name: str, collection_name: str, token_name: str
    ) -> TokenDetails:
        blockchain_name = blockchain_name.capitalize()
        json_response = self.token_feed_repository.read_token(
            blockchain_name, collection_name, token_name
        )
        if not json_response:
            raise DataClientException("Problems with client querying data store.")

        hits: List[Dict[str, Any]] = json_response.get("hits", [])
        if len(hits) > 0:
            token_hit = hits[0]
            token_dict = token_hit["_source"]
            token_details = TokenDetails.from_dict(token_dict)

            return token_details

        raise ResourceNotFoundException("Token not found.")

    def read_tokens(self) -> List[Token]:
        json_response = self.token_feed_repository.read_tokens()
        if not json_response:
            raise DataClientException("Problems with client querying data store.")

        token_hits: List[Dict[str, Any]] = json_response.get("hits", [])

        tokens: List[Token] = [
            Token.from_dict(token_hit["_source"]) for token_hit in token_hits
        ]

        return tokens

    def read_tokens_from(self, timestamp: datetime) -> List[Token]:
        formatted_dt = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        json_response = self.token_feed_repository.read_tokens_from(formatted_dt)
        if not json_response:
            raise DataClientException("Problems with client querying data store.")

        token_hits: List[Dict[str, Any]] = json_response.get("hits", [])

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
