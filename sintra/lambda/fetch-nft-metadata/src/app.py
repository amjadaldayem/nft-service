import json
import logging

logger = logging.getLogger(__name__)

# TODO:
#   1. Init Stream producer
#   2. Transform incoming records
#   3. Fetch NFT metadata
#   4. Send NFT metadata to stream


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
                # "location": ip.text.replace("\n", "")
            }
        ),
    }
