import os

import orjson
from fastapi import Header
from app.models.user import User
from app.web import services
from app.web.api.exceptions import AuthenticationError, UserNotFound


def get_auth_user(
        authorization: str = Header(None)
) -> User:
    try:
        user_data = services.user_service.extract_token(
            authorization,
            orjson.loads(os.environ['COGNITO_PUBLIC_KEYS']),
            os.environ.get('VERIFY_TOKEN', False)
        )
    except Exception as e:
        raise AuthenticationError(data={'details': str(e)})
    user = services.user_service.get_user(user_data['sub'])
    if not user:
        raise UserNotFound(data={'details': f"User sub = {user_data['sub']}"})
    return user
