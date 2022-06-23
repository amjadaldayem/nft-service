from abc import ABC, abstractmethod
from typing import Any, Dict, List

from data_api.model.token_feed import Token, TokenDetails
from data_api.open_search.client import OpenSearchClient
from data_api.open_search.query import QueryBuilder


class AbstractTokenFeedRepository(ABC):
    @abstractmethod
    def read_tokens(self) -> List[Token]:
        """Read last N tokens sorted by descending time."""

    @abstractmethod
    def read_token(
        self, blockchain_name: str, collection_name: str, token_name: str
    ) -> TokenDetails:
        """Read token data by blockchain name, collection name and token name."""

    @abstractmethod
    def read_tokens_from(self, timestamp: str) -> List[Token]:
        """Read last N tokens lower than timestamp."""


class TokenFeedRepository(AbstractTokenFeedRepository):
    def __init__(self, client: OpenSearchClient) -> None:
        self.client = client
        self.query_builder = QueryBuilder()

    def read_token(
        self, blockchain_name: str, collection_name: str, token_name: str
    ) -> Dict[str, Any]:
        query = self.query_builder.read_token_query(
            blockchain_name, collection_name, token_name
        )
        return self.client.submit_query(query)

    def read_tokens(self) -> List[Token]:
        query = self.query_builder.read_tokens_query()
        return self.client.submit_query(query)

    def read_tokens_from(self, timestamp: str) -> List[Token]:
        query = self.query_builder.read_tokens_from_query(timestamp)
        return self.client.submit_query(query)
