import dataclasses
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional


@dataclass
class NFTMetadata:
    mint_key: str  # Token address in SolScan speak
    update_authority: str
    primary_sale_happened: bool
    is_mutable: bool
    name: Optional[str]
    symbol: Optional[str]
    uri: Optional[str]
    seller_fee_basis_points: str
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
                "creator": creators[i],
                "share": share[i],
                "verified": verified[i],
            }
            for i in range(lc)
        ]

    def to_dikt(self) -> Dict[str, Any]:
        return {
            "mint_key": self.mint_key,
            "update_authority": self.update_authority,
            "primary_sale_happened": self.primary_sale_happened,
            "is_mutable": self.is_mutable,
            "name": "" if self.name is None else self.name,
            "symbol": "" if self.symbol is None else self.symbol,
            "uri": "" if self.uri is None else self.uri,
            "seller_fee_basis_points": self.seller_fee_basis_points,
            "creators": self.creators,
            "verified": self.verified,
            "share": self.share,
            "ext_data": self.ext_data,
        }
