from typing import List

from solana.publickey import PublicKey
from solana.rpc import commitment
from solana.rpc.api import MemcmpOpt
from solana.rpc.types import DataSliceOpts, TokenAccountOpts

from app import settings
from app.blockchains.solana import consts
from .patch import CustomClient
from .nft_metadata import NFTMetadataProgramAccount

# Reference:
# https://github.com/metaplex-foundation/metaplex-program-library/blob/master/token-metadata/program/src/state.rs
METAPLEX_MAX_NAME_LENGTH = 32
METAPLEX_MAX_URI_LENGTH = 200
METAPLEX_MAX_SYMBOL_LENGTH = 10
METAPLEX_MAX_CREATOR_LEN = 32 + 1 + 1
METAPLEX_MAX_CREATOR_LIMIT = 5
METAPLEX_MAX_DATA_SIZE = (
        4
        + METAPLEX_MAX_NAME_LENGTH
        + 4
        + METAPLEX_MAX_SYMBOL_LENGTH
        + 4
        + METAPLEX_MAX_URI_LENGTH
        + 2 + 1 + 4
        + METAPLEX_MAX_CREATOR_LIMIT * METAPLEX_MAX_CREATOR_LEN
)
METAPLEX_MAX_METADATA_LEN = (
        1  # Key
        + 32  # Update authority
        + 32  # mint pubkey
        + METAPLEX_MAX_DATA_SIZE
        + 1  # Primary Sale
        + 1  # mutable
        + 9  # nonce
        + 34  # collection
        + 18  # use
        + 2  # token standard
        + 118  # padding
)
METAPLEX_CREATOR_ARRAY_START = (
        1 + 32 + 32 + 4
        + METAPLEX_MAX_NAME_LENGTH
        + 4
        + METAPLEX_MAX_URI_LENGTH
        + 4
        + METAPLEX_MAX_SYMBOL_LENGTH + 2 + 1 + 4
)

# References:
# https://solanacookbook.com/references/nfts.html#get-nft-mint-addresses
# Note it is not totally correct, just for reference.
# For Metaplex V1 use the Actual CandyMachine ID for the collection
CANDY_MACHINE_V1_PROGRAM = 'cndyAnrLdpjq1Ssp1z8xxDsB8dxe7u4HL5Nxi2K5WXZ'
# For Metaplex V2 use this candy machine
CANDY_MACHINE_V2_PROGRAM = 'cndy3Z4yapfJBmL3ShUp5exZKqR3z33thTzeNMm2gRZ'
