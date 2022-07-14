import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
from src.config import settings
from src.model import Project, ProjectStats
from src.producer import KinesisProducer
from src.utils import headers, params, projects_endpoint, project_stats_endpoint

logger = logging.getLogger(__name__)

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    logger.info(
        f"Starting with Project stats fetch at {datetime.now(timezone.utc).isoformat()}."
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

    project_stats_batch: List[ProjectStats] = []

    nft_port_bearer_token = os.getenv("NFT_PORT_BEARER_TOKEN", None)

    logger.info("Fetching Project stats for each project.")
    for project in projects:
        project_stats = _get_project_stats(project, nft_port_bearer_token)
        project_stats_batch.append(project_stats)

    logger.info(
        f"Sending batch: {len(project_stats_batch)} to topic: {settings.kinesis.stream_name}."
    )

    if len(project_stats_batch) > 0:
        kinesis.produce_records(settings.kinesis.stream_name, project_stats_batch)
        return {
            "message": f"Successfully processed twitter data for batch of projects: {len(project_stats_batch)}."
        }

    return {"message": "Resulting batch of events is empty."}


def _get_project_stats(project: Project, bearer_token: str) -> ProjectStats:
    blockchain_name = settings.blockchain.name
    project_stats_endpoint_header = headers(bearer_token)
    project_stats_endpoint_params = params(blockchain_name)
    project_stats_url = project_stats_endpoint(project.contract_address)

    response = requests.get(
        url=project_stats_url,
        headers=project_stats_endpoint_header,
        params=project_stats_endpoint_params,
    )

    project_stats_data = response.json()
    project_statistics = project_stats_data.get("statistics", None)

    floor_price = project_statistics.get("floor_price", None)
    total_supply = project_statistics.get("total_supply", None)
    total_sales = project_statistics.get("total_sales", None)
    total_volume = project_statistics.get("total_volume", None)
    market_cap = project_statistics.get("market_cap", None)

    project_stats = ProjectStats(
        id=str(uuid.uuid4()),
        contract_address=project.contract_address,
        description=project.description,
        timestamp=datetime.now(timezone.utc),
        project_id=project.project_id,
        floor_price=floor_price,
        total_supply=total_supply,
        total_sales=total_sales,
        total_volume=total_volume,
        market_cap=market_cap,
    )

    return project_stats


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
