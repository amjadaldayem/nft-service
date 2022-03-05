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
ENV_PROD = 'prod'
ENV_DEV = 'dev'
ENV_LOCAL = 'local'
ENV_TEST = 'test'

# DEPLOYMENT_ENV, choices: prod, staging, dev, local
DEPLOYMENT_ENV = os.getenv('DEPLOYMENT_ENV', ENV_PROD)
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', logging.INFO)
DYNAMODB_ENDPOINT = os.getenv('DYNAMODB_ENDPOINT')
SQS_ENDPOINT = os.getenv('SQS_ENDPOINT')

SENTRY_IO_DSN = os.getenv('SENTRY_IO_DSN', '')
SENTRY_IO_TRACE_SAMPLERATE = float(os.getenv('SENTRY_IO_TRACE_SAMPLERATE', '1.0'))
SENTRY_IO_DEBUG = bool(int(os.getenv('SENTRY_IO_DEBUG', '0')))
SENTRY_IO_MAX_BREADCRUMBS = int(os.getenv('SENTRY_IO_MAX_BREADCRUMBS', '20'))
SENTRY_IO_CAPTURE_REQUEST_BODIES = os.getenv('SENTRY_IO_CAPTURE_REQUEST_BODIES', 'small')
SENTRY_IO_WITH_LOCALS = bool(int(os.getenv('SENTRY_IO_WITH_LOCALS', '0')))

AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')

COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_APP_CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')

# The number of minutes for the aggregation time window for
# secondary market events. Events within this time window will
# be saved under the same Partition (in DynamoDb).
SME_AGGREGATION_WINDOW = int(os.getenv('SME_AGGREGATION_WINDOW', '5'))
# The seconds to deduct from current time to make aritificial
# delay when fetching SMEs. Even client specifies a more recent timestamp to start.
# However, this can be overridden per user
# case.
SME_FETCH_DEFAULT_LAG = int(os.getenv('SME_FETCH_DEFAULT_LAG', '180'))
SME_FETCH_DEFAULT_TIMESPAN = int(os.getenv('SME_FETCH_DEFAULT_TIMESPAN', 60))
SME_FETCH_PAGE_SIZE = int(os.getenv('SME_FETCH_PAGE_SIZE', 10))
