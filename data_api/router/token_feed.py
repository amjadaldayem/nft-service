import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from data_api.exception import ResourceNotFoundException
from data_api.model.token_feed import Token, TokenDetails
from data_api.service.token_feed import TokenFeedService

router = APIRouter(
    tags=["feed"], prefix="/v1/nft", responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)


@router.get(
    "/{blockchain_name}/{collection_name}/{token_name}",
    response_model=TokenDetails,
    description="Return detail information about token.",
)
async def read_token(
    blockchain_name: str = Path(description="Blockchain name in lowercase."),
    collection_name: str = Path(description="Slugified collection name."),
    token_name: str = Path(description="Slugified token name"),
    token_service: TokenFeedService = Depends(TokenFeedService),
) -> TokenDetails:
    try:
        token = token_service.read_token(blockchain_name, collection_name, token_name)
        return token
    except ResourceNotFoundException as error:
        logger.error(error)

        raise HTTPException(status_code=404, detail="Token does not exist.") from error
    except Exception as error:
        logger.error(error)

        raise HTTPException(status_code=500, detail="Internal server error.") from error


@router.get(
    "/tokens",
    response_model=List[Token],
    description="Return list of token sorted by latest market activity.",
)
async def read_tokens(
    timestamp: datetime = Query(
        None,
        description="Starting point to read tokens from. Timestamp format is datetime ISO format.",
        example="2022-01-01T15:05:05",
    ),
    token_service: TokenFeedService = Depends(TokenFeedService),
) -> List[Token]:
    try:
        if timestamp:
            tokens = token_service.read_tokens_from(timestamp)
        else:
            tokens = token_service.read_tokens()
        return tokens
    except Exception as error:
        logger.error(error)

        raise HTTPException(status_code=500, detail="Internal server error.") from error
