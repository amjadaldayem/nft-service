import os
import boto3
from .user import UserService  # noqa

cognito_client = boto3.client('cognito-idp')
dynamodb_resource = boto3.resource('dynamodb')

user_service = UserService(
    user_pool_id=os.getenv('COGNITO_USER_POOL_ID'),
    user_pool_client_id=os.getenv('COGNITO_APP_CLIENT_ID'),
    cognito_client=cognito_client,
    dynamodb_resource=dynamodb_resource
)
