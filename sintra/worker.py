# pylint: disable=redefined-outer-name
from __future__ import annotations

import asyncio
import logging
import sys
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Type

from sintra.blockchain.utils import (
    market_accounts,
    market_name_map,
    market_program_id_map,
    get_blockchain_id,
)
from sintra.config import settings
from sintra.exception import (
    ClientRPCConnectionClosedException,
    EnvironmentVariableMissingException,
    ProduceRecordFailedException,
)
from sintra.kinesis.producer import KinesisProducer
from sintra.kinesis.record import KinesisRecord
from sintra.subscriber.ethereum import EthereumRPCClient
from sintra.subscriber.solana import SolanaRPCClient
import os

alchemy_api_key = os.getenv("ALCHEMY_API_KEY")

logger = logging.getLogger(__name__)


class TransactionWorker(ABC):
    @abstractmethod
    async def listen_for_transactions(
        self,
        blockchain_id: int,
        market: str,
        market_address: int,
        market_accounts: List[str],
    ) -> None:
        """Subscribe to RPC client, listen for transaction signatures
        and send them to sink connector.

        Args:
            blockchain_id: (int): ID of blockchain.
            market (str):  Name of secondary marketplace where transaction originates from.
            market_address (int): Secondary marketplace address.
            market_accounts (List(str)): List of secondary marketplace accounts.

        """

    @classmethod
    @abstractmethod
    def build_from_settings(cls) -> TransactionWorker:
        """Build worker class from environment variables."""


class SolanaTransactionWorker(TransactionWorker):
    def __init__(
        self,
        http_endpoint: str,
        http_timeout: float,
        ws_endpoint: str,
        ws_timeout: float,
        stream_name: str,
    ) -> None:
        self.solana_rpc_client = SolanaRPCClient(
            http_endpoint,
            http_timeout,
            ws_endpoint,
            ws_timeout,
        )
        self.kinesis = KinesisProducer()
        self.stream_name = stream_name

    async def listen_for_transactions(
        self,
        blockchain_id: int,
        market: str,
        market_address: int,
        market_accounts: List[str],
    ) -> None:
        while True:
            try:
                async for signature, timestamp in self.solana_rpc_client.listen_for_transactions(
                    market_accounts
                ):
                    logger.info(
                        f"Transaction signature: {signature} with timestamp: {timestamp} from worker: {id(self)}"
                    )
                    record = KinesisRecord(
                        blockchain_id=blockchain_id,
                        market=market,
                        market_address=market_address,
                        market_account=market_accounts[0],
                        signature=signature,
                        timestamp=timestamp,
                    )
                    self.kinesis.produce_record(self.stream_name, record, signature)
            except ClientRPCConnectionClosedException as error:
                logger.error(error)
                logger.info("Reconnecting Websocket client...")
            except ProduceRecordFailedException:
                logger.info("Can't send record to Kinesis. Closing...")
                sys.exit(1)

    @classmethod
    def build_from_settings(cls) -> SolanaTransactionWorker:
        return cls(
            settings.blockchain.solana.http.endpoint,
            settings.blockchain.solana.http.timeout,
            settings.blockchain.solana.ws.endpoint,
            settings.blockchain.solana.ws.timeout,
            settings.kinesis.stream,
        )


class EthereumTransactionWorker(TransactionWorker):
    def __init__(
        self,
        http_endpoint: str,
        http_timeout: float,
        ws_endpoint: str,
        ws_timeout: float,
        stream_name: str,
    ) -> None:
        self.ethereum_rpc_client = EthereumRPCClient(
            http_endpoint,
            http_timeout,
            ws_endpoint,
            ws_timeout,
        )
        self.kinesis = KinesisProducer()
        self.stream_name = stream_name

    async def listen_for_transactions(
        self,
        blockchain_id: int,
        market: str,
        market_address: int,
        market_accounts: List[str],
    ) -> None:
        while True:
            try:
                async for signature, timestamp in self.ethereum_rpc_client.listen_for_transactions(
                    market_accounts
                ):
                    logger.info(
                        f"Transaction signature: {signature} with timestamp: {timestamp} from worker: {id(self)}"
                    )
                    record = KinesisRecord(
                        blockchain_id=blockchain_id,
                        market=market,
                        market_address=market_address,
                        market_account=market_accounts[0],
                        signature=signature,
                        timestamp=timestamp,
                    )
                    self.kinesis.produce_record(self.stream_name, record, signature)
            except ClientRPCConnectionClosedException as error:
                logger.error(error)
                logger.info("Reconnecting Websocket client...")
            except ProduceRecordFailedException:
                logger.info("Can't send record to Kinesis. Closing...")
                sys.exit(1)

    @classmethod
    def build_from_settings(cls) -> EthereumTransactionWorker:
        return cls(
            f"{settings.blockchain.ethereum.http.endpoint}/{alchemy_api_key}",
            settings.blockchain.ethereum.http.timeout,
            f"{settings.blockchain.ethereum.ws.endpoint}/{alchemy_api_key}",
            settings.blockchain.ethereum.ws.timeout,
            settings.kinesis.stream,
        )


_WORKER_CLASSES: Dict[str, Type[TransactionWorker]] = {
    "solana": SolanaTransactionWorker,
    "ethereum": EthereumTransactionWorker,
}


def _build_worker(
    worker_type: str, default: Type[TransactionWorker] = SolanaTransactionWorker
) -> TransactionWorker:
    worker_class = _WORKER_CLASSES.get(worker_type, default)
    return worker_class.build_from_settings()


def start_worker(
    worker: TransactionWorker,
    blockchain_id: int,
    market: str,
    market_address: int,
    market_account: str,
) -> None:
    try:
        async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(async_loop)

        future = asyncio.ensure_future(
            asyncio.wait_for(
                worker.listen_for_transactions(
                    blockchain_id, market, market_address, [market_account]
                ),
                timeout=None,
            ),
            loop=async_loop,
        )
        async_loop.run_until_complete(future)
    except EnvironmentVariableMissingException as env_missing_error:
        logger.error(env_missing_error)
        sys.exit(1)
    except asyncio.exceptions.TimeoutError as error:
        logger.error(error)
        if not future.cancelled():
            future.cancel()
            async_loop.run_until_complete(asyncio.sleep(1))
            async_loop.stop()
    finally:
        async_loop.close()


if __name__ == "__main__":
    blockchain_id: int = get_blockchain_id(settings.worker.type)
    accounts: List[str] = list(set(market_accounts(settings.worker.type)))
    account_address_map: Dict[str, int] = market_program_id_map(settings.worker.type)
    address_name_map: Dict[int, str] = market_name_map(settings.worker.type)

    number_of_workers: int = len(accounts)
    thread_executor = ThreadPoolExecutor(max_workers=number_of_workers)

    try:
        for market_account in accounts:
            blockchain_id = blockchain_id
            market_address = account_address_map[market_account]
            market_name = address_name_map[market_address]

            worker: TransactionWorker = _build_worker(settings.worker.type)
            logger.info(
                f"Starting worker {id(worker)}  for market account {market_account}."
            )
            thread_executor.submit(
                start_worker,
                worker,
                blockchain_id,
                market_name,
                market_address,
                market_account,
            )
    except KeyboardInterrupt:
        logger.info("Shuting down worker.")
    finally:
        thread_executor.shutdown()
