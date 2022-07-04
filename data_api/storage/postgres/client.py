import logging
from typing import Any, Dict, List, Union

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from data_api.exception import DataClientException

logger = logging.getLogger(__name__)


class PostgresClient:
    def __init__(
        self,
        host: str,
        port: str,
        username: str,
        password: str,
        database_name: str,
        max_connections: int,
    ) -> None:
        self.connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=max_connections,
            user=username,
            password=password,
            host=host,
            port=port,
            database=database_name,
        )

        if self.connection_pool:
            logger.info("Connection pool created successfully.")

    def submit_query(
        self, query_data: Any
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        connection = self.connection_pool.getconn()
        if connection:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            if isinstance(query_data, tuple):
                query, data = query_data
                cursor.execute_query(query, data)
            else:
                cursor.execute_query(query_data)

            results = cursor.fetch_all()

            cursor.close()
            self.connection_pool.putconn(connection)

            return results

        raise DataClientException("Can't get connection from connection pool.")

    def close_pool(self) -> None:
        self.connection_pool.closeall()
