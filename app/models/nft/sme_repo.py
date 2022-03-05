import copy
import logging
from typing import List, Tuple

import orjson
import pylru
from boto3.dynamodb.conditions import Key

from app.models.shared import DynamoDBRepositoryBase, meta
from .data import SecondaryMarketEvent, NftData
from ...utils import full_stacktrace

logger = logging.getLogger(__name__)


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
        from .nft_repo import NFTRepository
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
                    logger.error(str(e))
                    logger.error("Bad item: %s", orjson.dumps(item))

        return c, failed

    def get_smes_in_time_window(self,
                                w: str,
                                tbt_lb=None,
                                tbt_ub=None,
                                tbt_lb_exclusive=False,
                                tbt_ub_exclusive=False,
                                filter_expression=None) -> List[dict]:
        """

        Retrieves Secondary Market Events that falls in the given time window key.

        Later we might want to watchout for the actual performance and RCU consumptions.

        Args:
            w: Time Window
            tbt_lb: The lower bound <timestamp>#<blockchain_id>#<transaction_hash> sort key.
                Inclusive by default.
            tbt_ub: The upper bound <timestamp>#<blockchain_id>#<transaction_hash> sort key.
                Inclusive by default.
            filter_expression:
            tbt_lb_exclusive: If we want to include the item that matches exactly
                the upper bound of sort key in the result. By default, true, setting
                this to false can help in the case of pagination, so we avoid overlapping.
            tbt_ub_exclusive: If we want to include the item that matches exactly
                the lower bound of sort key in the result. By default, true, setting
                this to false can help in the case of pagination, so we avoid overlapping.

        Returns:
        """
        table = self.table
        key_cond = Key(self.PK).eq(w)
        index_name = None
        if tbt_lb and not tbt_ub:
            index_name = self.LSI_SME_TBT
            key_cond &= Key(self.LSI_SME_TBT_SK).gte(tbt_lb)

        if tbt_ub and not tbt_lb:
            index_name = self.LSI_SME_TBT
            key_cond &= Key(self.LSI_SME_TBT_SK).lte(tbt_ub)

        if tbt_lb and tbt_ub:
            index_name = self.LSI_SME_TBT
            key_cond &= Key(self.LSI_SME_TBT_SK).between(tbt_lb, tbt_ub)

        query_params = {
            "Select": "ALL_ATTRIBUTES",
        }
        if index_name:
            query_params['IndexName'] = index_name

        # if tbt_ub_exclusive:
        #     f = Attr(self.LSI_SME_TBT_SK).ne(tbt_ub)
        #     filter_expression = f if not filter_expression else (filter_expression & f)
        #
        # if tbt_lb_exclusive:
        #     f = Attr(self.LSI_SME_TBT_SK).ne(tbt_lb)
        #     filter_expression = f if not filter_expression else (filter_expression & f)

        if filter_expression:
            query_params['FilterExpression'] = filter_expression

        query_params["KeyConditionExpression"] = key_cond
        items = []
        while True:
            resp = table.query(**query_params)
            items.extend(resp['Items'])
            exclusive_start_key = resp.get('LastEvaluatedKey')
            if not exclusive_start_key:
                break
            query_params['ExclusiveStartKey'] = exclusive_start_key

        items.sort(key=lambda i: i['tbt'], reverse=True)
        if items and tbt_ub_exclusive and items[0]['tbt'] == tbt_ub:
            items.pop(0)
        if items and tbt_lb_exclusive and items[-1]['tbt'] == tbt_lb:
            items.pop()

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
