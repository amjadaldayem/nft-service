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

# For User table and indexes
DYNAMODB_USER_TABLE = os.environ['DYNAMODB_USER_TABLE']
DYNAMODB_USER_TABLE_GSI_EMAILS = os.environ['DYNAMODB_USER_TABLE_GSI_EMAILS']

# For NFT and collecions table
DYNAMODB_NFT_TABLE = os.environ['DYNAMODB_NFT_TABLE']

# For SME table and indexes, set through stacks repo
DYNAMODB_SME_TABLE = os.environ['DYNAMODB_SME_TABLE']
DYNAMODB_SME_TABLE_GSI_SME_ID = os.environ['DYNAMODB_SME_TABLE_GSI_SME_ID']
DYNAMODB_SME_TABLE_GSI_NFT_EVENTS = os.environ['DYNAMODB_SME_TABLE_GSI_NFT_EVENTS']
DYNAMODB_SME_TABLE_GSI_COLLECTION_EVENTS = os.environ['DYNAMODB_SME_TABLE_GSI_COLLECTION_EVENTS']
DYNAMODB_SME_TABLE_LSI_TIMESTAMP = os.environ['DYNAMODB_SME_TABLE_LSI_TIMESTAMP']
DYNAMODB_SME_TABLE_LSI_NFT_NAME = os.environ['DYNAMODB_SME_TABLE_LSI_NFT_NAME']
DYNAMODB_SME_TABLE_LSI_EVENTS = os.environ['DYNAMODB_SME_TABLE_LSI_EVENTS']
DYNAMODB_SME_TABLE_LSI_BUY_LISTING_EVENTS = os.environ['DYNAMODB_SME_TABLE_LSI_BUY_LISTING_EVENTS']

# The number of minutes for the aggregation time window for
# secondary market events. Events within this time window will
# be saved under the same Partition (in DynamoDb).
SME_AGGREGATION_WINDOW = int(os.getenv('SME_AGGREGATION_WINDOW', '5'))

os.environ["MOTO_ALLOW_NONEXISTENT_REGION"] = '1'
# Per blockchain basic configurations
from .solana import *  # noqa
