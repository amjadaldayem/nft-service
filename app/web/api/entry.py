import fastapi_jsonrpc as jsonrpc

app = jsonrpc.API()

api_v1_noauth = jsonrpc.Entrypoint('/v1/rpc')
api_v1_auth = jsonrpc.Entrypoint('/v1/_rpc')
