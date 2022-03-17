import json
import logging
from typing import Any, Dict
from typing import Optional, Union

import httpx
import orjson
import requests
import websockets
from httpx import Timeout
from solana.blockhash import BlockhashCache
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.rpc.providers.async_http import AsyncHTTPProvider
from solana.rpc.providers.http import HTTPProvider
from solana.rpc.types import RPCMethod, RPCResponse
from solana.rpc.websocket_api import connect

from app import settings

logger = logging.getLogger(__name__)


class CustomHTTPProvider(HTTPProvider):

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop("timeout", 60)
        super().__init__(*args, **kwargs)
        username = settings.SOLANA_RPC_CLUSTER_USERNAME
        password = settings.SOLANA_RPC_CLUSTER_PASSWORD
        self.auth = (username, password) if username and password else None

    def make_request(self, method: RPCMethod, *params: Any) -> RPCResponse:
        """Make an HTTP request to an http rpc endpoint."""
        request_kwargs = self._before_request(method=method, params=params, is_async=False)
        if self.auth:
            request_kwargs['auth'] = self.auth
        raw_response = requests.post(**request_kwargs, timeout=self.timeout)
        return self._after_request(raw_response=raw_response, method=method)

    def json_decode(self, json_str: str) -> Dict[Any, Any]:  # pylint: disable=no-self-use
        """Deserialize JSON document to a Python object with friendly error messages.
        Customized with `orjson` to gain 10x speed boost on decoding.
        """
        try:
            decoded = orjson.loads(json_str)
            return decoded
        except json.decoder.JSONDecodeError as exc:
            err_msg = "Could not decode {} because of {}.".format(repr(json_str), exc)
            # Calling code may rely on catching JSONDecodeError to recognize bad json
            # so we have to re-raise the same type.
            raise json.decoder.JSONDecodeError(err_msg, exc.doc, exc.pos)


class CustomClient(Client):
    """
    A custom client with adjustable `timeout` value.
    """

    def __init__(
            self,
            endpoint: Optional[str] = None,
            commitment: Optional[Commitment] = None,
            blockhash_cache: Union[BlockhashCache, bool] = False,
            timeout: int = 30
    ) -> None:
        super().__init__(endpoint, commitment, blockhash_cache, timeout=timeout)
        self._provider = CustomHTTPProvider(endpoint, timeout=timeout)


class CustomAsyncHTTPProvider(AsyncHTTPProvider):

    def __init__(self, endpoint, timeout: int):
        """Init AsyncHTTPProvider."""
        super().__init__(endpoint)
        kwargs = {
            'timeout': Timeout(float(timeout)),
        }
        username = settings.SOLANA_RPC_CLUSTER_USERNAME
        password = settings.SOLANA_RPC_CLUSTER_PASSWORD
        if username and password:
            kwargs['auth'] = (username, password)

        self.session = httpx.AsyncClient(
            **kwargs
        )


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


async def reliable_solana_websocket():
    uri = settings.SOLANA_RPC_WSS_ENDPOINT
    username = settings.SOLANA_RPC_CLUSTER_USERNAME
    password = settings.SOLANA_RPC_CLUSTER_PASSWORD
    if username and password:
        uri = uri.replace('wss://', f'wss://{username}:{password}@')

    async for websocket in connect(uri):
        try:
            yield websocket
        except websockets.ConnectionClosed:
            logger.error("Websocket closed. Reconnecting")
            continue
        except:
            raise
