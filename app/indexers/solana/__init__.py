import logging
import asyncio

import multiprocess as mp
from typing import Set

import click
import multiprocessing_logging

from .aio_transaction_listeners import (
    listen_to_market_events,
    MENTIONS
)
from app.blockchains.solana import MARKET_NAME_MAP, ParsedTransaction, nft_get_metadata_by_token_key
from ...utils.streamer import KinesisStreamer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

multiprocessing_logging.install_mp_handler(logger)


async def _stop(loop):
    loop.stop()


async def _do_listent_to_market_events(market_id, streamer):
    try:
        async for sig, timestamp_ns in listen_to_market_events(market_id):
            streamer.put([(sig, timestamp_ns)])

    except asyncio.CancelledError:
        raise


def listen_to_market_events_wrapper(market_id, timeout, log_only, stream_name, region, endpoint_url):
    streamer = KinesisStreamer(
        stream_name, region, endpoint_url, dummy=log_only
    )
    if not timeout:
        asyncio.run(_do_listent_to_market_events(market_id, streamer))
    else:
        loop = asyncio.new_event_loop()
        future = asyncio.ensure_future(
            asyncio.wait_for(
                _do_listent_to_market_events(market_id, streamer),
                timeout=timeout,
                loop=loop
            ),
            loop=loop
        )
        try:
            loop.run_until_complete(future)
        except asyncio.exceptions.TimeoutError:
            logger.info(
                f"Timeout ({timeout}) triggered. Terminating."
            )
            if not future.cancelled():
                future.cancel()
                # Gives it a chance for the task to be set to cancelled from pending
                loop.run_until_complete(asyncio.sleep(0.1, loop=loop))
            loop.stop()
        except:
            if not future.cancelled():
                future.cancel()
                # Gives it a chance for the task to be set to cancelled from pending
                loop.run_until_complete(asyncio.sleep(0.1, loop=loop))
            loop.stop()
            raise
        finally:
            loop.close()


@click.command(name='solana-sme')
@click.argument('stream-name', nargs=1)
@click.argument('market-ids', nargs=-1)
@click.option('-t', '--runtime', type=int, default=0)
@click.option('-l', '--log-only', is_flag=True, default=False)
@click.option('--region', type=str, default='us-west-2')
@click.option('--endpoint-url', type=str, default=None)
def solana_sme(stream_name, market_ids: Set[int], runtime, log_only, region, endpoint_url):
    """
    Starts Solana Secondary Market Events listener on specified Market Id.

    E.g.,

    $ ./main producer solana-sme LocalTest 65793 -t 120 -l
    """
    if not stream_name:
        logger.error("No stream name given.")
    if not market_ids:
        logger.error("No market IDs given.")
        return
    if any([v == 'all' for v in market_ids]):
        market_ids = MENTIONS.keys()
    else:
        market_ids = set([int(k) for k in market_ids])
        invalid_market_ids = market_ids - MENTIONS.keys()
        if invalid_market_ids:
            logger.error(f"Invalid market IDs {invalid_market_ids}.")
            return

    processes = []
    for market_id in market_ids:
        p = mp.Process(
            target=listen_to_market_events_wrapper,
            args=(market_id, runtime, log_only, stream_name, region, endpoint_url),
        )
        processes.append(p)
        p.start()
        logger.info("Subprocess for %s started (PID=%s).", MARKET_NAME_MAP[market_id], p.pid)

    for p in processes:
        p.join()
