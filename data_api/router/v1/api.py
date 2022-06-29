from fastapi import APIRouter

from data_api.router.v1.endpoint import token_feed

router = APIRouter()
router.include_router(token_feed.router, prefix="/feed", tags=["Feed"])
