import os

from fastapi.responses import ORJSONResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app import settings
from app.settings import (
    ENV_TEST,
    ENV_LOCAL
)
from app.utils.fastapi_ex import jsonrpc

jsonrpc_app = jsonrpc.API(default_response_class=ORJSONResponse)

if settings.DEPLOYMENT_ENV in (ENV_LOCAL, ENV_TEST):
    app = jsonrpc_app
else:
    app = SentryAsgiMiddleware(jsonrpc_app)
api_v1_noauth = jsonrpc.Entrypoint('/v1/rpc')
api_v1_auth = jsonrpc.Entrypoint('/v1/_rpc')
