import logging
import os
import dotenv

dotenv_path = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    ),
    '.env'
)
dotenv.load_dotenv(dotenv_path)
DEBUG = os.getenv('DEBUG', 0)
#
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', logging.INFO)
POSTGRES_HOST = os.environ['POSTGRES_HOST']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_DATABASE = os.environ['POSTGRES_DATABASE']
POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)
DYNAMODB_ENDPOINT = os.getenv('DYNAMODB_ENDPOINT')
SQS_ENDPOINT = os.getenv('SQS_ENDPOINT')

# Per blockchain basic configurations
from .solana import *  # noqa
