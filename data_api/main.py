from fastapi import FastAPI
from mangum import Mangum

from data_api.router.v1 import api

app = FastAPI()

app.include_router(api.router, prefix="/api/v1")

handler = Mangum(app)
