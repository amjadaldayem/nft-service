from typing import Any, Dict


class QueryBuilder:
    def read_token_query(self, token_id: str) -> Dict[str, Any]:
        return {"query": {"match": {"token_id.keyword": token_id}}}

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
