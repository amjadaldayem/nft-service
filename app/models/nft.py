import contextlib
import dataclasses
from functools import cached_property
from typing import List

import boto3

from app import settings
from app.models.dynamo import DynamoDBRepositoryBase
from app.models.sme import SecondaryMarketEvent


@dataclasses.dataclass
class MediaFile:

    uri: str
    file_type: str = ''


@dataclasses.dataclass
class NftCreator:
    address: str
    verified: bool = False
    share: int = 0


@dataclasses.dataclass
class NftData:
    blockchain_id: int
    token_address: str
    current_owner: str
    name: str
    description: str
    symbol: str
    primary_sale_happened: bool
    metadata_uri: str
    creators: List[NftCreator]
    ext_data: dict = dataclasses.field(default_factory=dict)
    edition: str = ""
    attributes: dict = dataclasses.field(default_factory=dict)
    external_url: str = ""
    files: List[MediaFile] = dataclasses.field(default_factory=List)

    @property
    def nft_id(self):
        return f"bn#{self.blockchain_id}#{self.token_address}"


class NFTRepository(DynamoDBRepositoryBase):
    """
    nft_id = bn#<blockchain_id>#<nft_token_address>
    """

    def __init__(self,
                 dynamodb_resource,
                 ):
        super().__init__(
            settings.DYNAMODB_NFT_TABLE,
            dynamodb_resource
        )

    @staticmethod
    def nft_id(blockchain_id, token_address):
        return f"bn#{blockchain_id}#{token_address}"

    def save_nft(self, ):
        """

        Returns:

        """
        table = self.table
        pass
