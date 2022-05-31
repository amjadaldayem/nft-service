from abc import ABC, abstractmethod
from typing import List

from sintra.api.model.token_feed import TokenFeed


class TokenFeedRepository(ABC):
    @abstractmethod
    def read_token_feed(
        self, blockchain: str, collection_name: str, nft_name: str
    ) -> List[TokenFeed]:
        """Read last N tokens sorted by descending time."""


class OpenSearchTokenFeedRepository(TokenFeedRepository):
    def read_token_feed(
        self, blockchain: str, collection_name: str, nft_name: str
    ) -> List[TokenFeed]:
        return []
