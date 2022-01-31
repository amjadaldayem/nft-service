# This is where we define all the market listeners for Solana and emit
# transaction signatures
# Producers of Kinesis messages.
import logging
import time

import websockets
from solana.rpc.websocket_api import connect
from aiostream import stream

from app import settings
from app.blockchains.solana import (
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SOLANA_DIGITAL_EYES,
    SOLANA_SOLANART,
    SOLANA_SOLSEA,
    SOLANA_SMB,
    MAGIC_EDEN_PROGRAM_ACCOUNT,
    ALPHA_ART_PROGRAM_ACCOUNT,
    DIGITAL_EYES_PROGRAM_ACCOUNT,
    DIGITAL_EYES_SALE_PROGRAM_ACCOUNT,
    SOLANART_PROGRAM_ACCOUNT,
    SOLSEA_PROGRAM_ACCOUNT,
    SOLANA_MONKEY_BUSINESS_PROGRAM_ACCOUNT
)

# Add a known secondary market program account or some
# signature account that appears in log for us to subscribe.
MENTIONS = {
    SOLANA_MAGIC_EDEN: [MAGIC_EDEN_PROGRAM_ACCOUNT],
    SOLANA_ALPHA_ART: [ALPHA_ART_PROGRAM_ACCOUNT],
    SOLANA_DIGITAL_EYES: [
        DIGITAL_EYES_PROGRAM_ACCOUNT,
        DIGITAL_EYES_SALE_PROGRAM_ACCOUNT
    ],
    SOLANA_SMB: [SOLANA_MONKEY_BUSINESS_PROGRAM_ACCOUNT],
    SOLANA_SOLSEA: [SOLSEA_PROGRAM_ACCOUNT],
    SOLANA_SOLANART: [SOLANART_PROGRAM_ACCOUNT]
}

logger = logging.getLogger(__name__)


async def listen_to_market_events(secondary_market_id):
    if secondary_market_id not in MENTIONS:
        logger.error("Unknown market ID")
        return

    accounts = MENTIONS[secondary_market_id]
    if len(accounts) == 1:
        async for sig, timestamp_ns in iter_events_for(accounts[0]):
            yield sig, timestamp_ns
    else:
        args = [iter_events_for(account) for account in accounts]
        merged_stream = stream.merge(*args)
        async with merged_stream.stream() as s:
            async for sig, timestamp_ns in s:
                yield sig, timestamp_ns


async def iter_events_for(program_account):
    async for client in reliable_websocket(endpoint=settings.SOLANA_RPC_WSS_ENDPOINT):
        await client.logs_subscribe(
            {
                'mentions': [program_account]
            }
        )
        resp = await client.recv()
        sub_id = resp.result
        try:
            async for msg in client:
                try:
                    signature = msg.result.value.signature
                    yield signature, time.time_ns()
                except Exception as e:
                    logger.error(str(e))
        finally:
            await client.logs_unsubscribe(sub_id)


async def reliable_websocket(endpoint):
    async for websocket in connect(endpoint):
        try:
            yield websocket
        except websockets.ConnectionClosed:
            continue
