import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, List, Tuple

from src.async_client import SolanaHTTPClient
from src.config import settings
from src.exception import (
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
    TransactionParserNotFoundException,
    UnknownTransactionException,
)
from src.model import (
    EthereumTransaction,
    SecondaryMarketEvent,
    SignatureEvent,
    SolanaTransaction,
)
from src.parsing import TransactionParsing
from src.producer import KinesisProducer
from web3 import Web3

logger = logging.getLogger(__name__)

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def lambda_handler(event: Dict[str, Any], context):
    logger.info("Connecting to Kinesis service...")

    localstack_active_var = str(settings.localstack.active).lower()
    localstack_active = localstack_active_var == "true"

    if localstack_active:
        logger.info("Localstack is active.")

    kinesis: KinesisProducer = KinesisProducer(
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_REGION"),
        localstack_active,
    )

    logger.info(
        f"Initializing SolanaHTTPClient for endpoint: {settings.blockchain.solana.http.endpoint}."
    )

    solana_client: SolanaHTTPClient = SolanaHTTPClient(
        endpoint=settings.blockchain.solana.http.endpoint,
        timeout=settings.blockchain.solana.http.timeout,
        username=os.getenv("SOLANA_RPC_HTTP_USERNAME"),
        password=os.getenv("SOLANA_RPC_HTTP_PASSWORD"),
    )

    logger.info(
        f"Initializing AlchemyHTTPClient for endpoint: {settings.blockchain.ethereum.http.endpoint}."
    )

    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    alchemy_http_url = f"{settings.blockchain.ethereum.http.endpoint}/{alchemy_api_key}"
    http_provider = Web3.HTTPProvider(alchemy_http_url)
    alchemy_client = Web3(http_provider)

    parsing_service: TransactionParsing = TransactionParsing()

    records = event["Records"]

    logger.info(f"Records count: {len(records)}. Processing signatures..")

    sme_batch: List[SecondaryMarketEvent] = []

    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)

    for record in records:
        try:
            logger.info(f"Received record: {record}")
            signature_data = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            signature_record = json.loads(signature_data)
            signature_event: SignatureEvent = SignatureEvent.from_dict(signature_record)

            if signature_event.blockchain_id == int(
                settings.blockchain.address.solana, 0
            ):

                transaction_dict = async_loop.run_until_complete(
                    get_transaction(solana_client, signature_event)
                )

                if not transaction_dict:
                    logger.warning(
                        f"Could not fetch transaction details for transaction {signature_event.signature}."
                    )
                    continue

                transaction = SolanaTransaction.from_dict(transaction_dict)

                try:
                    secondary_market_event = parsing_service.parse(
                        transaction, signature_event.market_account
                    )
                    sme_batch.append(secondary_market_event)
                except TransactionParserNotFoundException as error:
                    logger.warning(error)
                    continue
                except (
                    TransactionInstructionMissingException,
                    UnknownTransactionException,
                    SecondaryMarketDataMissingException,
                ) as error:
                    logger.error(error)
                    raise RuntimeError from error
            elif signature_event.blockchain_id == int(
                settings.blockchain.address.ethereum, 0
            ):

                (
                    transaction_details,
                    transaction_receipt_event_logs,
                ) = async_loop.run_until_complete(
                    get_transaction_ethereum(alchemy_client, signature_event)
                )

                if not transaction_details:
                    logger.warning(
                        f"Could not fetch transaction details for transaction {signature_event.signature}."
                    )
                    continue

                if not transaction_receipt_event_logs:
                    logger.warning(
                        f"Could not fetch transaction receipt event logs for transaction {signature_event.signature}."
                    )
                    continue

                transaction = EthereumTransaction.from_dict(
                    transaction_details, transaction_receipt_event_logs
                )

                try:
                    secondary_market_event = parsing_service.parse(
                        transaction, signature_event.market_account
                    )
                    sme_batch.append(secondary_market_event)
                except (
                    TransactionInstructionMissingException,
                    UnknownTransactionException,
                    SecondaryMarketDataMissingException,
                    TransactionParserNotFoundException,
                ) as error:
                    logger.error(error)
                    continue

            else:
                logger.error(
                    f"Unknown blockchain name: {signature_event.blockchain_id}"
                )
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
            logger.error(error)

    logger.info("Sending secondary event batch.")
    if len(sme_batch) > 0:
        kinesis.produce_records(
            settings.kinesis.stream_name,
            sme_batch,
        )

        return {"message": "Successfully processed signature batch."}

    return {"message": "Resulting batch is empty."}


async def get_transaction(
    client: SolanaHTTPClient, event: SignatureEvent
) -> Dict[str, Any]:
    logger.info(f"Fetching transaction for signature: {event.signature}.")
    response = await client.get_confirmed_transaction(event.signature)
    logger.info(f"Fetched transaction data: {response}")

    transaction_dict = None

    if "error" in response:
        logger.error(
            f"Error occurred while fetching transaction data: {response['error']}"
        )
    elif "result" in response:
        transaction_dict = response["result"]

    return transaction_dict


async def get_transaction_ethereum(
    client: Web3,
    event: SignatureEvent,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    logger.info(f"Fetching transaction for signature: {event.signature}.")
    transaction_details = client.eth.get_transaction(event.signature)
    transaction_receipt_event_logs = client.eth.getTransactionReceipt(event.signature)
    logger.info(f"Fetched transaction details data: {transaction_details}")
    logger.info(
        f"Fetched transaction receipt event logs data: {transaction_receipt_event_logs}"
    )

    return transaction_details, transaction_receipt_event_logs
