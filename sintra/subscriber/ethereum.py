import asyncio
import json
import logging
from time import time_ns
from typing import AsyncGenerator, List, Optional, Tuple

from websockets import connect
from websockets.client import WebSocketClientProtocol


from sintra.utils import get_env_variable

logger = logging.getLogger(__name__)


class EthereumRPCClient:
    def __init__(
        self,
        http_endpoint: str,
        http_timeout: float,
        ws_endpoint: str,
        ws_timeout: int,
    ) -> None:

        self.http_username = get_env_variable("ETHEREUM_RPC_HTTP_USERNAME")
        self.http_password = get_env_variable("ETHEREUM_RPC_HTTP_PASSWORD")
        self.http_endpoint = http_endpoint
        self.http_timeout = http_timeout

        self.ws_client: Optional[WebSocketClientProtocol] = None
        self.ws_timeout = ws_timeout
        self.ws_endpoint = self._auth_ws_endpoint(ws_endpoint)
        self.last_signature_recv: Optional[str] = None
        self.subscription_id: Optional[int] = None

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
            await self.ws_client.send(
                json.dumps(
                    {
                        "id": 1,
                        "method": "eth_subscribe",
                        "params": ["logs", {"address": accounts, "topics": []}],
                    }
                )
            )
            logger.info(f"Websocket client subscribed with account: {account}.")
            while True:
                try:
                    message = await asyncio.wait_for(
                        self.ws_client.recv(), timeout=self.ws_timeout
                    )
                    signature: str = json.loads(message)["params"]["result"][
                        "transactionHash"
                    ]
                    timestamp: int = time_ns()
                    yield signature, timestamp
                except json.JSONDecodeError as error:
                    logger.error("Decoding Ethereum subscription JSON has failed")
                    logger.error(error)
                except KeyError as error:
                    logger.error(
                        "There is no Ethereum transaction hash in received data."
                    )
                    logger.error(error)
                except asyncio.TimeoutException as error:
                    logger.error("Ethereum websocket timeout.")
                    logger.error(error)

    async def unsubscribe(self) -> None:
        if self.subscription_id is None:
            logger.info("Client is not subscribed to transaction logs.")
            return

        if self.ws_client is not None:
            await self.ws_client.close()
            logger.info("Websocket client is unsubscribed.")

    def ws_client_connected(self) -> bool:
        return self.ws_client is not None

    def _auth_ws_endpoint(self, ws_endpoint: str) -> str:
        ws_username = get_env_variable("ETHEREUM_RPC_WS_USERNAME")
        ws_password = get_env_variable("ETHEREUM_RPC_WS_PASSWORD")

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
