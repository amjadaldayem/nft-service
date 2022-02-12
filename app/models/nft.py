from typing import List, Tuple

import orjson
import pylru
from boto3.dynamodb.conditions import Key
from app import settings
from app.models import SecondaryMarketEvent, NftData
from app.models.dynamo import DynamoDBRepositoryBase


class NFTRepository(DynamoDBRepositoryBase):
    """
    nft_id = bn#<blockchain_id>#<nft_token_address>

    * Facet: Nft
        pk = <nft_id> from NftData


    * Facet: Collection
        pk = <collection_id> from NftData

    * Facet: Quick Name Filter
    ( partitioned into 26 + 10 + 1 = 37 partitions, 26 letters, 10 digits and others
    so people type something, we immediately try the partition initializing with that
    character, the sort key is the full name, which is matched with begins_with)

        pk = qfi#<initial_letter>
        fq = <full_name> <-- Use collection names

        attribute: collection_id

    """

    def __init__(self,
                 dynamodb_resource,
                 ):
        super().__init__(
            settings.DYNAMODB_NFT_TABLE,
            dynamodb_resource
        )

    def save_nfts(self, nft_data: NftData):
        """

        Returns:

        """
        table = self.table
        pass

    @staticmethod
    def nft_data_to_dynamo(nft_data: NftData, fields_to_remove=None) -> dict:
        d = {
            'collection_id': nft_data.collection_id,
            'nft_id': nft_data.nft_id,
            'media_url': nft_data.media_url,
        }
        creators = nft_data.creators
        d.update(nft_data.__dict__)
        d['creators'] = [c.__dict__ for c in creators]
        if fields_to_remove:
            for f in fields_to_remove:
                del d[f]
        return d


class SMERepository(DynamoDBRepositoryBase):
    """
    - Table

    * Facet: Secondary Market Event Time series
        pk = w
            w#<date-hour-5min_window> (in format 2022-01-31-17-00, 2022-01-31-17-05)
        sk = btt
            btt#<blockchain_id>#<timestamp>#<transaction_hash>
             <- Per blockchain & Transaction timestamp & transaction hash

        -Lsi: Nft name
            list_sort_key
            name = <name> string

        - Lsi: Timestamp
            lsi_sort_key
            timestamp = <timestamp> (Number)

        - Lsi: Event Type
            lsi_sort_key
            et = et#<event_type>#<timestamp>  (filter by single event)

        - Lsi: Event Buy & Listing

            lsi_sort_key
            eblt = eblt#<timestamp>
                (filter by buy and listing only, optimized common case)
    - Gsi: Transaction Events

        gsi_pk = sme_id
        gsi_sk = None

    - Gsi: Nft Events

        gsi_pk = nft_id
        gsi_sk = timestamp (number)

    - Gsi: Nft Collection Events

        gsi_pk = collection_id
        gsi_sk = timestamp (number)

    """

    def __init__(self, dynamodb_resource):
        super().__init__(
            settings.DYNAMODB_SME_TABLE,
            dynamodb_resource,
        )
        self.gsi_sme_id = settings.DYNAMODB_SME_TABLE_GSI_SME_ID
        self.gsi_nft_events = settings.DYNAMODB_SME_TABLE_GSI_NFT_EVENTS
        self.gsi_collection_events = settings.DYNAMODB_SME_TABLE_GSI_COLLECTION_EVENTS
        self.lsi_timestamp = settings.DYNAMODB_SME_TABLE_LSI_TIMESTAMP
        self.lsi_nft_name = settings.DYNAMODB_SME_TABLE_LSI_NFT_NAME
        self.lsi_events = settings.DYNAMODB_SME_TABLE_LSI_EVENTS
        self.lsi_buy_listing_events = settings.DYNAMODB_SME_TABLE_LSI_BUY_LISTING_EVENTS
        # A temporary cache for skipping dupes in a time window
        # (which is more likely to happen)
        self._seen = pylru.lrucache(10000)

    def save_sme_with_nft_batch(self,
                                smes_and_nfts: List[Tuple[SecondaryMarketEvent, NftData]]
                                ) -> Tuple[int, List[dict]]:
        """
        Stitch the SME and NFT data.

        Returns
            (int, list) Total number of items inserted successfully, failed item list.
        """
        failed = []
        table = self.table
        c = 0
        with table.batch_writer() as batch:
            for sme, nft_data in smes_and_nfts:
                if sme.sme_id in self._seen:
                    continue
                self._seen[sme.sme_id] = 1
                item = self.sme_to_dynamo(sme, ('data',))
                item.update(
                    NFTRepository.nft_data_to_dynamo(
                        nft_data, ('blockchain_id', 'files')
                    )
                )
                try:
                    batch.put_item(
                        Item=item,
                    )
                    c += 1
                except BaseException as e:
                    failed.append(item)

        return c, failed

    @staticmethod
    def sme_to_dynamo(sme: SecondaryMarketEvent, fields_to_remove=None) -> dict:
        d = {
            'w': sme.w,
            'btt': sme.btt,
            'sme_id': sme.sme_id,
            'et': sme.et,
            'eblt': sme.eblt,
        }
        d.update(sme.__dict__)
        if fields_to_remove:
            for f in fields_to_remove:
                del d[f]
        return d
