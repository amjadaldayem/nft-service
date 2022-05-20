from typing import Any, Dict, Optional, Union

import httpx
from solana.blockhash import BlockhashCache
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.rpc.providers.async_http import AsyncHTTPProvider


class AsynchronousHTTPProvider(AsyncHTTPProvider):
    """Expansion of Async HTTP provider with auth enabled."""

    def __init__(
        self,
        endpoint: str,
        timeout: float,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        super().__init__(endpoint)
        kwargs: Dict[str, Any] = {"timeout": httpx.Timeout(timeout)}

        if username and password:
            kwargs["auth"] = (username, password)

        self.session = httpx.AsyncClient(**kwargs)


class SolanaHTTPClient(AsyncClient):
    """Async client with adjustable timeout."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        commitment: Optional[Commitment] = None,
        blockhash_cache: Union[BlockhashCache, bool] = False,
        timeout: float = 10,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        super().__init__(endpoint, commitment, blockhash_cache)
        if endpoint is None:
            raise ValueError("Endpoint is not specified.")

        self._provider = AsynchronousHTTPProvider(endpoint, timeout, username, password)


__all__ = ["SolanaHTTPClient"]
