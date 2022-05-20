import boto3
import orjson
import os
import uuid

kinesis_client = boto3.client('kinesis')
# sme_events_data_stream_name = os.getenv("SME_EVENTS_KINESIS_DATA_STREAM_NAME")
sme_events_data_stream_name = "sme-events-data-stream"


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
