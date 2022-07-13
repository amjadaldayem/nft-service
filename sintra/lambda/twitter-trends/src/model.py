from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class TwitterTrend:
    id: str
    twitter_account_name: str
    timestamp: datetime
    mentions_number: Optional[int]
    followers_number: Optional[int]
    start_time: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "twitter_account_name": self.twitter_account_name,
            "timestamp": self.timestamp.isoformat(),
            "mentions_number": self.mentions_number if self.mentions_number else 0,
            "followers_number": self.followers_number if self.followers_number else 0,
            "start_time": self.start_time.isoformat(),
        }


@dataclass
class Project:
    id: str
    project_name: str
    contract_address: str
    project_id: str
    twitter_account_username: str
    blockchain_id: int

    @classmethod
    def from_dict(cls, project_dict: Dict[str, Any]) -> Project:
        return cls(
            id=project_dict["id"],
            project_name=project_dict["project_name"],
            contract_address=project_dict["contract_address"],
            project_id=project_dict["project_id"],
            twitter_account_username=project_dict["twitter_account_username"],
            blockchain_id=project_dict["blockchain_id"],
        )
