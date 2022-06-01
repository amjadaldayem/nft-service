from typing import Any, Dict, List

from sintra.api.exception import ResourceNotFoundException
from sintra.api.model.token_feed import Token, TokenDetails
from sintra.api.repository.token_feed import TokenFeedRepository


class TokenFeedService:
    def __init__(self) -> None:
        self.token_feed_repository = TokenFeedRepository()

    def read_token(self, token_id: str) -> TokenDetails:
        json_response = self.token_feed_repository.read_token(token_id)

        hits: List[Dict[str, Any]] = json_response["hits"]
        if hits:
            token_dict = hits[0]
            token_details = TokenDetails.from_dict(token_dict)

            return token_details

        raise ResourceNotFoundException(f"Token with id: {token_id} not found.")

    def read_tokens(self) -> List[Token]:
        json_response = self.token_feed_repository.read_tokens()
        token_hits: List[Dict[str, Any]] = json_response["hits"]

        tokens: List[Token] = [Token.from_dict(token_hit) for token_hit in token_hits]

        return tokens
