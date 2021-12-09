from typing import Optional, Union

import httpx
from httpx import Timeout
from solana.blockhash import BlockhashCache
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.rpc.providers.async_http import AsyncHTTPProvider


class CustomAsyncHTTPProvider(AsyncHTTPProvider):

    def __init__(self, endpoint, timeout: int):
        """Init AsyncHTTPProvider."""
        super().__init__(endpoint)
        self.session = httpx.AsyncClient(timeout=Timeout(float(timeout)))


class CustomAsyncClient(AsyncClient):
    """
    A custom async client with adjustable `timeout` value.
    """

    def __init__(
            self,
            endpoint: Optional[str] = None,
            commitment: Optional[Commitment] = None,
            blockhash_cache: Union[BlockhashCache, bool] = False,
            timeout: int = 30
    ) -> None:
        super().__init__(commitment, blockhash_cache)
        self._provider = CustomAsyncHTTPProvider(endpoint, timeout=timeout)
