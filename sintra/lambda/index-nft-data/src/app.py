import base64
import json
import logging
import os
from typing import List

from src.async_client import SolanaHTTPClient
from src.config import settings
from src.exception import DecodingException
from src.model import NFTData, NFTMetadata
from src.producer import KinesisProducer
from src.utils import ethereum_address, solana_address

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    kinesis: KinesisProducer = KinesisProducer(
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_REGION"),
    )
    solana_client: SolanaHTTPClient = SolanaHTTPClient(
        endpoint=settings.blockchain.solana.http.endpoint,
        timeout=settings.blockchain.solana.http.timeout,
        username=os.getenv("SOLANA_RPC_HTTP_USERNAME"),
        password=os.getenv("SOLANA_RPC_HTTP_PASSWORD"),
    )

    records = event["Records"]

    logger.info(f"Records count: {len(records)}. Processing secondary market events.")

    nft_data_list: List[NFTData] = []

    for record in records:
        try:
            metadata = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            metadata_record = json.loads(metadata)
            nft_metadata: NFTMetadata = NFTMetadata.from_dict(metadata_record)

            if nft_metadata.blockchain_id == solana_address():
                pass
            elif nft_metadata.blockchain_id == ethereum_address():
                logger.warning(
                    f"NFT Metadata from blockchain: {nft_metadata.blockchain_id} is not supported."
                )
                continue
            else:
                logger.warning(
                    f"NFT Metadata from blockchain: {nft_metadata.blockchain_id} is not supported."
                )
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as error:
            logger.error(error)
            raise DecodingException("Failed to decode NFT metadata record.") from error

    if len(nft_data_list) > 0:
        kinesis.produce_records(settings.kinesis.stream_name, nft_data_list)
        return {"message": "Successfully processed metadata batch."}

    return {"message": "Resulting batch of events is empty."}
