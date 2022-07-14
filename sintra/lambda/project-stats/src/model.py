from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ProjectStats:
    id: str
    contract_address: str
    project_id: str
    timestamp: datetime
    floor_price: Optional[float]
    total_supply: Optional[int]
    total_sales: Optional[int]
    total_volume: Optional[float]
    market_cap: Optional[float]
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "contract_address": self.contract_address,
            "project_id": self.project_id,
            "timestamp": self.timestamp.isoformat(),
            "floor_price": self.floor_price if self.floor_price else 0.0,
            "total_supply": self.total_supply if self.total_supply else 0,
            "total_sales": self.total_sales if self.total_sales else 0,
            "total_volume": self.total_volume if self.total_volume else 0.0,
            "market_cap": self.market_cap if self.market_cap else 0.0,
            "description": self.description,
        }


@dataclass
class Project:
    id: str
    project_name: str
    contract_address: str
    project_id: str
    twitter_account_username: str
    blockchain_id: int
    description: str

    @classmethod
    def from_dict(cls, project_dict: Dict[str, Any]) -> Project:
        return cls(
            id=project_dict["id"],
            project_name=project_dict["project_name"],
            contract_address=project_dict["contract_address"],
            project_id=project_dict["project_id"],
            twitter_account_username=project_dict["twitter_account_username"],
            blockchain_id=project_dict["blockchain_id"],
            description=project_dict["description"],
        )
