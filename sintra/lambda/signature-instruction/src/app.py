import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, List

from .async_client import SolanaHTTPClient
from .config import settings
from .exception import (
    DecodingException,
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
    TransactionParserNotFoundException,
    UnknownTransactionException,
)
from .model import SecondaryMarketEvent, SignatureEvent, Transaction
from .parsing import TransactionParsing
from .producer import KinesisProducer

logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context):
    kinesis: KinesisProducer = KinesisProducer(
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_REGION"),
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
            signature_data = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            signature_record = json.loads(signature_data)
            signature_event: SignatureEvent = SignatureEvent.from_dict(signature_record)

            transaction_dict = async_loop.run_until_complete(
                get_transaction(solana_client, signature_event)
            )
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
    transaction_dict = response["result"]

    return transaction_dict
