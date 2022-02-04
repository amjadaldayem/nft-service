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

COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_APP_CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')

DYNAMODB_USER_TABLE = os.getenv('DYNAMODB_USER_TABLE', 'user')
DYNAMODB_NFT_TABLE = os.getenv('DYNAMODB_NFT_TABLE', 'nft')
DYNAMODB_SME_TABLE = os.getenv('DYNAMODB_SME_TABLE', 'sme')

os.environ["MOTO_ALLOW_NONEXISTENT_REGION"] = '1'
# Per blockchain basic configurations
from .solana import *  # noqa
