from abc import ABC, abstractmethod
from typing import Any, Dict, List

from data_api.storage.postgres.client import PostgresClient
from data_api.storage.postgres.query import PostgresQueryBuilder


class AbstractTokenFeedRepository(ABC):
    @abstractmethod
    def read_tokens(self) -> List[Dict[str, Any]]:
        """Read last N tokens sorted by descending time."""

    @abstractmethod
    def read_token(
        self, blockchain_name: str, collection_name: str, token_name: str
    ) -> Dict[str, Any]:
        """Read token data by blockchain name, collection name and token name."""

    @abstractmethod
    def read_tokens_from(self, timestamp: str) -> List[Dict[str, Any]]:
        """Read last N tokens lower than timestamp."""


class TokenFeedRepository(AbstractTokenFeedRepository):
    def __init__(self, client: PostgresClient) -> None:
        self.client = client
        self.query_builder = PostgresQueryBuilder()

    def read_token(
        self, blockchain_name: str, collection_name: str, token_name: str
    ) -> Dict[str, Any]:
        query = self.query_builder.read_token_query(
            blockchain_name, collection_name, token_name
        )
        return self.client.submit_query(query)

    def read_tokens(self) -> List[Dict[str, Any]]:
        query = self.query_builder.read_tokens_query()
        return self.client.submit_query(query)

    def read_tokens_from(self, timestamp: str) -> List[Dict[str, Any]]:
        query = self.query_builder.read_tokens_from_query(timestamp)
        return self.client.submit_query(query)
