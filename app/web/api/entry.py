from fastapi.responses import ORJSONResponse

from app.utils.fastapi_ex import jsonrpc

app = jsonrpc.API(default_response_class=ORJSONResponse)

api_v1_noauth = jsonrpc.Entrypoint('/v1/rpc')
api_v1_auth = jsonrpc.Entrypoint('/v1/_rpc')
