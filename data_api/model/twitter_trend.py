from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class TwitterTrend(BaseModel):
    id: int
    twitter_account_username: str
    timestamp: datetime
    mentions_number: int
    followers_number: int
    start_time: datetime

    @classmethod
    def from_dict(cls, twitter_trend_dict: Dict[str, Any]) -> TwitterTrend:
        return cls(
            id=twitter_trend_dict["id"],
            twitter_account_username=twitter_trend_dict["twitter_account_username"],
            timestamp=twitter_trend_dict["timestamp"],
            mentions_number=twitter_trend_dict["mentions_number"],
            followers_number=twitter_trend_dict["followers_number"],
            start_time=twitter_trend_dict["start_time"],
        )
