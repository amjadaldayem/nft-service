import boto3
import orjson
import os
import uuid

from app.models import SecondaryMarketEvent, NftData, NftCreator, MediaFile

kinesis_client = boto3.client('kinesis')
# sme_events_data_stream_name = os.getenv("SME_EVENTS_KINESIS_DATA_STREAM_NAME")
sme_events_data_stream_name = "solana-sme-events-data-stream"


def convert_secondary_market_event_to_dict(secondary_market_event: SecondaryMarketEvent) -> dict:
    return {
        "blockchain_id": secondary_market_event.blockchain_id,
        "market_id": secondary_market_event.market_id,
        "timestamp": secondary_market_event.timestamp,
        "event_type": secondary_market_event.event_type,
        "token_key": secondary_market_event.token_key,
        "price": secondary_market_event.price,
        "owner": secondary_market_event.owner,
        "buyer": secondary_market_event.buyer,
        "transaction_hash": secondary_market_event.transaction_hash,
        "data": secondary_market_event.data
    }


def convert_nft_data_to_dict(nft_data: NftData) -> dict:
    return {
        "blockchain_id": nft_data.blockchain_id,
        "token_address": nft_data.token_address,
        "collection_key": nft_data.collection_key,
        "current_owner": nft_data.current_owner,
        "name": nft_data.name,
        "description": nft_data.description,
        "symbol": nft_data.symbol,
        "primary_sale_happened": nft_data.primary_sale_happened,
        "metadata_uri": nft_data.metadata_uri,
        "creators": [convert_nft_creator_to_dict(creator) for creator in nft_data.creators],
        "ext_data": nft_data.ext_data,
        "edition": nft_data.edition,
        "attributes": nft_data.attributes,
        "external_url": nft_data.external_url,
        "files": [convert_media_file_to_dict(file) for file in nft_data.files]
    }


def convert_media_file_to_dict(media_file: MediaFile) -> dict:
    return {
        "uri": media_file.uri,
        "file_type": media_file.file_type
    }


def convert_nft_creator_to_dict(nft_creator: NftCreator):
    return {
        "address": nft_creator.address,
        "verified": nft_creator.verified,
        "share": nft_creator.share
    }


def publish_sme_events_to_kinesis(events):
    kinesis_client.put_records(
        Records=[
            {
                'Data': orjson.dumps(event),
                'PartitionKey': str(uuid.uuid4()),
            } for event in events
        ],
        StreamName=sme_events_data_stream_name
    )
