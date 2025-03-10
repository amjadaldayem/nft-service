import os

import orjson
from fastapi import Header
from app.models.user import User
from app.web import services
from ..exceptions import AuthenticationError, UserNotFound
from ...utils import notify_error


def get_auth_user(
        authorization: str = Header(None)
) -> User:
    try:
        user_data = services.user_service.extract_token(
            authorization,
            orjson.loads(os.getenv('COGNITO_PUBLIC_KEYS', "[]")),
            int(os.environ.get('VERIFY_TOKEN', '0'))
        )
    except Exception as e:
        notify_error(e, metadata={'token': authorization})
        raise AuthenticationError(data={'details': str(e)})
    user = services.user_service.get_user(user_data['sub'])
    if not user:
        raise UserNotFound(data={'details': f"User sub = {user_data['sub']}"})
    return user
