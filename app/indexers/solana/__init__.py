import asyncio
import logging
import os
import signal
import threading
from typing import Set

import multiprocessing_logging
import pylru

from app import settings
from app.blockchains.solana import MARKET_NAME_MAP
from app.utils.parallelism import ProcessManager
from app.utils.streamer import KinesisStreamer
from .aio_transaction_listeners import (
    listen_to_market_events,
    MENTIONS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

multiprocessing_logging.install_mp_handler(logger)


async def _stop(loop):
    loop.stop()


# Memorize recent 1,000 items
local_cache = pylru.lrucache(1000)


async def _do_listent_to_market_events(market_id, streamer):
    try:
        async for sig, timestamp_ns in listen_to_market_events(market_id):
            if sig in local_cache:
                continue
            local_cache[sig] = 1
            streamer.put([(sig, timestamp_ns)])
    except Exception as e:
        # We need to notify the parent process to exit.
        # Since we are using ECS, it will relaunch.
        logger.error(str(e))
        raise


def listen_to_market_events_wrapper(market_id, timeout, stream_name, region, endpoint_url):
    logger.info("Subprocess for %s started (PID=%s).", MARKET_NAME_MAP[market_id], os.getpid())
    from app.indexers.solana.sme_indexer import handle_transactions
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    producer_level = settings.SOLANA_SME_PRODUCER_MODE
    streamer = KinesisStreamer(
        stream_name, region, endpoint_url,
        producer_mode=producer_level,
        handler=KinesisStreamer.wrap_local_handler(handle_transactions)
    )

    future = asyncio.ensure_future(
        asyncio.wait_for(
            _do_listent_to_market_events(market_id, streamer),
            timeout=timeout or None,
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
        streamer.kill_local_poller()
        loop.stop()
    except:
        if not future.cancelled():
            future.cancel()
            # Gives it a chance for the task to be set to cancelled from pending
            loop.run_until_complete(asyncio.sleep(0.1, loop=loop))
        streamer.kill_local_poller()
        loop.stop()
        raise
    finally:
        loop.close()


latch = threading.Event()


def do_solana_sme(stream_name, market_ids: Set[int], runtime, region, endpoint_url):
    """
    Starts Solana Secondary Market Events listener on Market Id set or `all`.
    This will run as the producers for Kinesis data stream messages.

    --producer_mode 0: normal kinesis producer, 1: log only 2: local handler invocation (for testing)
    E.g.,

    $ ./main producer solana-sme LocalTest 65793 -t 120 -l 0
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

    process_managers = {}
    # For each market we spin up a subprocess
    # and to make sure we have a reasonable restart mechanism,
    # we need to restart a subprocess if it raised / terminated by chance.
    for market_id in market_ids:
        process_managers[market_id] = ProcessManager(
            target=listen_to_market_events_wrapper,
            args=(market_id, runtime, stream_name, region, endpoint_url),
        )

    normally_exited = {market_id: False for market_id in market_ids}

    def _release_latch(signum, frame):
        latch.set()

    signal.signal(signal.SIGALRM, _release_latch)
    if runtime:
        signal.alarm(runtime)

    while not latch.is_set():
        for market_id in market_ids:
            process_manager = process_managers[market_id]
            process = process_manager.process
            if not process:
                process_manager.start()
            else:
                if process.exitcode:
                    if process.exitcode != 0:
                        logger.info("Restarting subprocess for market %s", MARKET_NAME_MAP[market_id])
                        process_manager.start()
                    else:
                        # Exitcode = 0, normal exit
                        logger.info("Subprocess %s exited with code %s", process.pid, process.exitcode)
                        normally_exited[market_id] = True
        if all(normally_exited.values()):
            logger.info("All subprocesses exited normally.")
            break

        for pm in process_managers.values():
            p = pm.process
            if p:
                p.join(2)
    logger.info("Main Process Exit.")
