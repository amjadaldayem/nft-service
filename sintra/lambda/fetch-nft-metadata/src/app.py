import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, List

from src.config import settings
from src.exception import DecodingException
from src.metadata import MetadataFetcher, SolanaMetadataFetcher
from src.model import NFTMetadata, SecondaryMarketEvent
from src.producer import KinesisProducer
from src.utils import ethereum_address, solana_address, solana_event_type

logger = logging.getLogger(__name__)

solana_metadata_fetcher: MetadataFetcher = SolanaMetadataFetcher()


def lambda_handler(event: Dict[str, Any], context):
    logger.info("Initializing Kinesis connection.")
    kinesis: KinesisProducer = KinesisProducer(
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_REGION"),
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
                nft_metadata = async_loop.run_until_complete(
                    get_nft_metadata(solana_metadata_fetcher, market_event)
                )
                nft_metadata.blockchain_id = market_event.blockchain_id
                nft_metadata.timestamp = market_event.timestamp

                if _solana_sale_or_auction(market_event):
                    nft_metadata.owner = market_event.buyer
                else:
                    nft_metadata.owner = market_event.owner

                nft_metadata.last_market_activity = solana_event_type(
                    market_event.event_type
                )
                nft_metadata.transaction_hash = market_event.transaction_hash
                nft_metadata_list.append(nft_metadata)
            elif market_event.blockchain_id == ethereum_address():
                logger.warning(
                    "Metadata fetcher for blockchain: {market_event.blockchain_id}, not implemented."
                )
                continue
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


def _solana_sale_or_auction(event: SecondaryMarketEvent) -> bool:
    return event.event_type in (
        settings.blockchain.solana.market.event.sale,
        settings.blockchain.solana.market.event.sale_auction,
    )
