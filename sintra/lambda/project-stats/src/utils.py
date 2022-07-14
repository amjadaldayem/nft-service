from typing import Dict

from src.config import settings


def headers(bearer_token: str) -> Dict[str, str]:
    headers_dict = {
        "Content-Type": "application/json",
        "Authorization": bearer_token,
    }

    return headers_dict


def params(chain: str) -> Dict[str, str]:
    params_dict = {"chain": chain}

    return params_dict


def project_stats_endpoint(contract_address: str) -> str:
    base_url = settings.nft.port.endpoint
    project_stats_url = f"{base_url}/{contract_address}"

    return project_stats_url


def projects_endpoint(page: int, page_size: int) -> str:
    base_url = settings.data.api.project_endpoint
    project_url = f"{base_url}?page={page}&page_size={page_size}"

    return project_url
