# Lambda Handler for consuming the Kinesis data stream
import asyncio
import logging
from typing import List

import orjson

from app import settings
from app.models.nft import NFTRepository
from app.utils.streamer import KinesisStreamer, KinesisStreamRecord
from app.blockchains.solana import ParsedTransaction, nft_get_metadata_by_token_key, CustomAsyncClient
from app.utils import full_stacktrace

logger = logging.getLogger(__name__)


async def get_transaction(client, record: KinesisStreamRecord):
    signature, _ = orjson.loads(record.data)
    resp = await client.get_confirmed_transaction(signature)
    try:
        transaction_dict = resp['result']
        pt = ParsedTransaction.from_transaction_dict(transaction_dict)
        event = pt.event
        if event:
            metadata = nft_get_metadata_by_token_key(event.token_key)
            return metadata, record
    except Exception as e:
        logger.error(str(e))
        logger.error(full_stacktrace())

    return None, record


async def handle_transactions(records: List[KinesisStreamRecord],
                              loop: asyncio.AbstractEventLoop):
    if not records:
        return

    # first_record = records[0]

    with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT, timeout=60) as client:
        await client.is_connected()
        # Data: [signature, timestamp_ns]
        task_list = [
            get_transaction(client, record)
            for record in records
        ]
        results = await asyncio.gather(*task_list, loop=loop)

        failed_record = None
        for i, metadata, record in enumerate(results):
            if not metadata:
                # Failed record at which we bisect
                failed_record = record
                break
        # Trim the result to the succeeded entries
        succeeded = results[:i]
        if succeeded:
            # Persistence, note that if the persistence fails, we will retry all
            # from the first record
            # Emits to Websocket
            # TODO: Write to DynamoDB and emit Websocket events

        return failed_record


handler = KinesisStreamer(
    settings.SOLANA_SME_KINESIS_STREAM,
    region=settings.AWS_REGION
).wrap_handler(handle_transactions)
