# Some supportive data structures for NFT Metadata
import dataclasses
from collections import namedtuple
from typing import List, Mapping, Optional

NFTCollectionInput = namedtuple(
    'NFTCollectionInput',
    [
        'update_authority',  # For fetching all mints
        'num_creators',
    ]
)

NFTMetadataProgramAccount = namedtuple(
    'NFTMetadataProgramAccount',
    [
        'public_key',
        'data',
        'encoding'
    ]
)


@dataclasses.dataclass
class NFTMetaData:
    """
    The metadata of an NFT, note that to retrieve the actual content of the
    metadata, we need to issue HTTP GET against the `uri` field again. This
    can be potentially expensive and needed to be handled carefully.
    """
    mint_key: str  # Token address in SolScan speak
    update_authority: str
    primary_sale_happened: bool
    is_mutable: bool
    name: Optional[str]
    symbol: Optional[str]
    uri: Optional[str]
    seller_fee_basis_points: str
    # Num of Creators is important for use with analysis on secondary
    # sales/listing
    creators: List[str]
    verified: List[str]
    share: List[str]
    ext_data: Mapping = dataclasses.field(default_factory=dict)

    @property
    def creators_info(self) -> List[Mapping]:
        creators = self.creators
        verified = self.verified
        share = self.share
        lc = len(creators)
        lv = len(verified)
        ls = len(share)

        if not (lc == lv == ls):
            return []

        return [
            {
                'creator': creators[i],
                'share': share[i],
                'verified': verified[i],
            }
            for i in range(lc)
        ]
