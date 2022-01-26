import os

from fastapi import Header
from app.models.user import User
from app.web import services
from app.web.api.exceptions import AuthenticationError


def get_auth_user(
        authorization: str = Header(None)
) -> User:
    try:
        user_data = services.user_service.extract_token(
            authorization,
            os.environ['COGNITO_PUBLIC_KEYS'],
            os.environ.get('VERIFY_TOKEN', False)
        )
    except Exception as e:
        raise AuthenticationError(data={'details': str(e)})

    return User(
        user_id=user_data['sub'],
        username=user_data['cognito:username'],
        preferred_username=user_data['cognito:username'],
        email=user_data['email'],
        joined_on=user_data['joined_on']
    )
