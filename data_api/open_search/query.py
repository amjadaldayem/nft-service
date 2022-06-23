from typing import Any, Dict


class QueryBuilder:
    def read_token_query(
        self, blockchain_name: str, collection_name_slug: str, token_name_slug: str
    ) -> Dict[str, Any]:
        return {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"blockchain_name": blockchain_name}},
                        {"match": {"collection_name_slug": collection_name_slug}},
                        {"match": {"token_name_slug": token_name_slug}},
                    ]
                }
            }
        }

    def read_tokens_query(self) -> Dict[str, Any]:
        return {
            "size": 20,
            "sort": {"timestamp_of_market_activity": {"order": "desc"}},
            "query": {"match_all": {}},
        }

    def read_tokens_from_query(self, timestamp: str) -> Dict[str, Any]:
        return {
            "size": 20,
            "sort": {"timestamp_of_market_activity": {"order": "desc"}},
            "query": {"range": {"timestamp_of_market_activity": {"lt": timestamp}}},
        }
