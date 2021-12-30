import asyncio
import base64
import dataclasses
import struct
import logging
import time
from collections import namedtuple
from typing import Optional, List, Mapping, Union, Iterable, Dict

import base58
from solana.publickey import PublicKey
from solana.rpc import commitment
from solana.rpc.api import MemcmpOpt
from solana.rpc.async_api import AsyncClient

from app import settings
from app.blockchains.solana import consts
from app.blockchains.solana.patch import CustomAsyncClient

logger = logging.getLogger(__name__)

METADATA_PROGRAM_ID = PublicKey('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')

NftCollectionInput = namedtuple(
    'NftCollectionInput',
    [
        'update_authority',  # For fetching all mints
        'num_creators',
    ]
)

NftMetadataProgramAccount = namedtuple(
    'NftMetadataProgramAccount',
    [
        'public_key',
        'data',
        'encoding'
    ]
)


@dataclasses.dataclass
class NftMetaData:
    """
    The metadata of an NFT, note that to retrieve the actual content of the
    metadata, we need to issue HTTP GET against the `uri` field again. This
    can be potentially expensive and needed to be handled carefully.
    """
    mint_key: str  # Token address in SolScan speak
    update_authority: str
    primary_sale_happened: bool
    is_mutable: bool
    name: Optional[str]
    symbol: Optional[str]
    uri: Optional[str]
    seller_fee_basis_points: str
    # Num of Creators is important for use with analysis on secondary
    # sales/listing
    creators: List[str]
    verified: List[str]
    share: List[str]
    ext_data: Mapping = dataclasses.field(default_factory=dict)


class RPCHelper:

    @staticmethod
    def memcmp_opts_update_authority_filters(update_authority):
        return {
            'memcmp_opts': [
                MemcmpOpt(offset=1, bytes=update_authority),
            ]
        }

    @staticmethod
    def memcmp_opts_candy_machine_filters(candy_machine_public_key):
        return {
            'memcmp_opts': [
                MemcmpOpt(offset=326, bytes=candy_machine_public_key),
            ]
        }

    @staticmethod
    def memcmp_opts_token_accounts_filters(mint):
        """
        Finds all token accounts for a specific mint.
        https://spl.solana.com/token#finding-all-token-accounts-for-a-specific-mint

        :param mint:
        :return:
        """
        return {
            'data_size': 165,
            'memcmp_opts': [
                MemcmpOpt(offset=0, bytes=mint),
            ]
        }

    @staticmethod
    def metadata_unpack_data(data):
        if data[0] != 4:
            return None
        i = 1
        source_account = base58.b58encode(
            bytes(struct.unpack('<' + "B" * 32, data[i:i + 32]))
        )
        i += 32
        mint_account = base58.b58encode(
            bytes(struct.unpack('<' + "B" * 32, data[i:i + 32]))
        )
        i += 32
        name_len = struct.unpack('<I', data[i:i + 4])[0]
        i += 4
        name = struct.unpack('<' + "B" * name_len, data[i:i + name_len])
        i += name_len
        symbol_len = struct.unpack('<I', data[i:i + 4])[0]
        i += 4
        symbol = struct.unpack('<' + "B" * symbol_len, data[i:i + symbol_len])
        i += symbol_len
        uri_len = struct.unpack('<I', data[i:i + 4])[0]
        i += 4
        uri = struct.unpack('<' + "B" * uri_len, data[i:i + uri_len])
        i += uri_len
        fee = struct.unpack('<h', data[i:i + 2])[0]
        i += 2
        has_creator = data[i]
        i += 1
        creators = []
        verified = []
        share = []
        if has_creator:
            creator_len = struct.unpack('<I', data[i:i + 4])[0]
            i += 4
            for _ in range(creator_len):
                creator = base58.b58encode(bytes(struct.unpack('<' + "B" * 32, data[i:i + 32])))
                creators.append(bytes(creator).decode('utf-8'))
                i += 32
                verified.append(data[i])
                i += 1
                share.append(data[i])
                i += 1
        primary_sale_happened = bool(data[i])
        i += 1
        is_mutable = bool(data[i])
        metadata = NftMetaData(
            update_authority=bytes(source_account).decode('utf-8'),
            mint_key=bytes(mint_account).decode('utf-8'),
            primary_sale_happened=primary_sale_happened,
            is_mutable=is_mutable,
            name=bytes(name).decode("utf-8").strip("\x00"),
            symbol=bytes(symbol).decode("utf-8").strip("\x00"),
            uri=bytes(uri).decode("utf-8").strip("\x00"),
            seller_fee_basis_points=fee,
            creators=creators,
            verified=verified,
            share=share
        )
        return metadata


