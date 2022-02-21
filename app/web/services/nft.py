from typing import Union, FrozenSet, Set, Tuple, Optional, List

from app.models import (
    NFTRepository,
    SMERepository, SecondaryMarketEvent,
)


class NFTService:

    def __init__(self, *, dynamodb_resource):
        self.nft_repository = NFTRepository(
            dynamodb_resource=dynamodb_resource,
        )
        self.sme_repository = SMERepository(
            dynamodb_resource=dynamodb_resource
        )