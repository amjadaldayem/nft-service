# Lambda Handler for consuming the Kinesis data stream
# TODO: Definitely the most efficient pipelining here
#   1. Maybe change it to traditional multi-threading / multi-processing instead
#       of `async` since most of the operations here are IO bound instead of CPU bound.
#   2. Better pipelining -- now there is a waste of time on the retry part.
import asyncio
import logging
import os
from typing import List, Tuple, Optional
from datetime import datetime

import aiohttp
import boto3
import orjson
from aiohttp import ClientTimeout

from app import settings
from app.blockchains import (
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_SALE_AUCTION
)
from app.blockchains.solana import (
    ParsedTransaction,
    CustomAsyncClient
)
from app.blockchains.solana.client import (
    nft_get_token_account_by_token_key,
    nft_get_metadata_by_token_account_async,
    transform_nft_data,
    SolanaNFTMetaData
)
from app.models import (
    SecondaryMarketEvent,
    NFTRepository,
    SMERepository,
    NftData
)
from app.utils import (
    notify_error,
    http
)
from app.utils.parallelism import retriable_map
from app.utils.streamer import KinesisStreamer, KinesisStreamRecord
from app.utils.sme_events_publisher import publish_sme_events_to_kinesis

logger = logging.getLogger(__name__)

no_raise = os.getenv('CONSUMER_NO_RAISE')


async def get_nft_metadata(input_data) -> Tuple[Optional[SolanaNFTMetaData], bool]:
    """
    Gets Solana specific NFT Metadata from token (mint) key.

    Args:
        input_data:

    Returns:

    """
    client, sme = input_data
    if not sme:
        return None, True
    try:
        metadata_pda_key = nft_get_token_account_by_token_key(sme.token_key)
        nft_metadata = await nft_get_metadata_by_token_account_async(
            metadata_pda_key, client
        )
        return nft_metadata, True
    except:
        return None, False


async def get_nft_data(input_data) -> Tuple[Optional[NftData], bool]:
    """
    Fetches the JSON data from the URI carried by the Metadata.

    Args:
        input_data:

    Returns:
        Tuple of standard NftData (can be None) and if succeeds in fetching.
        We consider a None input of nft_metadata as success, so just return
        None, True.
    """
    client, nft_metadata = input_data
    if not nft_metadata:
        return None, True
    try:
        async with client.get(nft_metadata.uri, allow_redirects=True) as resp:
            data = await http.get_json(resp)
        return data, True
    except:
        return None, False


async def get_transaction(input_data) -> Optional[dict]:
    """
    Download the transaction data.

    Args:
        input_data: Tuple of (async_client, transaction_hash)

    Returns:
        Tuple: Transaction dict or None, if the request succeeds or not (excepted)
    """
    async_client, transaction_hash = input_data
    try:
        resp = await async_client.get_confirmed_transaction(transaction_hash)
        transaction_dict = resp['result']
        return transaction_dict
    except:
        return None


async def parse_transaction(transaction_dict) -> Optional[SecondaryMarketEvent]:
    try:
        pt = ParsedTransaction.from_transaction_dict(transaction_dict)
        return pt.event
    except Exception as e:
        logger.error(str(e))
        # Non-captured error, but do not retry
        return None


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


async def save_to_db(dynamodb_resource, succeeded_items_to_commit):
    """

    Args:
        dynamodb_resource:
        succeeded_items_to_commit:

    Returns:

    """
    dynamodb_resource = dynamodb_resource or boto3.resource(
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


async def handle_transactions(records: List[KinesisStreamRecord],
                              loop: asyncio.AbstractEventLoop,
                              dynamodb_resource=None):
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
    for _ in range(1):
        async with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT, timeout=10) as client:
            await client.is_connected()
            transaction_dict_list, failed_input_list = await retriable_map(
                get_transaction,
                [(client, t) for t in transaction_hashes],
                success_test=lambda d: (d, bool(d)),
                max_retries=2,
                wait_strategy='backoff'
            )
            if failed_input_list:
                _, failed_transaction_hashes = zip(*failed_input_list)

            # Skips the errored transactions
            transaction_dict_list = [t for t in transaction_dict_list if t and t['meta']['err'] is None]
            sme_list = []
            transaction_non_events = []
            for t in transaction_dict_list:
                parsed = await parse_transaction(t)
                if parsed:
                    sme_list.append(parsed)
                else:
                    transaction_non_events.append(t['transaction']['signatures'][0])

            if transaction_non_events:
                logger.warning("Transactions parsing failed: %s", transaction_non_events)

            if not sme_list:
                # Early exit
                logger.warning("No SecondaryMarketEvents parsed.")
                break
            # Keep nft_metadata_list the same length as the sme_list
            nft_metadata_list, failed_input_list = await retriable_map(
                get_nft_metadata,
                [(client, e) for e in sme_list],
                max_retries=2,
                wait_strategy='backoff'
            )
            if failed_input_list:
                nft_fetching_failed = [e.transaction_hash for _, e in failed_input_list]
                logger.warning("Transactions with NFT metadata fetching failed: %s", nft_fetching_failed)
                failed_transaction_hashes.extend(nft_fetching_failed)

        # Now we have the SecondaryMarketEvent list ready.
        current_owner_list = [
            event.buyer if event.event_type in {
                SECONDARY_MARKET_EVENT_SALE,
                SECONDARY_MARKET_EVENT_SALE_AUCTION,
            } else event.owner for event in sme_list
        ]

        async with aiohttp.ClientSession(timeout=ClientTimeout(total=10.0), requote_redirect_url=False) as client:
            nft_json_data_list, failed_input_list = await retriable_map(
                get_nft_data,
                [(client, n) for n in nft_metadata_list],
                max_retries=2,
                wait_strategy='backoff'
            )
            if failed_input_list:
                logger.warning("NFT metadata URIs fetching faild: %s",
                               [(n.mint_key, n.uri) for _, n in failed_input_list if n])
            # Transforms to NFTData
            sme_len = len(sme_list)
            nft_data_list = [
                transform_nft_data(
                    nft_metadata_list[i], nft_json_data_list[i], current_owner_list[i]
                ) for i in range(sme_len)
            ]

        # Skips any None NFT data
        succeeded_items_to_commit = list(
            filter(lambda o: o[1], zip(sme_list, nft_data_list))
        )

        if not succeeded_items_to_commit:
            break

        await save_to_db(dynamodb_resource, succeeded_items_to_commit)
        publish_events(succeeded_items_to_commit)
        # for e, n in succeeded_items_to_commit:
        #     logger.info("%s\n%s", orjson.dumps(e.dict()), orjson.dumps(n.dict()))

        logger.info(
            ">> Handled signatures: %s", [e.transaction_hash for e, _ in succeeded_items_to_commit]
        )

    if failed_transaction_hashes:
        # Pin the failed record from where we want to retry next
        # We just throw in multiple records, and kinesis will take the
        # one with the lowest sequence id
        failed_transaction_hashes = set(failed_transaction_hashes)
        logger.error("Transactions failed to fetch or did not yield correct NFT info: %s",
                     failed_transaction_hashes)
        return [
            record for record in records if record.data[0] in failed_transaction_hashes
        ]
    return


def publish_events(events):
    try:
        current_hour = datetime.utcnow().strftime("%Y-%d-%m-%H")
        published_events = [{"data": event, "eventPartitionKey": current_hour} for event in events]
        publish_sme_events_to_kinesis(published_events)
    except Exception as error:
        logger.error(error)


# For Lambda handler
handler = KinesisStreamer.wrap_handler(handle_transactions)
