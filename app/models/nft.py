import copy
import logging
from datetime import datetime
from typing import (
    List,
    Optional,
    Any
)
from typing import Tuple

import pylru
from boto3.dynamodb.conditions import Attr, Key
from pydantic import dataclasses

from app.blockchains import (
    SECONDARY_MARKET_EVENT_UNKNOWN,
    EMPTY_PUBLIC_KEY,
    EMPTY_TRANSACTION_HASH
)
from app.models import meta
from app.models.dynamo import DynamoDBRepositoryBase
from app.settings import SME_AGGREGATION_WINDOW
from app.utils import full_stacktrace
from .shared import DataClassBase

logger = logging.getLogger(__name__)

NO_VALUE = '__NO_VALUE__'


class MediaFile(DataClassBase):
    uri: str
    file_type: str = ''


class NftCreator(DataClassBase):
    address: str
    verified: bool = False
    share: int = 0


class NftData(DataClassBase):
    blockchain_id: int
    token_address: str
    collection_key: str  # Unique address or something that identifies this collection scoped to that chain
    current_owner: str
    name: str
    description: str
    symbol: str
    primary_sale_happened: bool
    metadata_uri: str
    creators: List[NftCreator]
    ext_data: dict = dataclasses.Field(default_factory=dict)
    edition: str = ""
    attributes: dict = dataclasses.Field(default_factory=dict)
    external_url: str = ""
    files: List[MediaFile] = dataclasses.Field(default_factory=List)

    @property
    def collection_id(self):
        return f"bc#{self.blockchain_id}#{self.collection_key}"

    @property
    def collection_name(self):
        name = self.name
        if not name:
            collection_name = self.symbol or ""
        else:
            try:
                collection_name, _ = name.rsplit('#', 10)
            except:
                collection_name = name
        collection_name = collection_name.strip()
        return collection_name if collection_name else NO_VALUE

    @property
    def nft_id(self):
        return f"bn#{self.blockchain_id}#{self.token_address}"

    @property
    def current_owner_id(self):
        return f"bo#{self.blockchain_id}#{self.current_owner}"

    @property
    def media_url(self):
        """

        Returns:
            The 1st URL in the files array.
        """
        return self.files[0].uri or ''


class SecondaryMarketEvent(DataClassBase):
    blockchain_id: int  # The Index for the blockchain
    market_id: int  # The secondary market ID, e.g. SOLANA_MAGIC_EDEN
    timestamp: int  # Approx. unix timestamp (seconds since epoch)
    event_type: int = SECONDARY_MARKET_EVENT_UNKNOWN  # See above
    token_key: str = ''  # Token address / Mint key
    price: int = 0  # Listing/Sale price in the smallest UNIT. E.g., for Solana this is lamports
    owner: str = EMPTY_PUBLIC_KEY  # Account that owns this piece, who liste / sells this.
    buyer: str = EMPTY_PUBLIC_KEY
    transaction_hash: str = EMPTY_TRANSACTION_HASH
    data: Optional[Any] = None  # Extra information

    @staticmethod
    def get_time_window_key(timestamp):
        """
        Generates the time window key used as PK in sme table.

        Args:
            timestamp:

        Returns:

        """
        try:
            # By default, on server this should be in UTC always.
            dt = datetime.fromtimestamp(timestamp)
            minute_marker = dt.minute // SME_AGGREGATION_WINDOW
            s = dt.strftime('%Y-%m-%d-%H-')
            return f"w#{s}{minute_marker:02d}"
        except:
            return 'unknown'

    @property
    def sme_id(self):
        return f'be#{self.blockchain_id}#{self.transaction_hash}'

    @property
    def w(self) -> str:
        """
        The time window marker
        Returns:
            w#<date-hour-5min_window>
        """
        return self.get_time_window_key(self.timestamp)

    @property
    def btt(self) -> str:
        """
        Blockchain - timestamp attribute
        Returns:
            btt#<blockchain_id>#<timestamp>#transaction_hash
        """
        return f"btt#{self.blockchain_id}#{self.timestamp}#{self.transaction_hash}"

    @property
    def tbt(self) -> str:
        """
        Timestamp - blockchain id - transaction id
        Returns:
            tbt#<timestamp>#<blockchain_id>#transaction_hash
        """
        return f"tbt#{self.timestamp}#{self.blockchain_id}#{self.transaction_hash}"

    @property
    def et(self) -> str:
        """
        Event - timestamp attribiute

        Returns:
            et#<event_type>#<timestamp>
        """
        return f"et#{self.event_type}#{self.timestamp}"


