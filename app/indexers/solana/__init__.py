import logging
import time
import asyncio

import multiprocess as mp
from typing import Set

import asyncclick as click
import multiprocessing_logging

from .aio_transaction_listeners import (
    listen_to_market_events,
    MENTIONS
)
from app.blockchains.solana import MARKET_NAME_MAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

multiprocessing_logging.install_mp_handler(logger)


async def _do_listent_to_market_events(market_id):
    await asyncio.sleep(10)
    print(market_id)


def listen_to_market_events_wrapper(market_id, timeout):
    # async for signagure in listen_to_market_events(market_id):
    #     print(time.time_ns(), signagure)
    if not timeout:
        asyncio.run(_do_listent_to_market_events(market_id))
    else:
        loop = asyncio.new_event_loop()
        future = asyncio.wait_for(
            _do_listent_to_market_events(market_id),
            timeout=timeout
        )
        try:
            loop.run_until_complete(future)
        except asyncio.exceptions.TimeoutError:
            logger.info(
                f"Timeout ({timeout}) triggered. Terminating."
            )
        finally:
            loop.close()


@click.command(name='solana')
@click.argument('market-ids', nargs=-1)
@click.option('-r', '--runtime', type=int, default=0)
async def solana_sme(market_ids: Set[int], runtime):
    if not market_ids:
        logger.error(f"No market IDs given.")
        return
    market_ids = set([int(k) for k in market_ids])
    invalid_market_ids = market_ids - MENTIONS.keys()
    if invalid_market_ids:
        logger.error(f"Invalid market IDs {invalid_market_ids}.")
        return

    for market_id in market_ids:
        p = mp.Process(target=listen_to_market_events_wrapper, args=(market_id, runtime))
        p.start()
        logger.info("Subprocess for %s started.", MARKET_NAME_MAP[market_id])
        p.join()
