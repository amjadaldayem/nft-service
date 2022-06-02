from abc import ABC, abstractmethod
from typing import Any, Dict, List

from sintra.api.model.token_feed import Token, TokenDetails
from sintra.api.open_search.client import OpenSearchClient
from sintra.api.open_search.query import QueryBuilder


class AbstractTokenFeedRepository(ABC):
    @abstractmethod
    def read_tokens(self) -> List[Token]:
        """Read last N tokens sorted by descending time."""

    @abstractmethod
    def read_token(self, token_id: str) -> TokenDetails:
        """Read token data by id."""


class TokenFeedRepository(AbstractTokenFeedRepository):
    def __init__(self, client: OpenSearchClient) -> None:
        self.client = client
        self.query_builder = QueryBuilder()

    def read_token(self, token_id: str) -> Dict[str, Any]:
        query = self.query_builder.read_token_query(token_id)
        return self.client.submit_query(query)

    def read_tokens(self) -> List[Token]:
        query = self.query_builder.read_tokens_query()
        return self.client.submit_query(query)