class NFTRepository(DynamoDBRepositoryBase, meta.DTNftMeta):

    def __init__(self,
                 dynamodb_resource,
                 ):
        super().__init__(
            self.NAME,
            dynamodb_resource
        )

    def save_nfts(self, nft_data_list: List[NftData]) -> Tuple[int, List[NftData]]:
        """

        Returns:
            Num of items got successfully processed (without _any_ exceptions), list of failed ones.
        """
        failed = []
        table = self.table
        # 1. Save the NFT data (immutable part) with `nft_id` as pk and literal
        #   'n' as sk. Removes the following,
        #    - `current_owner`
        # Put current owner in separate row
        c = 0
        for nft_data in nft_data_list:
            # Saves the current owner info
            nft_id = nft_data.nft_id

            try:
                current_owner_id = nft_data.current_owner_id
                table.put_item(
                    Item={
                        self.PK: nft_id,
                        self.SK: 'co',
                        'current_owner_id': current_owner_id
                    },
                    ReturnValues=self.RV_NONE,
                    ConditionExpression=~(Attr(self.PK).eq(nft_id)
                                          & Attr(self.SK).eq('co')
                                          & Attr('current_owner_id').eq(current_owner_id))
                )
                # Saves the NFT info
                item = self.nft_data_to_dynamo(
                    nft_data,
                    fields_to_remove={'current_owner'},
                    field_as_pk='nft_id',
                )
                item[self.SK] = 'n'
                table.put_item(
                    Item=item,
                    ReturnValues=self.RV_NONE,
                    ConditionExpression=~(Attr(self.PK).eq(nft_id) & Attr(self.SK).eq('n'))
                )

                # 2. Update the name filter
                qfi = self.get_qfi(nft_data)
                if qfi:
                    collection_name_lc = qfi[self.SK]
                    table.put_item(
                        Item=qfi,
                        ReturnValues=self.RV_NONE,
                        ConditionExpression=~(Attr(self.PK).eq(nft_data.nft_id) & Attr(self.SK).eq(collection_name_lc))
                    )
                c += 1
            except self.exceptions.ConditionalCheckFailedException:
                continue
            except Exception as e:
                failed.append(nft_data)
                logger.error(str(e) + "\n" + full_stacktrace())

        return c, failed

    @classmethod
    def get_qfi(cls, nft_data: NftData):
        """
        Generate an item to store as a Quick Filter Index in the `nft` table.
        A qfi has a parition key of one letter, which is the initial letter
        of the NFT collection name, then the sort key being the actual collection
        name if any (or NO_VALUE if empty).

        Args:
            nft_data:

        Returns:

        """
        qfi = {}
        collection_name = nft_data.collection_name
        if collection_name:
            collection_name_lc = collection_name.lower()
            initial = collection_name_lc[0]
            qfi = {
                cls.PK: f"qfi#{initial}",
                cls.SK: collection_name_lc,  # All lower cased collection name, for quick filtering
                'collection_name': collection_name,  # Original inferred collection name
                cls.GSI_NFT_COLLECTION_NFTS_PK: nft_data.collection_id
                # In turn use this to index all NFTs underneath
            }
        return qfi

    @classmethod
    def nft_data_to_dynamo(cls, nft_data: NftData, fields_to_remove=None,
                           field_as_pk=None, field_as_sk=None) -> dict:
        """

        Args:
            nft_data:
            fields_to_remove:
            field_as_pk: If not given, there will be no Pk field in the returned dict.
            field_as_sk: If not given, there will be no Sk field in the returned dict.

        Returns:

        """
        ret = {
            cls.GSI_NFT_COLLECTION_NFTS_PK: nft_data.collection_id,
            'nft_id': nft_data.nft_id,
            'media_url': nft_data.media_url,
            'collection_name': nft_data.collection_name,
        }
        if field_as_pk:
            ret[cls.PK] = getattr(nft_data, field_as_pk)
        if field_as_sk:
            ret[cls.SK] = getattr(nft_data, field_as_sk)

        creators = nft_data.creators
        files = nft_data.files
        # Intentional shallow copy here
        ret.update(copy.copy(nft_data.__dict__))
        ret['creators'] = [copy.copy(c.__dict__) for c in creators]
        ret['files'] = [copy.copy(f.__dict__) for f in files]
        if fields_to_remove:
            for f in fields_to_remove:
                del ret[f]
        if field_as_pk:
            # We have this value in PK field, so do not need to repeat it its
            # original cell.
            del ret[field_as_pk]
        if field_as_sk:
            # We have this value in SK field, so do not need to repeat it its
            # original cell.
            del ret[field_as_sk]
        return ret


