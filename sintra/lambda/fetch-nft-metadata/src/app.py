import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, List

from src.config import settings
from src.exception import DecodingException, UnableToFetchMetadataException
from src.metadata import MetadataFetcher, SolanaMetadataFetcher, EthereumMetadataFetcher
from src.model import NFTMetadata, SecondaryMarketEvent
from src.producer import KinesisProducer
from src.utils import ethereum_address, solana_address, transaction_event_type

logger = logging.getLogger(__name__)

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

solana_metadata_fetcher: MetadataFetcher = SolanaMetadataFetcher()
ethereum_metadata_fetcher: MetadataFetcher = EthereumMetadataFetcher()


def lambda_handler(event: Dict[str, Any], context):
    logger.info("Initializing Kinesis connection.")

    localstack_active_var = str(settings.localstack.active).lower()
    localstack_active = localstack_active_var == "true"

    if localstack_active:
        logger.info("Localstack is active.")

    kinesis: KinesisProducer = KinesisProducer(
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_REGION"),
        localstack_active,
    )

    records = event["Records"]

    logger.info(f"Records count: {len(records)}. Processing secondary market events.")

    nft_metadata_list: List[NFTMetadata] = []

    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)

    for record in records:
        try:
            market_data = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            market_record = json.loads(market_data)
            market_event: SecondaryMarketEvent = SecondaryMarketEvent.from_dict(
                market_record
            )

            if market_event.blockchain_id == solana_address():
                try:
                    nft_metadata = async_loop.run_until_complete(
                        get_nft_metadata(solana_metadata_fetcher, market_event)
                    )

                    nft_metadata.blockchain_id = market_event.blockchain_id
                    nft_metadata.blocktime = market_event.blocktime
                    nft_metadata.price = market_event.price
                    nft_metadata.market_id = market_event.market_id

                    if _sale_or_auction(market_event):
                        nft_metadata.owner = market_event.buyer
                    else:
                        nft_metadata.owner = market_event.owner

                    nft_metadata.last_market_activity = transaction_event_type(
                        market_event.event_type
                    )
                    nft_metadata.transaction_hash = market_event.transaction_hash
                    nft_metadata_list.append(nft_metadata)
                except UnableToFetchMetadataException as error:
                    logger.error(error)
            elif market_event.blockchain_id == ethereum_address():
                try:
                    nft_metadata = async_loop.run_until_complete(
                        get_nft_metadata(ethereum_metadata_fetcher, market_event)
                    )

                    nft_metadata.blockchain_id = market_event.blockchain_id
                    nft_metadata.blocktime = market_event.blocktime
                    nft_metadata.price = market_event.price
                    nft_metadata.market_id = market_event.market_id

                    if _sale_or_auction(market_event):
                        nft_metadata.owner = market_event.buyer
                    else:
                        nft_metadata.owner = market_event.owner

                    nft_metadata.last_market_activity = transaction_event_type(
                        market_event.event_type
                    )
                    nft_metadata.transaction_hash = market_event.transaction_hash
                    nft_metadata_list.append(nft_metadata)
                except UnableToFetchMetadataException as error:
                    logger.error(error)
            else:
                logger.warning(
                    "Metadata fetcher for blockchain: {market_event.blockchain_id}, not implemented."
                )
                continue
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
            logger.error(error)
            raise DecodingException(
                "Failed to decode Secondary Market record."
            ) from error

    logger.info("Sending NFT metadata batch.")
    if len(nft_metadata_list) > 0:
        kinesis.produce_records(
            settings.kinesis.stream_name,
            nft_metadata_list,
        )

        return {"message": "Successfully processed signature batch."}

    return {"message": "Resulting batch of events is empty."}


async def get_nft_metadata(
    metadata_fetcher: MetadataFetcher, event: SecondaryMarketEvent
) -> NFTMetadata:
    nft_metadata = await metadata_fetcher.get_nft_metadata(event)

    return nft_metadata


def _sale_or_auction(event: SecondaryMarketEvent) -> bool:
    return event.event_type in (
        settings.blockchain.market.event.sale,
        settings.blockchain.market.event.sale_auction,
    )
