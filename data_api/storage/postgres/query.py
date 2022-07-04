from typing import Tuple

from psycopg2 import sql

from data_api.storage.query_builder import QueryBuilder


class PostgresQueryBuilder(QueryBuilder):
    def read_token_query(
        self, blockchain_name: str, collection_name_slug: str, token_name_slug: str
    ) -> Tuple[sql.SQL, Tuple[str, str, str]]:
        pass

    def read_tokens_query(self) -> sql.SQL:
        return sql.SQL("SELECT * FROM {table} ORDER BY {field} DESC LIMIT 20;").format(
            table=sql.Identifier("nft_data"),
            field=sql.Identifier("timestamp_of_market_activity"),
        )

    def read_tokens_from_query(self, timestamp: str) -> Tuple[sql.SQL, str]:
        pass
