import logging
from os import getenv
from typing import Any

import boto3

from sintra.config import settings

logger = logging.getLogger(__name__)


def get_env_variable(env_name: str) -> Any:
    """Return environment variable by trying to find it
    in locally defined variables or AWS secret manager.

    Args:
        env_name (str): Environment variable name.

    Returns:
        Any: Value of environment variable.

    """
    env_variable = getenv(env_name)

    if env_variable is not None:
        return env_variable

    active_var = str(settings.localstack.active).lower()
    active = active_var == "true"
    if active:
        secrets_manager = boto3.client(
            "secretsmanager",
            region_name=settings.localstack.region,
            endpoint_url=settings.localstack.endpoint,
        )
    else:
        secrets_manager = boto3.client(
            "secretsmanager",
            region_name=settings.secretsmanager.region,
        )

    try:
        response = secrets_manager.get_secret_value(SecretId=env_name)
    except secrets_manager.exceptions.ResourceNotFoundException:
        return None

    env_variable = response["SecretString"]
    return env_variable
