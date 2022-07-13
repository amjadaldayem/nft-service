import json
import logging
import os
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
from src.config import settings
from src.model import Project, TwitterTrend
from src.producer import KinesisProducer
from src.utils import count_endpoint, followers_endpoint, headers, projects_endpoint

logger = logging.getLogger(__name__)

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    logger.info(
        f"Starting with Twitter trends fetch at {datetime.now(timezone.utc).isoformat()}."
    )

    localstack_active_param = str(settings.localstack.active).lower()
    localstack_active = localstack_active_param == "true"

    if localstack_active:
        logger.info("Localstack is active.")

    kinesis: KinesisProducer = KinesisProducer(
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_REGION"),
        localstack_active,
    )

    logger.info("Fetching projects...")
    projects = _projects()

    twitter_trends: Dict[str, TwitterTrend] = {}

    bearer_token_1 = os.getenv("BEARER_TOKEN_1", None)
    bearer_token_2 = os.getenv("BEARER_TOKEN_2", None)

    logger.info("Fetching number of followers for each project.")
    followers_futures: List[Future] = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for project in projects:
            future = executor.submit(_get_followers, project, bearer_token_1)
            followers_futures.append(future)

    for future in as_completed(followers_futures):
        twitter_trend = future.result()
        twitter_trends[twitter_trend.twitter_account_name] = twitter_trend

    logger.info("Fetching number of mentions for each project.")
    mentions_futures: List[Future] = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for index, project in enumerate(projects):
            if index % 2 == 0:
                count_endpoint_header = headers(bearer_token_1)
            else:
                count_endpoint_header = headers(bearer_token_2)

            future = executor.submit(_get_mentions, project, count_endpoint_header)
            mentions_futures.append(future)

    for future in as_completed(mentions_futures):
        mentions_dict = future.result()

        twitter_account_username = mentions_dict["twitter_username"]
        twitter_trend = twitter_trends.get(twitter_account_username, None)
        if twitter_trend:
            twitter_trend.mentions_number = mentions_dict["tweets_count"]

    trend_list = twitter_trends.values()

    logger.info(
        f"Sending batch: {len(trend_list)} to topic: {settings.kinesis.stream_name}."
    )

    if len(trend_list) > 0:
        kinesis.produce_records(settings.kinesis.stream_name, trend_list)
        return {
            "message": f"Successfully processed twitter data for batch of projects: {len(twitter_trends)}."
        }

    return {"message": "Resulting batch of events is empty."}


def _get_followers(project: Project, bearer_token: str) -> TwitterTrend:
    followers_endpoint_header = headers(bearer_token)
    followers_url = followers_endpoint(project.twitter_account_username)
    response = requests.get(followers_url, headers=followers_endpoint_header)

    user_lookup_json = response.json()
    user_data = user_lookup_json["data"]
    public_metrics = user_data["public_metrics"]

    twitter_trend = TwitterTrend(
        id=str(uuid.uuid4()),
        twitter_account_name=project.twitter_account_username,
        timestamp=datetime.now(timezone.utc),
        followers_number=public_metrics.get("followers_count", None),
    )

    return twitter_trend


def _get_mentions(project: Project, headers: Dict[str, str]) -> Dict[str, int]:
    count_url = count_endpoint(project.twitter_account_username)
    response = requests.get(url=count_url, headers=headers)

    tweets_count_json = response.json()
    tweets_count_metadata = tweets_count_json["meta"]
    tweets_count = tweets_count_metadata.get("total_tweet_count", None)

    return {
        "twitter_username": project.twitter_account_username,
        "tweets_count": tweets_count,
    }


def _projects() -> List[Project]:
    projects: List[Project] = []
    has_results = True
    page_number = 0
    page_size = 20

    while has_results:
        response = requests.get(url=projects_endpoint(page_number, page_size))
        if response.status_code >= 400:
            has_results = False
            break

        data = response.json()
        projects_list: List[Dict[str, Any]] = json.loads(data)
        if len(projects_list) == 0:
            has_results = False
            break

        projects = [Project.from_dict(project_dict) for project_dict in projects_list]
        page_number += 1

    return projects
