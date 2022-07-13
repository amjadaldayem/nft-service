import random
from typing import Dict, Generator, List
from unittest.mock import patch
from uuid import uuid4

import boto3
from faker import Faker
from faker.providers import date_time
from src.app import lambda_handler
from src.model import Project, TwitterTrend

faker = Faker()
Faker.seed(42)
faker.add_provider(date_time)


def projects() -> List[Project]:
    fake_projects = []
    for _ in range(random.randint(1, 5)):
        fake_projects.append(
            Project(
                id=str(uuid4()),
                project_name=faker.name(),
                contract_address=faker.lexify(text="????????????????"),
                project_id=faker.numerify(text="?????"),
                twitter_account_username=faker.name(),
                blockchain_id=faker.numerify(text="?????"),
            )
        )

    return fake_projects


def twitter_trends() -> TwitterTrend:
    return TwitterTrend(
        id=str(uuid4()),
        twitter_account_name=faker.name(),
        timestamp=faker.date_time(),
        mentions_number=random.randint(1, 5),
        followers_number=random.randint(1, 5),
        start_time=faker.date_time(),
    )


def mentions_dict() -> Dict[str, int]:
    return {
        "twitter_username": faker.name(),
        "tweets_count": random.randint(1, 5),
    }


class TestTwitterTrends:
    @patch("src.app._projects")
    @patch("src.app._get_followers")
    @patch("src.app._get_mentions")
    def test_lambda_handler(
        self,
        mentions_fn,
        followers_fn,
        projects_fn,
        kinesis_twitter_trends_stream: Generator[boto3.client, None, None],
    ) -> None:
        generated_project_list = projects()
        projects_fn.return_value = generated_project_list

        followers_fn.return_value = twitter_trends()
        mentions_fn.return_value = mentions_dict()

        response = lambda_handler(event={}, context={})

        projects_fn.assert_called_once()
        followers_fn.assert_called()
        mentions_fn.assert_called()

        assert (
            response["message"]
            == "Successfully processed twitter data for batch of projects: 1."
        )
