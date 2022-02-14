# Lambda Handler for consuming the Kinesis data stream
import asyncio
import logging
from typing import List, Tuple, Optional

import boto3
import orjson
from solana.rpc import commitment

from app import settings
from app.blockchains import SECONDARY_MARKET_EVENT_SALE
from app.blockchains.solana import ParsedTransaction, nft_get_metadata_by_token_key, CustomAsyncClient, CustomClient
from app.blockchains.solana.client import (
    nft_get_nft_data
)
from app.models import (
    NFTRepository,
    SMERepository
)
from app.models import SecondaryMarketEvent
from app.utils import notify_error
from app.utils.streamer import KinesisStreamer, KinesisStreamRecord

logger = logging.getLogger(__name__)


async def get_sme(client, transaction_hash: str) -> Tuple[str, bool, Optional[SecondaryMarketEvent]]:
    """

    Args:
        client:
        transaction_hash:

    Returns:
        The input transaction_hash, flag marking if fetching succeeded (False means
        we might need to retry),and a SecondaryMarketEvent (will be None
        if the fetching failed)
    """
    try:
        resp = await client.get_confirmed_transaction(transaction_hash)
        transaction_dict = resp['result']
        if transaction_dict is None:
            return transaction_hash, False, None
    except:
        return transaction_hash, False, None

    if transaction_dict['meta']['err']:
        # Nothing to do for failed transactions
        return transaction_hash, True, None

    try:
        pt = ParsedTransaction.from_transaction_dict(transaction_dict)
        event = pt.event
        return transaction_hash, True, event
    except Exception as e:
        logger.error(str(e))
        # logger.error(full_stacktrace())
        # Non-captured error, but do not retry
        return transaction_hash, True, None


async def get_smes(client, transaction_hashes: List[str], loop) -> Tuple[List[SecondaryMarketEvent], List[str]]:
    task_list = [
        get_sme(client, transaction_hash)
        for transaction_hash in transaction_hashes
    ]
    results = await asyncio.gather(*task_list, loop=loop)

    # Retry
    failed_retriable = []
    succeeded_events = []
    for i, (transaction_hash, succeeded, event) in enumerate(results):
        if not succeeded:
            failed_retriable.append(transaction_hash)
            continue
        if not event:
            continue
        succeeded_events.append(event)

    return succeeded_events, failed_retriable


def write_to_local(succeeded_items_to_commit):
    """
    For local testing purpose only.

    Returns:

    """
    with open('smes.json', 'a') as fd:
        for e, n in succeeded_items_to_commit:
            fd.write(orjson.dumps((e, n)).decode('utf8'))
            fd.write(',')
            fd.flush()


async def handle_transactions(records: List[KinesisStreamRecord],
                              loop: asyncio.AbstractEventLoop):
    if not records:
        return

    transaction_hashes = [
        record.data[0]
        for record in records
    ]
    failed_transaction_hashes = []
    async with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT, timeout=60) as client:
        await client.is_connected()
        max_retries = 3
        while max_retries > 0:
            sme_list, failed_transaction_hashes = await get_smes(
                client,
                transaction_hashes,
                loop
            )
            if not failed_transaction_hashes:
                break
            transaction_hashes = failed_transaction_hashes
            max_retries -= 1

    succeeded_items_to_commit = []
    if sme_list:
        # Metadata is Solana specific, can be None if fetching failed
        client = CustomClient(
            settings.SOLANA_RPC_ENDPOINT,
            commitment=commitment.Confirmed,
            timeout=15
        )

        for event in sme_list:
            try:
                metadata = nft_get_metadata_by_token_key(event.token_key, client=client)
                # Nft_data is shared format across all chains, generic
                nft_data = nft_get_nft_data(
                    metadata,
                    current_owner=(
                        event.buyer if event.event_type == SECONDARY_MARKET_EVENT_SALE
                        else event.owner
                    )
                )
                succeeded_items_to_commit.append((event, nft_data))
            except Exception as e:
                failed_transaction_hashes.append(event.transaction_hash)
                logger.error(str(e))

    dynamodb_resource = boto3.resource('dynamodb')
    sme_repository = SMERepository(
        dynamodb_resource
    )
    nft_repository = NFTRepository(
        dynamodb_resource
    )
    _, failed = sme_repository.save_sme_with_nft_batch(succeeded_items_to_commit)
    if failed:
        notify_error(IOError(
            f"Error saving some items: {sme_repository.NAME}"
        ), metadata={
            'details': orjson.dumps(failed).decode('utf8'),
        })

    _, nft_data_list = zip(*succeeded_items_to_commit)
    _, failed = nft_repository.save_nfts(nft_data_list)
    if failed:
        notify_error(IOError(
            f"Error saving some items:  {nft_repository.NAME}"
        ), metadata={
            'details': orjson.dumps(failed).decode('utf8'),
        })

    if failed_transaction_hashes:
        # Pin the failed record from where we want to retry next
        # We just throw in multiple records, and kinesis will take the
        # one with the lowest sequence id
        failed_transaction_hashes = set(failed_transaction_hashes)
        return [
            record for record in records if record.data[0] in failed_transaction_hashes
        ]
    return


# For Lambda handler
handler = KinesisStreamer.wrap_handler(handle_transactions)
