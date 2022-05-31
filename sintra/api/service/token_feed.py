from typing import List

from sintra.api.model.token_feed import TokenFeed
from sintra.api.repository.token_feed import OpenSearchTokenFeedRepository


class TokenFeedService:
    def __init__(self) -> None:
        self.token_feed_repository = OpenSearchTokenFeedRepository()

    def read_token_feed(
        self, blockchain: str, collection_name: str, nft_name: str
    ) -> List[TokenFeed]:
        return self.token_feed_repository.read_token_feed(
            blockchain, collection_name, nft_name
        )
