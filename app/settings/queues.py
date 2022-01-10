import os

from slab.messaging import CQueue

SQS_ENDPOINT = os.getenv('SQS_ENDPOINT')

#
# List the Queue URLs here
NFT_COLLECTION_CRAWL_QUEUE_URL = os.environ['NFT_COLLECTION_CRAWL_QUEUE_URL']

_queue_urls = (
    NFT_COLLECTION_CRAWL_QUEUE_URL,

)


def get_queue_map():
    return {
        url: CQueue(name=url.split('/')[-1].title(), url=url, endpoint=SQS_ENDPOINT)
        for (name, url) in _queue_urls
    }
