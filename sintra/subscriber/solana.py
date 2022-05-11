import logging
from time import time_ns
from typing import AsyncGenerator, List, Optional, Tuple

from apischema.validation.errors import ValidationError
from solana.rpc.websocket_api import Error, connect
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosedError

from sintra.exception import (
    ClientRPCConnectionClosedException,
    ClientRPCConnectionException,
)
from sintra.subscriber.client import AsynchronousClient
from sintra.utils import get_env_variable

logger = logging.getLogger(__name__)


class SolanaRPCClient:
    def __init__(
        self,
        http_endpoint: str,
        http_timeout: float,
        ws_endpoint: str,
        ws_timeout: int,
    ) -> None:

        self.http_username = get_env_variable("SOLANA_RPC_HTTP_USERNAME")
        self.http_password = get_env_variable("SOLANA_RPC_HTTP_PASSWORD")
        self.http_client: Optional[AsynchronousClient] = None
        self.http_endpoint = http_endpoint
        self.http_timeout = http_timeout

        self.ws_client: Optional[WebSocketClientProtocol] = None
        self.ws_timeout = ws_timeout
        self.ws_endpoint = self._auth_ws_endpoint(ws_endpoint)
        self.last_signature_recv: Optional[str] = None
        self.subscription_id: Optional[int] = None

    async def connect_http_client(self) -> None:
        self.http_client = AsynchronousClient(
            endpoint=self.http_endpoint,
            timeout=self.http_timeout,
            username=self.http_username,
            password=self.http_password,
        )
        logger.info(f"HTTP client connected: {await self.http_client.is_connected()}")

    async def get_signatures_before(
        self, signature: str, account: str
    ) -> List[Tuple[str, int]]:
        if self.http_client is not None and await self.http_client.is_connected():
            rpc_response = await self.http_client.get_signatures_for_address(
                account, signature, self.last_signature_recv, 15
            )
            signatures_leftover = [
                (result["signature"], time_ns()) for result in rpc_response["result"]
            ]
            logger.debug(f"Signature leftover: {len(signatures_leftover)}.")
            return signatures_leftover

        raise ClientRPCConnectionException("HTTP Client not connected.")

    async def listen_for_transactions(
        self, accounts: List[str]
    ) -> AsyncGenerator[Tuple[str, int], None]:
        account: str = accounts[0]
        async with connect(
            uri=self.ws_endpoint, ping_timeout=self.ws_timeout
        ) as websocket:
            self.ws_client = websocket

            if self.ws_client is None:
                logger.info("Websocket client hasn't been initialized.")
                return

            await self.ws_client.logs_subscribe({"mentions": accounts})
            message = await self.ws_client.recv()
            if isinstance(message, Error):
                logger.error(
                    f"Can't connect to Websocket client on address: {self.solana_ws_endpoint}."
                )
                raise ClientRPCConnectionException(message.message)

            self.subscription_id = message.result
            logger.info(
                f"Subscribe to Solana blockchain. Subscription id: {self.subscription_id}."
            )
            logger.info(f"Websocket client subscribed with account: {account}.")
            try:
                async for transaction in self.ws_client:
                    signature: str = transaction.result.value.signature
                    timestamp: int = time_ns()

                    yield signature, timestamp
            except ConnectionClosedError as error:
                logger.error("Websocket client connection unexpectedly closed.")
                logger.error(error)

                self.ws_client = None
                raise ClientRPCConnectionClosedException(error) from error
            except ValidationError:
                logger.error("Error deserializing transaction hash.")

    async def unsubscribe(self) -> None:
        if self.subscription_id is None:
            logger.info("Client is not subscribed to transaction logs.")
            return

        if self.ws_client is not None:
            await self.ws_client.logs_unsubscribe(self.subscription_id)
            logger.info("Websocket client is unsubscribed from logs.")

    def ws_client_connected(self) -> bool:
        return self.ws_client is not None

    def _auth_ws_endpoint(self, ws_endpoint: str) -> str:
        ws_username = get_env_variable("SOLANA_RPC_WS_USERNAME")
        ws_password = get_env_variable("SOLANA_RPC_WS_PASSWORD")

        if ws_username and ws_password:
            if ws_endpoint.startswith("wss://"):
                ws_endpoint = ws_endpoint.replace(
                    "wss://", f"wss://{ws_username}:{ws_password}@"
                )
            elif ws_endpoint.startswith("ws://"):
                ws_endpoint = ws_endpoint.replace(
                    "ws://", f"ws://{ws_username}:{ws_password}@"
                )

        return ws_endpoint
