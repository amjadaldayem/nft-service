import logging
from typing import Union, List

from app.blockchains import solana
from app.models.helpers import pg_create_async_engine, pg_get_session
from slab.messaging import DRoutine, OK, DRoutineBaseParams

logger = logging.getLogger(__name__)


class NftInputParam(DRoutineBaseParams):
    update_authority: str = ''


class NftDRoutine(DRoutine):
    TIMEOUT = 180
    params_class = NftInputParam

    async def run(self, params: NftInputParam) -> Union[int, float]:
        async_session = pg_get_session()
        async with async_session() as session:
            # Checks if the collection is already there
            # In Solana, the `update_authority` maps to the onchain_id
            await session.execute()
            async with session.begin():
                session.add_all(
                    [
                    ]
                )

        update_authority = params.update_authority
        if not update_authority:
            logger.warning("Empty `update_authority`.")
            return OK
        pda_accounts = await solana.nft_get_collection_pdas(update_authority)

        return OK

    async def on_timeout(self, timeout) -> Union[int, float]:
        return OK
