import os
from datetime import datetime
from typing import List

from data_api.exception import DataClientException, ResourceNotFoundException
from data_api.model.token_feed import Token, TokenDetails
from data_api.repository.token_feed import TokenFeedRepository
from data_api.storage.postgres.client import PostgresClient
from data_api.utils import postgres_params


class TokenFeedService:
    def __init__(self) -> None:
        host, port, database_name, max_connections = postgres_params()

        open_search_client = PostgresClient(
            host,
            port,
            os.getenv("POSTGRES_USERNAME", None),
            os.getenv("POSTGRES_PASSWORD", None),
            database_name,
            max_connections,
        )
        self.token_feed_repository = TokenFeedRepository(open_search_client)

    def read_token(
        self, blockchain_name: str, collection_name: str, token_name: str
    ) -> TokenDetails:
        blockchain_name = blockchain_name.capitalize()
        response = self.token_feed_repository.read_token(
            blockchain_name, collection_name, token_name
        )
        if not response:
            raise DataClientException("Problems with client querying data store.")

        if len(response) > 0:
            token_details = TokenDetails.from_dict(response[0])
            return token_details

        raise ResourceNotFoundException("Token not found.")

    def read_tokens(self) -> List[Token]:
        response = self.token_feed_repository.read_tokens()
        if not response:
            raise DataClientException("Problems with client querying data store.")

        tokens: List[Token] = [Token.from_dict(row) for row in response]
        return tokens

    def read_tokens_from(self, timestamp: datetime) -> List[Token]:
        formatted_dt = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        response = self.token_feed_repository.read_tokens_from(formatted_dt)
        if not response:
            raise DataClientException("Problems with client querying data store.")

        tokens: List[Token] = [Token.from_dict(row) for row in response]
        return tokens
