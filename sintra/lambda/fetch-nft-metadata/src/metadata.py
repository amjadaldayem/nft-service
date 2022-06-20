import base64
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

import base58
from solana.publickey import PublicKey
from src.async_client import SolanaHTTPClient
from src.config import settings
from src.exception import DecodingException, UnableToFetchMetadataException
from src.model import NFTMetadata, SecondaryMarketEvent
from src.utils import MetadataUnpacker

logger = logging.getLogger(__file__)


class MetadataFetcher(ABC):
    @abstractmethod
    async def get_nft_metadata(self, event: SecondaryMarketEvent) -> NFTMetadata:
        """Download metadata for NFT based on it's token key."""


class SolanaMetadataFetcher(MetadataFetcher):
    def __init__(self) -> None:
        self.METADATA_PROGRAM_ID = PublicKey(
            "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
        )
        self.solana_client = SolanaHTTPClient(
            endpoint=settings.blockchain.solana.http.endpoint,
            timeout=settings.blockchain.solana.http.timeout,
            username=os.getenv("SOLANA_RPC_HTTP_USERNAME"),
            password=os.getenv("SOLANA_RPC_HTTP_PASSWORD"),
        )
        self.unpacker = MetadataUnpacker()

    async def get_nft_metadata(self, event: SecondaryMarketEvent) -> NFTMetadata:
        program_address_key = self._program_address(event.token_key)
        nft_metadata = await self._fetch_metadata(program_address_key)
        return nft_metadata

    def _program_address(self, token_key: Union[str, PublicKey]) -> PublicKey:
        """Finds the program_address key from the given token key.

        Args:
            token_key: The token key or mint address.

        Returns: Program address key.
        """
        if not isinstance(token_key, PublicKey):
            public_key = PublicKey(token_key)
        else:
            public_key = token_key

        seeds: List[bytes] = [
            b"metadata",
            bytes(self.METADATA_PROGRAM_ID),
            bytes(public_key),
        ]
        program_address: Tuple[PublicKey, int] = PublicKey.find_program_address(
            seeds, self.METADATA_PROGRAM_ID
        )

        return program_address[0]

    async def _fetch_metadata(
        self, program_account_key: Union[str, PublicKey]
    ) -> NFTMetadata:
        """
        Gets the NFT metadata by the program account key.

        Args:
            program_account_key: The key to the `update_authority`, the wallet used to sign
                the new candy machine.
            client: Async HTTP client.
        Returns: NFTMetadata model object.

        """
        response = await self.solana_client.get_account_info(program_account_key)

        value = response["result"]["value"]
        if not value:
            raise UnableToFetchMetadataException(
                f"Can't find account info for program key: {program_account_key}."
            )
        data, encoding = value["data"]
        try:
            nft_metadata = self._unpack_data(data, encoding)
            return nft_metadata
        except ValueError as error:
            raise UnableToFetchMetadataException(error) from error

    def _unpack_data(self, data: str, encoding: str) -> NFTMetadata:
        """Decode encoded metadata.

        Args:
            data: Encoded NFT metadata.
            encoding: Encoding type of input data.

        Returns: NFTMetadata model object.

        """
        if encoding == "base64":
            data = base64.b64decode(data)
        else:
            data = base58.b58decode(data)

        try:
            return self.unpacker.unpack(data)
        except DecodingException as error:
            logger.error(error)
            raise ValueError from error
