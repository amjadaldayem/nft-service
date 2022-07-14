import random
from typing import Dict, Generator, List
from unittest.mock import patch
from uuid import uuid4

import boto3
from faker import Faker
from faker.providers import date_time
from src.app import lambda_handler
from src.model import Project, ProjectStats

faker = Faker()
Faker.seed(23)
faker.add_provider(date_time)
NUMBER_OF_PROJECTS = faker.random_int(1, 500)


def projects() -> List[Project]:
    fake_projects = []
    for _ in range(0, NUMBER_OF_PROJECTS):
        fake_projects.append(
            Project(
                id=str(uuid4()),
                project_name=faker.name(),
                contract_address=faker.lexify(text="????????????????"),
                project_id=faker.numerify(text="?????"),
                twitter_account_username=faker.name(),
                blockchain_id=faker.numerify(text="?????"),
                description=faker.text(),
            )
        )

    return fake_projects


def project_stats() -> ProjectStats:
    return ProjectStats(
        id=str(uuid4()),
        timestamp=faker.date_time(),
        contract_address=faker.lexify(text="????????????????"),
        project_id=faker.numerify(text="?????"),
        floor_price=faker.random_int(),
        total_supply=faker.random_int(),
        total_sales=faker.random_int(),
        total_volume=faker.random_int(),
        market_cap=faker.random_int(),
        description=faker.text(),
    )


class TestProjectStats:
    @patch("src.app._projects")
    @patch("src.app._get_project_stats")
    def test_lambda_handler(
        self,
        project_stats_fn,
        projects_fn,
        kinesis_twitter_trends_stream: Generator[boto3.client, None, None],
    ) -> None:
        projects_fn.return_value = projects()

        project_stats_fn.return_value = project_stats()

        response = lambda_handler(event={}, context={})

        projects_fn.assert_called_once()
        project_stats_fn.assert_called()

        assert (
            response["message"]
            == f"Successfully processed twitter data for batch of projects: {NUMBER_OF_PROJECTS}."
        )
