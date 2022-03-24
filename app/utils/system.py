import os

import boto3
import cachetools

SECRETSMANGER_PREFIX = 'secretsmanager://'

secretsmanager_client = boto3.client("secretsmanager")
lru_cache = cachetools.LRUCache(maxsize=1000)


def get_secure_env(env_name, default_value=None):
    """
    Wrapper for the os.getenv() function that will retrieve the env var
    directly or try to fetch from a secure secret store.

    If the env var starts with `secretsmanager://`, it will try to fetch the
    value from the AWS SecretsManager.

    Args:
        env_name:
        default_value:

    Returns:

    """
    var = os.getenv(env_name, default_value)
    if var is None:
        return None
    if var.startswith(SECRETSMANGER_PREFIX):
        var_name = var[len(SECRETSMANGER_PREFIX):]
        if not var_name:
            return None
        if var_name in lru_cache:
            return lru_cache[var_name]

        resp = secretsmanager_client.get_secret_value(
            SecretId=var_name
        )
        value = resp['SecretString']
        lru_cache[var_name] = value
    else:
        value = var
    return value
