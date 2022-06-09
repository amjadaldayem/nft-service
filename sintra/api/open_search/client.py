import json
import logging
from typing import Any, Dict

import requests
from requests_aws4auth import AWS4Auth

logger = logging.getLogger(__name__)


class OpenSearchClient:
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str,
        domain: str,
        host: str,
        index: str,
    ) -> None:
        self.index = index
        self.url = f"http://{domain}.{region}.opensearch.{host}/{index}/_search"
        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json"}

        auth = AWS4Auth(access_key_id, secret_access_key, region, "opensearch")

        self.session.auth = auth

    def submit_query(self, query) -> Dict[str, Any]:
        response = self.session.post(
            url=self.url, headers=self.headers, data=json.dumps(query)
        )
        if response.status_code >= 400:
            logger.error(response.text)

        result = json.loads(response.text)
        hits = result.get("hits", None)
        return hits
