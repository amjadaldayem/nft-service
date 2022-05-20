import boto3
import orjson
import os
import uuid

from app.models import SecondaryMarketEvent

kinesis_client = boto3.client('kinesis')
# sme_events_data_stream_name = os.getenv("SME_EVENTS_KINESIS_DATA_STREAM_NAME")
sme_events_data_stream_name = "sme-events-data-stream"


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
