from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class KinesisRecord:
    """Record representing transaction signature that occurred on the market."""

    blockchain_id: int
    market: str
    market_address: int
    market_account: str
    signature: str
    timestamp: int

    def to_dikt(self) -> Dict[str, Any]:
        return {
            "blockchain_id": self.blockchain_id,
            "market": self.market,
            "market_address": self.market_address,
            "market_account": self.market_account,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }
