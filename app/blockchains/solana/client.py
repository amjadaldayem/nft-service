import base64
import dataclasses
import logging
import struct
from collections import namedtuple
from typing import Optional, List, Mapping, Union, Dict

import base58
import multiprocess as mp
from solana.publickey import PublicKey
from solana.rpc import commitment
from solana.rpc.api import MemcmpOpt, Client

from app import settings
from app.blockchains import BLOCKCHAIN_SOLANA
from app.blockchains.solana import consts
from app.blockchains.solana.patch import CustomClient
from app.models import (
    NftData,
    NftCreator,
    MediaFile
)

logger = logging.getLogger(__name__)

METADATA_PROGRAM_ID = PublicKey('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')

NFTCollectionInput = namedtuple(
    'NFTCollectionInput',
    [
        'update_authority',  # For fetching all mints
        'num_creators',
    ]
)

NFTMetadataProgramAccount = namedtuple(
    'NFTMetadataProgramAccount',
    [
        'public_key',
        'data',
        'encoding'
    ]
)


@dataclasses.dataclass
class SolanaNFTMetaData:
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

    @property
    def creators_info(self) -> List[Mapping]:
        creators = self.creators
        verified = self.verified
        share = self.share
        lc = len(creators)
        lv = len(verified)
        ls = len(share)

        if not (lc == lv == ls):
            return []

        return [
            {
                'creator': creators[i],
                'share': share[i],
                'verified': verified[i],
            }
            for i in range(lc)
        ]


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
        metadata = SolanaNFTMetaData(
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


def nft_get_collection_nfts(update_authority) -> List[NFTMetadataProgramAccount]:
    client = CustomClient(
        settings.SOLANA_RPC_ENDPOINT,
        commitment=commitment.Confirmed,
        timeout=60
    )

    # This is darn expensive ...
    resp = client.get_program_accounts(
        PublicKey(consts.METAPLEX_METADATA_PROGRAM),
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
            NFTMetadataProgramAccount(
                public_key=r['pubkey'],
                data=data,
                encoding=encoding
            )
        )
    return result


def nft_get_metadata(pda: NFTMetadataProgramAccount) -> Optional[SolanaNFTMetaData]:
    """

    Args:
        pda: The namedtuple `NFTMetadataProgramAccount`, usually from the result
            of a call to the `nft_get_collection_nfts` function.

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


def nft_get_metadata_by_token_account(pda_key: Union[str, PublicKey], client) -> Optional[SolanaNFTMetaData]:
    """
    Gets the NFT metadata by the `update_authority` key.

    Args:
        pda_key: The key to the `update_authority`, the wallet used to sign
            the new candy machine.
        client:
    Returns:

    """
    client = client or CustomClient(
        settings.SOLANA_RPC_ENDPOINT,
        commitment=commitment.Confirmed,
        timeout=15
    )
    resp = client.get_account_info(pda_key)

    value = resp['result']['value']
    if not value:
        return None
    data_field = value['data']
    data, encoding = data_field
    return nft_get_metadata(
        NFTMetadataProgramAccount(
            public_key=pda_key,
            data=data,
            encoding=encoding
        )
    )


def nft_get_metadata_by_token_key(token_key: str, client=None) -> SolanaNFTMetaData:
    """
    Gets the NFT metadata by the Token key (address).

    Args:
        token_key: The token key (or mint address in SolScan term).
        client:
    Returns:

    """
    metadata_pda_key = nft_get_token_account_by_token_key(token_key)
    return nft_get_metadata_by_token_account(metadata_pda_key, client)


def nft_get_nft_data(metadata: SolanaNFTMetaData, current_owner: str = "") -> NftData:
    """
    Gets the shared standard NFT model from metadata.

    Args:
        metadata: The token key (or mint address in SolScan term).
        current_owner: The current owner to set. This is not accessible from metadata.
    Returns:

    """
    import requests

    def transform_attributes(attrs):
        return {
            attr['trait_type']: str(attr['value']) if attr['value'] is not None else ''
            for attr in attrs if 'trait_type' in attr
        }

    # Let it throw if errors
    more_data = requests.get(metadata.uri).json()

    files = []
    image_uri = more_data.get('image', '')
    if image_uri:
        files.append(MediaFile(image_uri))

    files_raw = more_data.get('properties', {}).get('files')
    if files_raw:
        for d in files_raw:
            if not d.get('uri'):
                continue
            if d['uri'] == image_uri:
                # If repeated the image uri, just replace the type.
                files[0].file_type = d.get('type')
                continue
            files.append(
                MediaFile(
                    uri=d['uri'],
                    file_type=d.get('type', '')
                )
            )

    nft_data = NftData(
        blockchain_id=BLOCKCHAIN_SOLANA,
        token_address=metadata.mint_key,
        current_owner=current_owner,
        collection_key=metadata.update_authority,
        name=metadata.name,
        description=more_data.get('description', ''),
        symbol=metadata.symbol,
        primary_sale_happened=metadata.primary_sale_happened,
        metadata_uri=metadata.uri or "",
        creators=[
            NftCreator(address=a, verified=bool(v), share=int(s))
            for a, v, s in zip(
                metadata.creators, metadata.verified, metadata.share
            )
        ],
        ext_data={
            'update_authority': metadata.update_authority
        },
        edition=str(more_data.get('edition', -1)),
        attributes=transform_attributes(more_data.get('attributes', [])),
        external_url=more_data.get('external_url', ''),
        files=files
    )

    return nft_data


def nft_get_token_account_by_token_key(token_key: str) -> PublicKey:
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


def _get_transaction(client_signature_pair):
    client, sig = client_signature_pair
    try:
        resp = client.get_confirmed_transaction(sig)
    except Exception as e:
        logger.error("Cannot get transaction data due to %s", str(e))
        return None
    return resp.get('result')


def get_multi_transactions(signatures: List[str], batch_size=50) -> Dict[str, dict]:
    """

    Args:
        signatures:
        batch_size:

    Returns:
        Dict, mapping from signatures to the transaction data. The values can be null
        if the fetch for the trasactions failed.
    """
    batches = int(round(len(signatures) / batch_size))
    if batches == 0:
        batches = 1
    clients = [
        CustomClient(settings.SOLANA_RPC_ENDPOINT, timeout=60)
        for _ in range(batches)
    ]
    client_signature_pairs = [
        (clients[i % batches], signature)
        for i, signature in enumerate(signatures)
    ]
    pool = mp.Pool(batches)
    try:
        all_result = list(pool.imap(
            _get_transaction,
            client_signature_pairs,
            chunksize=batch_size
        ))
        pool.close()
    finally:
        pool.terminate()
        pool.join()

    return dict(zip(
        signatures,
        all_result
    ))


def fetch_transactions_for_pubkey_para(
        client: Client,
        public_key: str,
        before: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 500,
        batch_size: int = 50
) -> Dict[str, dict]:
    """
    Helper function to fetch transactions for the specified PubKey in parallel.
    The resulting transactions are sorted in the descending order (from most recent
    to the oldest).
    """

    resp = client.get_confirmed_signature_for_address2(
        public_key,
        before=before,
        until=until,
        limit=limit
    )
    signatures = [s['signature'] for s in resp['result']]

    all_result = get_multi_transactions(
        signatures, batch_size=batch_size
    )
    return all_result
