import logging
import os
import dotenv

PROJECT_BASE_PATH = os.path.abspath(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )
)
dotenv_path = os.path.join(
    PROJECT_BASE_PATH,
    '.env'
)
dotenv.load_dotenv(dotenv_path)
DEBUG = os.getenv('DEBUG', 0)

# DEPLOYMENT_ENV, choices: prod, staging, dev, local
DEPLOYMENT_ENV = os.getenv('DEPLOYMENT_ENV', 'prod')
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', logging.INFO)
DYNAMODB_ENDPOINT = os.getenv('DYNAMODB_ENDPOINT')
SQS_ENDPOINT = os.getenv('SQS_ENDPOINT')

AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')

# For PostgreSQL databases
DATABASES = {
    # Make sure you have a section named `database-<db_alias>`
    # in the alembic.ini where the `version_locations` are specified
    # so that the migration files for different database reside
    # in different folders.
    'nft': {
        'host': os.environ['NFT_DB_HOST'],
        'user': os.environ['NFT_DB_USER'],
        'password': os.environ['NFT_DB_PASSWORD'],
        'name': os.environ['NFT_DB_NAME'],
        'port': os.environ['NFT_DB_PORT'],
        'test': {
            'name': 'nft_test',
            'on_creation': [
                'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
            ]
        }
    }
}

# For testing, when AWS_REGION is not set, falls back to this
# fictional default region.
os.environ["MOTO_ALLOW_NONEXISTENT_REGION"] = '1'
os.environ["AWS_DEFAULT_REGION"] = 'neverland'

# Per blockchain basic configurations
from .solana import *  # noqa
from .queues import *  # noqa
