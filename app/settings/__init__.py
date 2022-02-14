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

# The number of minutes for the aggregation time window for
# secondary market events. Events within this time window will
# be saved under the same Partition (in DynamoDb).
SME_AGGREGATION_WINDOW = int(os.getenv('SME_AGGREGATION_WINDOW', '5'))
# The seconds to deduct from current time to make aritificial
# delay when fetching SMEs. However this can be overridden per user
# case.
SME_FETCH_DEFAULT_LAG = int(os.getenv('SME_FETCH_DEFAULT_LAG', '300'))

# Per blockchain basic configurations
from .solana import *  # noqa
