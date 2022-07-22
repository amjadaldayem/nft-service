import asyncio
import base64
import json
import logging
import os
from typing import List

from src.config import settings
from src.exception import DecodingException, FetchTokenDataException
from src.model import NFTData, NFTMetadata
from src.producer import KinesisProducer
from src.token_data import (
    SolanaTokenDataFetcher,
    TokenDataFetcher,
    EthereumTokenDataFetcher,
)
from src.utils import ethereum_address, solana_address

logger = logging.getLogger(__name__)

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
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
    solana_token_fetcher: TokenDataFetcher = SolanaTokenDataFetcher(
        username=os.getenv("HTTP_USERNAME"),
        password=os.getenv("HTTP_PASSWORD"),
    )

    ethereum_token_fetcher: TokenDataFetcher = EthereumTokenDataFetcher()

    records = event["Records"]

    logger.info(f"Records count: {len(records)}. Processing secondary market events.")

    nft_data_list: List[NFTData] = []

    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)

    for record in records:
        try:
            metadata = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")

            logger.info(f"Received record: {metadata}")

            metadata_record = json.loads(metadata)
            nft_metadata: NFTMetadata = NFTMetadata.from_dict(metadata_record)

            if nft_metadata.blockchain_id == solana_address():
                try:
                    nft_data = async_loop.run_until_complete(
                        get_nft_data(solana_token_fetcher, nft_metadata)
                    )
                    nft_data_list.append(nft_data)
                except (FetchTokenDataException, json.JSONDecodeError):
                    continue
            elif nft_metadata.blockchain_id == ethereum_address():
                try:
                    nft_data = async_loop.run_until_complete(
                        get_nft_data(ethereum_token_fetcher, nft_metadata)
                    )
                    nft_data_list.append(nft_data)
                except (FetchTokenDataException, json.JSONDecodeError):
                    continue
                continue
            else:
                logger.warning(
                    f"NFT Metadata from blockchain: {nft_metadata.blockchain_id} is not supported."
                )
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
            logger.error(f"Failed to decode JSON metadata record: {metadata}")
            logger.error(f"JSON decoding failed with error: {error}")

    if len(nft_data_list) > 0:
        kinesis.produce_records(settings.kinesis.stream_name, nft_data_list)
        return {
            "message": f"Successfully processed metadata batch of length: {len(nft_data_list)}."
        }

    return {"message": "Resulting batch of events is empty."}


async def get_nft_data(
    token_fetcher: TokenDataFetcher, metadata: NFTMetadata
) -> NFTData:
    nft_data = await token_fetcher.get_token_data(metadata)

    return nft_data
