# Lambda Handler for consuming the Kinesis data stream
import asyncio
import logging
import os
import time
from typing import List, Tuple, Optional

import aiohttp
import boto3
import httpx
import orjson
from aiohttp import ClientTimeout
from httpx import Timeout

from app import settings
from app.blockchains import (
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_SALE_AUCTION
)
from app.blockchains.solana import (
    ParsedTransaction,
    nft_get_metadata_by_token_key,
    CustomAsyncClient
)
from app.blockchains.solana.client import (
    nft_get_nft_data, SolanaNFTMetaData, nft_get_token_account_by_token_key, nft_get_metadata_by_token_account_async,
    transform_nft_data
)
from app.models import SecondaryMarketEvent, NFTRepository, SMERepository, NftData
from app.utils import notify_error, full_stacktrace
from app.utils.streamer import KinesisStreamer, KinesisStreamRecord

logger = logging.getLogger(__name__)

no_raise = os.getenv('CONSUMER_NO_RAISE')


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
        if no_raise:
            logger.error(str(e))
        else:
            raise
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


async def get_nft_metadata(client, index, token_key) -> Tuple[int, Optional[NftData]]:
    try:
        metadata_pda_key = nft_get_token_account_by_token_key(token_key)
        nft_metadata = await nft_get_metadata_by_token_account_async(metadata_pda_key, client)
        return index, nft_metadata
    except Exception as e:
        logger.error("Failed to fetch NFT metadata for %s (%s)", token_key, str(e))
        return index, None


async def get_nft_metadata_list(client, sme_list, loop) -> List[Optional[SolanaNFTMetaData]]:
    """

    Args:
        client:
        sme_list:

    Returns:
        Tuple of list of SolanaNFTMetaData, and a list of failed-to-fetch token_keys
    """
    sme_list_len = len(sme_list)
    ret = [None] * sme_list_len
    failed_retriable = {i for i in range(sme_list_len)}
    tries = 2
    while tries > 0 and sme_list:
        task_list = [
            get_nft_metadata(client, i, event.token_key)
            for i, event in enumerate(sme_list) if i in failed_retriable
        ]
        results = await asyncio.gather(*task_list, loop=loop)

        failed_retriable = set()
        for i, nft_metadata in results:
            if nft_metadata:
                ret[i] = nft_metadata
            else:
                failed_retriable.add(i)

        if failed_retriable:
            time.sleep(1)
        tries -= 1
    return ret


async def get_nft_data(client, index, uri) -> Tuple[int, NftData]:
    try:
        async with client.get(uri) as resp:
            data = await resp.json()
        return index, data
    except Exception as e:
        logger.error("Failed to fetch NFT data from uri (%s) (%s)", uri, str(e))
        return index, None


async def get_nft_data_list(nft_metadata_list: List[SolanaNFTMetaData],
                            current_owner_list: List[str], client, loop) -> List[NftData]:
    nft_metadata_list_len = len(nft_metadata_list)
    ret = [None] * nft_metadata_list_len
    failed_retriable = {i for i in range(nft_metadata_list_len)}
    tries = 2
    while tries > 0 and nft_metadata_list:
        task_list = [
            get_nft_data(client, i, metadata.uri)
            for i, metadata in enumerate(nft_metadata_list)
            if metadata and metadata.uri and i in failed_retriable
        ]
        results = await asyncio.gather(*task_list, loop=loop)

        failed_retriable = set()
        for i, nft_metadata_ex in results:
            if nft_metadata_ex:
                try:
                    ret[i] = transform_nft_data(
                        nft_metadata_list[i],
                        nft_metadata_ex,
                        current_owner_list[i]
                    )
                except Exception as e:
                    ret[i] = None
                    logger.error("Error transforming NFT data. %s ", full_stacktrace())
            else:
                failed_retriable.add(i)

        if failed_retriable:
            time.sleep(1)
        tries -= 1
    return ret


def write_to_local(succeeded_items_to_commit, file_name='smes.json'):
    """
    For local testing purpose only.

    Returns:

    """
    with open(file_name, 'a') as fd:
        for e, n in succeeded_items_to_commit:
            fd.write(orjson.dumps((e.dict(), n.dict())).decode('utf8'))
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
    logger.info(
        "Received signatures: %s", transaction_hashes
    )

    failed_transaction_hashes = []
    sme_list = []  # List of Secondary Market Events
    async with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT, timeout=15) as client:
        await client.is_connected()
        max_retries = 3
        while max_retries > 0:
            sme_list_temp, failed_transaction_hashes = await get_smes(
                client,
                transaction_hashes,
                loop
            )
            sme_list.extend(sme_list_temp)
            if not failed_transaction_hashes:
                break
            transaction_hashes = failed_transaction_hashes
            max_retries -= 1
            time.sleep(2)

    succeeded_items_to_commit = []
    if sme_list:
        current_owner_list = [
            event.buyer if event.event_type in {
                SECONDARY_MARKET_EVENT_SALE,
                SECONDARY_MARKET_EVENT_SALE_AUCTION,
            } else event.owner for event in sme_list
        ]
        async with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT, timeout=15) as client:
            await client.is_connected()
            # The returned nft_metadata_list is the same length as the input sme_list
            # and keeps the same order. Failed spot will be set None instead of
            # SolanaNFTMetadata instance. So later it will be easier to stitch
            nft_metadata_list = await get_nft_metadata_list(
                client,
                sme_list,
                loop
            )

        async with aiohttp.ClientSession(timeout=ClientTimeout(total=15.0), requote_redirect_url=False) as client:
            nft_data_list = await get_nft_data_list(
                nft_metadata_list, current_owner_list, client, loop
            )

        succeeded_items_to_commit = list(
            filter(lambda o: o[1], zip(sme_list, nft_data_list))
        )

    if succeeded_items_to_commit:
        dynamodb_resource = boto3.resource(
            'dynamodb', endpoint_url=settings.DYNAMODB_ENDPOINT
        )
        sme_repository = SMERepository(
            dynamodb_resource
        )
        nft_repository = NFTRepository(
            dynamodb_resource
        )
        _, failed = sme_repository.save_sme_with_nft_batch(succeeded_items_to_commit)
        if failed:
            notify_error(IOError(
                f"Error saving some items: {orjson.dumps(failed)}"
            ), metadata={})

        _, nft_data_list = zip(*succeeded_items_to_commit)
        _, failed = nft_repository.save_nfts(nft_data_list)
        if failed:
            notify_error(IOError(
                f"Error saving some items:  {orjson.dumps(failed)}"
            ), metadata={})
    logger.info(
        ">> Handled signatures: %s", [e.transaction_hash for e, _ in succeeded_items_to_commit]
    )
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
