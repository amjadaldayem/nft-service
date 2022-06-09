import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from sintra.api.exception import ResourceNotFoundException
from sintra.api.model.token_feed import Token, TokenDetails
from sintra.api.service.token_feed import TokenFeedService

router = APIRouter(
    tags=["feed"], prefix="/v1/nft/feed", responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)


@router.get("/token/{token_id}")
async def read_token(
    token_id: str, token_service: TokenFeedService = Depends(TokenFeedService)
) -> TokenDetails:
    try:
        token = token_service.read_token(token_id)
        return token
    except ResourceNotFoundException as error:
        logger.error(error)

        raise HTTPException(
            status_code=404, detail=f"Token with id: {token_id} does not exist."
        ) from error
    except Exception as error:
        logger.error(error)

        raise HTTPException(status_code=500, detail="Internal server error.") from error


@router.get("/tokens")
async def read_tokens(
    token_service: TokenFeedService = Depends(TokenFeedService),
) -> List[Token]:
    try:
        tokens = token_service.read_tokens()
        return tokens
    except Exception as error:
        logger.error(error)

        raise HTTPException(status_code=500, detail="Internal server error.") from error


@router.get("/tokens")
async def read_tokens_from(
    timestamp: int,
    token_service: TokenFeedService = Depends(TokenFeedService),
) -> List[Token]:
    try:
        tokens = token_service.read_tokens_from(timestamp)
        return tokens
    except Exception as error:
        logger.error(error)

        raise HTTPException(status_code=500, detail="Internal server error.") from error
