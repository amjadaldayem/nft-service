# This is where we define all the market listeners for Solana and emit
# transaction signatures
# Producers of Kinesis messages.
import logging
import time

import websockets
from aiostream import stream
from solana.rpc.websocket_api import connect
from websockets.exceptions import ConnectionClosedError

from app import settings
from app.blockchains.solana import (
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SOLANA_DIGITAL_EYES,
    SOLANA_SOLANART,
    SOLANA_SOLSEA,
    SOLANA_SMB,
    MAGIC_EDEN_PROGRAM_ACCOUNT,
    MAGIC_EDEN_PROGRAM_ACCOUNT_V2,
    MAGIC_EDEN_AUCTION_PROGRAM_ACCOUNT,
    ALPHA_ART_PROGRAM_ACCOUNT,
    DIGITAL_EYES_DIRECT_SELL_PROGRAM_ACCOUNT,
    DIGITAL_EYES_NFT_MARKETPLACE_PROGRAM_ACCOUNT,
    SOLANART_PROGRAM_ACCOUNT,
    SOLSEA_PROGRAM_ACCOUNT,
    SOLANA_MONKEY_BUSINESS_PROGRAM_ACCOUNT,
    CustomAsyncClient
)

# Add a known secondary market program account or some
# signature account that appears in log for us to subscribe.
MENTIONS = {
    SOLANA_MAGIC_EDEN: [
        MAGIC_EDEN_PROGRAM_ACCOUNT,
        MAGIC_EDEN_PROGRAM_ACCOUNT_V2,
        MAGIC_EDEN_AUCTION_PROGRAM_ACCOUNT,
    ],
    SOLANA_ALPHA_ART: [ALPHA_ART_PROGRAM_ACCOUNT],
    SOLANA_DIGITAL_EYES: [
        DIGITAL_EYES_DIRECT_SELL_PROGRAM_ACCOUNT,
        DIGITAL_EYES_NFT_MARKETPLACE_PROGRAM_ACCOUNT
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
    """
    Use WSS subscription to the transactions that mentions the program_account.

    This is not reliable and there will be missing transactions! That is why
    whenever we get a signature from ws, we immediately try fetching the transactions
    _before_ this signature and _until_ the last_read_signature, to make sure
    we made it up for the gap. This might cause the result to be somehow out of order.
    But at the end of the day they are stored in db with the block time. So all good.

    Args:
        program_account:

    Returns:

    """
    last_read_signature = None
    async with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT) as client:
        async for ws_client in reliable_websocket(endpoint=settings.SOLANA_RPC_WSS_ENDPOINT):
            await ws_client.logs_subscribe(
                {
                    'mentions': [program_account]
                }
            )
            resp = await ws_client.recv()
            sub_id = resp.result
            try:
                async for msg in ws_client:
                    try:
                        signature = msg.result.value.signature
                        yield signature, time.time_ns()
                        if last_read_signature:
                            # Try catch up missing events between (signature, last_read_signature)
                            await client.is_connected()
                            resp = await client.get_confirmed_signature_for_address2(
                                account=program_account,
                                before=signature,
                                until=last_read_signature,
                                limit=20  # this is really high limit though
                            )
                            result = resp.get('result', [])
                            for r in result:
                                # logger.info("Caught up: %s", r['signature'])
                                yield r['signature'], time.time_ns()
                        last_read_signature = signature
                    except Exception as e:
                        logger.error(str(e))
            finally:
                try:
                    await ws_client.logs_unsubscribe(sub_id)
                except ConnectionClosedError:
                    logger.error("Error occurred while trying to close connection.")
                    raise


async def reliable_websocket(endpoint):
    async for websocket in connect(endpoint):
        try:
            yield websocket
        except websockets.ConnectionClosed:
            logger.error("Websocket closed. Reconnecting")
            continue
        except:
            raise
