import functools
import logging
from typing import Union, List, Mapping

import slugify as slugify
from sqlalchemy.future import select

from app.blockchains import solana, BLOCKCHAIN_SOLANA
from app.blockchains.solana.client import NFTMetaData
from app.models.manager import SQLDBManager
from app.models.models import NFTCollection, NFT
from slab.messaging import DRoutine, OK, DRoutineBaseParams

logger = logging.getLogger(__name__)


def map_nft_metadata_to_nft_model(nft_collection_id, nft_metadata: NFTMetaData) -> NFT:
    """
    TODO: Finish this later.
    Args:
        nft_collection_id:
        nft_metadata:

    Returns:

    """
    name = nft_metadata.name
    return NFT(
        name=name,
        slug=slugify.slugify(name),
        token_address=nft_metadata.mint_key,
        nft_collection_id=nft_collection_id,
        is_mutable=nft_metadata.is_mutable,
    )


def fetch_extra_metadata(nft_metadata_list: List[NFTMetaData]) -> Mapping:
    """
    TODO: Finish this.
    Visits the `uri` property on each NFTMetadata, fetch the JSON info from
    `uri`

    Args:
        nft_metadata_list:

    Returns:
        Mapping from mint_key to extra metadata dict
    """


class NftCollectionInputParam(DRoutineBaseParams):
    update_authority: str = ''


class NftCollectionDRoutine(DRoutine):
    TIMEOUT = 180
    params_class = NftCollectionInputParam

    def run(self, params: NftCollectionInputParam) -> Union[int, float]:
        update_authority = params.update_authority
        if not update_authority:
            logger.warning("Empty `update_authority`.")
            return OK

        sessionmaker = SQLDBManager.create('nft').async_sessionmaker
        with sessionmaker() as session:
            # Checks if the collection is already there
            # In Solana, the `update_authority` maps to the onchain_id
            r = session.execute(
                select(NFTCollection).where(
                    NFTCollection.onchain_id == update_authority
                )
            )
            nft_collection = r.scalar()
            if nft_collection:
                logger.warning(
                    "NFT Collection %s is being processed or already in. Skipping",
                    update_authority
                )
                return OK

        # If the collection does not exist, fetch it.
        # Placeholder for collection first
        with sessionmaker() as session:
            collection = NFTCollection(
                name="unnamed",
                blockchain_id=BLOCKCHAIN_SOLANA,
                onchain_id=update_authority,
                data_status=NFTCollection.DATA_STATUS_UPDATING
            )
            with session.begin():
                session.add(collection)

            # Expensive...
            pdas = solana.nft_get_collection_pdas(update_authority)
            if not pdas:
                logger.error(
                    "No NFT found for NFT Collection %s. Skipping",
                    update_authority
                )
                return OK

            nft_metadata_list = [solana.nft_get_metadata(pda) for pda in pdas]
            if not nft_metadata_list:
                logger.error(
                    "No NFT metadata can be fetched for NFT Collection %s, though "
                    "%s accounts found. Skipping",
                    update_authority,
                    len(pdas)
                )
                return OK

            # Fetch the information at `uri` for each NFT in parallel
            nft_extra_metadata_map = fetch_extra_metadata(
                nft_metadata_list
            )

            one_nft = nft_metadata_list[0]  # type: NFTMetaData

            nft_models = list(filter(bool, map(
                functools.partial(map_nft_metadata_to_nft_model, collection.pk),
                nft_metadata_list
            )))
            logger.info(
                "Found %s NFTs for NFT Collection %s.",
                len(nft_models),
                update_authority
            )

            with session.begin():
                # Updates the NFT Collection model instance
                collection.name = common_prefix
                collection.slug = slugify.slugify(common_prefix)
                collection.creators = one_nft.creators_info  # Stores JSONB
                session.add_all(nft_models)

        return OK

    def on_timeout(self, timeout) -> Union[int, float]:
        return OK