async def nft_get_collection_pdas(update_authority) -> List[NftMetadataProgramAccount]:
    async with CustomAsyncClient(
            settings.SOLANA_RPC_ENDPOINT,
            commitment=commitment.Confirmed,
            timeout=60
    ) as client:
        await client.is_connected()
        resp = await client.get_program_accounts(
            PublicKey(consts.METAPLEX_PUBKEY),
            encoding='base64',
            commitment=commitment.Confirmed,
            **RPCHelper.memcmp_opts_update_authority_filters(
                update_authority
            )
        )
        result = []
        for r in resp['result']:
            data, encoding = r['account']['data']
            result.append(
                NftMetadataProgramAccount(
                    public_key=r['pubkey'],
                    data=data,
                    encoding=encoding
                )
            )
        return result


async def nft_get_metadata(pda: NftMetadataProgramAccount) -> Optional[NftMetaData]:
    """

    Args:
        pda: The namedtuple `NftMetadataProgramAccount`, usually from the result
            of a call to the `nft_get_collection_pdas` function.

    Returns:

    """
    data = (
        base64.b64decode(pda.data)
        if pda.encoding == 'base64'
        else
        base58.b58decode(pda.data)
    )
    try:
        return RPCHelper.metadata_unpack_data(data)
    except Exception as e:
        logger.error(str(e))
        return None


async def nft_get_metadata_by_pda_key(pda_key: Union[str, PublicKey]) -> Optional[NftMetaData]:
    """
    Gets the NFT metadata by the `update_authority` key.

    Args:
        pda_key: The key to the `update_authority`, the wallet used to sign
            the new candy machine.

    Returns:

    """
    async with CustomAsyncClient(
            settings.SOLANA_RPC_ENDPOINT,
            commitment=commitment.Confirmed,
            timeout=15
    ) as client:
        await client.is_connected()
        resp = await client.get_account_info(pda_key)

        value = resp['result']['value']
        if not value:
            return None
        data_field = value['data']
        data, encoding = data_field
        return await nft_get_metadata(
            NftMetadataProgramAccount(
                public_key=pda_key,
                data=data,
                encoding=encoding
            )
        )


async def nft_get_metadata_by_token_key(token_key: str) -> NftMetaData:
    """
    Gets the NFT metadata by the Token key (address).

    Args:
        token_key: The token key (or mint address in SolScan term).

    Returns:

    """
    metadata_pda_key = await nft_get_metadata_pda_key_by_token_key(token_key)
    return await nft_get_metadata_by_pda_key(metadata_pda_key)


async def nft_get_metadata_pda_key_by_token_key(token_key: str) -> PublicKey:
    """
    Finds the `update_authority` key from the given token key.

    Args:
        token_key: The token key (or mint address in SolScan term).

    Returns:
    """

    return PublicKey.find_program_address(
        [
            b'metadata',
            bytes(METADATA_PROGRAM_ID),
            bytes(
                PublicKey(token_key)
                if type(token_key) is not PublicKey else token_key
            )
        ],
        METADATA_PROGRAM_ID
    )[0]


# TODO:
#   Fetch transactions related to the Candy Machine
#   E.g., 3LUbx4G9YZjiN4HYCL7pm5Wzng6Hy87Z4x1cvYUsD55aszuWimhTVVytC6bhYDbKCNCuUa1Wnuwq7Xr4eGV3SGms
#   The 2nd parameter (the wallet) is the update_authority for InitializeCandyMachine instruction
#   The could be use to fetch the new collection.

async def _get_transaction_with_index(client: AsyncClient, idx, sig):
    resp = await client.get_confirmed_transaction(sig)
    return idx, resp['result']


async def fetch_transactions_for_pubkey_para(
        async_client: AsyncClient,
        public_key: str,
        before: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 500,
        batch_size: int = 50
) -> List[Dict]:
    """
    Helper function to fetch transactions for the specified PubKey in parallel.
    The resulting transactions are sorted in the descending order (from most recent
    to the oldest).
    """
    await async_client.is_connected()
    resp = await async_client.get_confirmed_signature_for_address2(
        public_key,
        before=before,
        until=until,
        limit=limit
    )
    signatures = [s['signature'] for s in resp['result']]

    size = len(signatures)
    start = 0
    all_result = []

    while start < size:
        segment = signatures[start: start + batch_size]
        tasks = [
            _get_transaction_with_index(async_client, i, signature)
            for i, signature in enumerate(segment)
        ]
        segment_result = list(await asyncio.gather(*tasks))
        segment_result.sort()
        _, events = zip(*segment_result)
        all_result.extend(events)
        start += batch_size
        time.sleep(0.1)

    return all_result
