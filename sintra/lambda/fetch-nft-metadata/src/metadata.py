import base64
import logging
import os
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import List, Tuple, Union, Any, Dict

import base58
from solana.exceptions import SolanaRpcException
from solana.publickey import PublicKey
from src.async_client import SolanaHTTPClient, EthereumHTTPClient
from src.config import settings
from src.exception import DecodingException, UnableToFetchMetadataException
from src.model import NFTMetadata, SecondaryMarketEvent
from src.utils import MetadataUnpacker
import requests

logger = logging.getLogger(__file__)


alchemy_api_key = os.getenv("ALCHEMY_API_KEY")


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

        logger.info(
            f"Fetching metadata for program address key: {program_address_key}."
        )
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
        try:
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
        except SolanaRpcException as error:
            error_message = f"Failed to fetch metadata from Solana RPC for program account key: {program_account_key}"
            logger.error(error_message)
            raise UnableToFetchMetadataException(error_message) from error

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
            return self.unpacker.solana_metadata_unpack(data)
        except DecodingException as error:
            logger.error(error)
            raise ValueError from error


class EthereumMetadataFetcher(MetadataFetcher):
    def __init__(self) -> None:
        self.ethereum_client = EthereumHTTPClient(
            endpoint=settings.blockchain.ethereum.http.endpoint,
            timeout=settings.blockchain.ethereum.http.timeout,
        )
        self.unpacker = MetadataUnpacker()

    async def get_nft_metadata(self, event: SecondaryMarketEvent) -> NFTMetadata:
        token_key = event.token_key
        alchemy_params = token_key.split("/")
        contract_address = alchemy_params[0]
        token_id = alchemy_params[1]
        logger.info(f"Fetching metadata for contract address: {contract_address}.")
        nft_metadata = await self._fetch_metadata(contract_address, token_id)
        return nft_metadata

    async def _fetch_metadata(
        self, contract_address: str, token_id: str
    ) -> NFTMetadata:
        params = {
            "contractAddress": contract_address,
            "tokenId": token_id,
        }

        try:
            response = requests.get(
                f"{self.ethereum_client.endpoint}/{alchemy_api_key}/getNFTMetadata",
                params=params,
            )

            data = response.json()

            if not data:
                raise UnableToFetchMetadataException(
                    f"Unable to fetch metadata for token with token id: {token_id}."
                )
            try:
                nft_metadata = self._unpack_data(data)
                return nft_metadata
            except ValueError as error:
                raise UnableToFetchMetadataException(error) from error
        except ValueError as error:
            error_message = f"Failed to decode metadata JSON for token with id {token_id}: {error}"
            logger.error(error_message)
            raise UnableToFetchMetadataException(error_message) from error

    def _unpack_data(self, data: Dict[str, Any]) -> NFTMetadata:
        try:
            return self.unpacker.ethereum_metadata_unpack(data)
        except ValueError as error:
            logger.error(error)
