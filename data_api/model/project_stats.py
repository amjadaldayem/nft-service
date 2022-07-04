from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ProjectStats(BaseModel):
    id: int
    contract_address: str
    project_id: str
    timestamp: datetime
    floor_price: float
    total_supply: int
    total_sales: int
    total_volume: float
    market_cap: float
    holders: List[str] = Field(default_factory=list)
    description: str

    @classmethod
    def from_dict(cls, project_stats_dict: Dict[str, Any]) -> ProjectStats:
        return cls(
            id=project_stats_dict["id"],
            contract_address=project_stats_dict["contract_address"],
            project_id=project_stats_dict["project_id"],
            timestamp=project_stats_dict["timestamp"],
            floor_price=project_stats_dict["floor_price"],
            total_supply=project_stats_dict["total_supply"],
            total_sales=project_stats_dict["total_sales"],
            total_volume=project_stats_dict["total_volume"],
            market_cap=project_stats_dict["market_cap"],
            holders=project_stats_dict["holders"],
            description=project_stats_dict["description"],
        )
