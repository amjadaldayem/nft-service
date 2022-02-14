import copy
import logging
from typing import List, Tuple
import pylru
from boto3.dynamodb.conditions import Attr

from app.models import SecondaryMarketEvent, NftData, meta
from app.models.dynamo import DynamoDBRepositoryBase
from app.utils import full_stacktrace

logger = logging.getLogger(__name__)


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
                except Exception as e:
                    failed.append(item)
                    logger.error(str(e) + "\n" + full_stacktrace())

        return c, failed

    @classmethod
    def sme_to_dynamo(cls, sme: SecondaryMarketEvent, fields_to_remove=None) -> dict:
        d = {
            cls.PK: sme.w,
            cls.SK: sme.btt,
            cls.GSI_SME_SME_ID_PK: sme.sme_id,
            cls.LSI_SME_ET_SK: sme.et,
            cls.LSI_SME_EBLT_SK: sme.eblt,
        }
        # Shallow copy here
        d.update(copy.copy(sme.__dict__))
        if fields_to_remove:
            for f in fields_to_remove:
                del d[f]
        return d
