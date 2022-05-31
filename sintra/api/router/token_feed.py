from typing import List

from fastapi import APIRouter, Depends

from sintra.api.model.token_feed import TokenFeed
from sintra.api.service.token_feed import TokenFeedService

router = APIRouter(tags=["feed"], responses={404: {"description": "Not found"}})


@router.get("/nft/{blockchain}/{collection_name}/{nft_item_name}")
async def read_tokens(
    blockchain: str,
    collection_name: str,
    nft_item_name: str,
    token_service: TokenFeedService = Depends(TokenFeedService),
) -> List[TokenFeed]:
    tokens = token_service.read_token_feed(blockchain, collection_name, nft_item_name)

    return tokens
