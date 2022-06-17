import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, List

from src.async_client import SolanaHTTPClient
from src.config import settings
from src.exception import (
    DecodingException,
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
    TransactionParserNotFoundException,
    UnknownTransactionException,
)
from src.model import SecondaryMarketEvent, SignatureEvent, Transaction
from src.parsing import TransactionParsing
from src.producer import KinesisProducer

logger = logging.getLogger(__name__)

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def lambda_handler(event: Dict[str, Any], context):
    logger.info("Connecting to Kinesis service...")

    kinesis: KinesisProducer = KinesisProducer(
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_REGION"),
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
    parsing_service: TransactionParsing = TransactionParsing()

    records = event["Records"]

    logger.info(f"Records count: {len(records)}. Processing signatures..")

    sme_batch: List[SecondaryMarketEvent] = []

    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)

    for record in records:
        try:
            logger.info("Received record: " + str(record))
            signature_data = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            signature_record = json.loads(signature_data)
            signature_event: SignatureEvent = SignatureEvent.from_dict(signature_record)

            transaction_dict = async_loop.run_until_complete(
                get_transaction(solana_client, signature_event)
            )

            if not transaction_dict:
                continue

            logger.info("Parsing transaction details: " + str(transaction_dict))

            transaction = Transaction.from_dict(transaction_dict)

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

        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
            logger.error(error)
            raise DecodingException("Failed to decode signature record.") from error

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
    response = await client.get_transaction(event.signature)

    transaction_dict = None

    logger.info("Got response: " + str(response))

    if response["error"]:
        logger.error("Error occurred while fetching transaction data: " + str(response["error"]))
    else:
        transaction_dict = response["result"]

    return transaction_dict
