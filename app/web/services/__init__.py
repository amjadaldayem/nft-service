import boto3

from app import settings
from .nft import NFTService
from .user import UserService

cognito_client = boto3.client('cognito-idp')
dynamodb_resource = boto3.resource('dynamodb')

user_service = UserService(
    user_pool_id=settings.COGNITO_USER_POOL_ID,
    user_pool_client_id=settings.COGNITO_APP_CLIENT_ID,
    cognito_client=cognito_client,
    dynamodb_resource=dynamodb_resource
)

nft_service = NFTService(
    dynamodb_resource=dynamodb_resource
)
