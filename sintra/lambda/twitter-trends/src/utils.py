from datetime import datetime, timedelta, timezone
from typing import Dict

from src.config import settings


def headers(bearer_token: str) -> Dict[str, str]:
    headers_dict = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }

    return headers_dict


def count_endpoint(
    project_username: str, granularity: str = "day", timedelta_days: int = 3
) -> str:
    time_now = datetime().now(timezone.utc).isoformat()
    start_time = time_now - timedelta(days=timedelta_days)

    base_url = settings.twitter.count_endpoint
    count_url = f"{base_url}?query=@{project_username}&granularity={granularity}&start_time={start_time}"

    return count_url


def followers_endpoint(project_username: str) -> str:
    base_url = settings.twitter.followers_endpoint
    followers_url = f"{base_url}/{project_username}?user.fields=public_metrics"

    return followers_url


def projects_endpoint(page: int, page_size: int) -> str:
    base_url = settings.data.api.project_endpoint
    project_url = f"{base_url}?page={page}&page_size={page_size}"

    return project_url