class SMERepository(DynamoDBRepositoryBase, meta.DTSmeMeta):

    def __init__(self, dynamodb_resource):
        super().__init__(
            self.NAME,
            dynamodb_resource,
        )
        # A temporary cache for skipping dupes in a time window when ingesting
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

        fn_sme_to_dynamo = self.sme_to_dynamo
        fn_nft_data_to_dynamo = NFTRepository.nft_data_to_dynamo
        with table.batch_writer() as batch:
            for sme, nft_data in smes_and_nfts:
                if sme.sme_id in self._seen:
                    continue
                self._seen[sme.sme_id] = 1
                item = fn_sme_to_dynamo(sme, ('data',))
                item.update(
                    fn_nft_data_to_dynamo(
                        nft_data, ('blockchain_id', 'files')
                    )
                )
                try:
                    batch.put_item(
                        Item=item,
                    )
                    c += 1
                except Exception as e:
                    failed.append(item)
                    logger.error(str(e) + "\n" + full_stacktrace())

        return c, failed

    def get_smes_in_time_window(self,
                                w: str,
                                tbt=None,
                                forward: bool = True,
                                filter_expression=None) -> List[dict]:
        """

        Retrieves Secondary Market Events that falls in the given time window key.

        Args:
            w:
            tbt: Timestamp - <blockchain_id>#<transaction_hash> sort key.
            forward: If true, will go forward (from older to newer)
                another wise go "backward". Exclusive.
            filter_expression:

        Returns:
        """
        table = self.table
        key_cond = Key(self.PK).eq(w)
        index_name = None
        if tbt:
            index_name = self.LSI_SME_TBT
            if forward:
                # Travelling forward to newer items
                key_cond &= Key(self.LSI_SME_TBT_SK).gt(tbt)
            else:
                key_cond &= Key(self.LSI_SME_TBT_SK).lt(tbt)

        query_params = {
            "KeyConditionExpression": key_cond,
            "Select": "ALL_ATTRIBUTES"
        }
        if index_name:
            query_params['IndexName'] = index_name
        if filter_expression:
            query_params['FilterExpression'] = filter_expression

        items = []
        while True:
            resp = table.query(**query_params)
            items.extend(resp['Items'])
            exclusive_start_key = resp['LastEvaluatedKey']
            if not exclusive_start_key:
                break
            query_params['ExclusiveStartKey'] = exclusive_start_key

        items.sort(key=lambda i: i['tbt'], reverse=not forward)
        return items

    @classmethod
    def sme_to_dynamo(cls, sme: SecondaryMarketEvent, fields_to_remove=None) -> dict:
        d = {
            cls.PK: sme.w,
            cls.SK: sme.btt,
            cls.GSI_SME_SME_ID_PK: sme.sme_id,
            cls.LSI_SME_ET_SK: sme.et,
            cls.LSI_SME_TBT_SK: sme.tbt,
        }
        # Shallow copy here
        d.update(copy.copy(sme.__dict__))
        if fields_to_remove:
            for f in fields_to_remove:
                del d[f]
        return d
