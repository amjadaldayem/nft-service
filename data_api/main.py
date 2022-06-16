from fastapi import FastAPI

from data_api.router import token_feed

app = FastAPI()

app.include_router(token_feed.router)
