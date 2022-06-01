from abc import ABC, abstractmethod
from typing import Any, Dict, List

from sintra.api.exception import ResourceNotFoundException
from sintra.api.model.token_feed import Token, TokenDetails
from sintra.api.open_search.client import OpenSearchClient


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

    def read_token(self, token_id: str) -> Dict[str, Any]:
        # TODO: build query
        return self.client.submit_query()

    def read_tokens(self) -> List[Token]:
        # TODO: build query
        return self.client.submit_query()
