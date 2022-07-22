import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from time import time
from typing import Any, Dict, List

import requests
import slugify
from requests import HTTPError, Timeout
from src.config import settings
from src.exception import FetchTokenDataException, UnknownBlockchainException
from src.model import MediaFile, NFTCreator, NFTData, NFTMetadata
from src.utils import base_curency_for_blockchain, blockchain_id_to_name

logger = logging.getLogger(__name__)
alchemy_api_key = os.getenv("ALCHEMY_API_KEY")


class TokenDataFetcher(ABC):
    @abstractmethod
    async def get_token_data(self, metadata: NFTMetadata) -> NFTData:
        """Download NFT data based on metadata URI."""


class SolanaTokenDataFetcher(TokenDataFetcher):
    def __init__(
        self, username=None, password=None, allow_redirects=True, timeout=30
    ) -> None:
        self.session: requests.Session = requests.Session()
        self.session.auth = (username, password)
        self.timeout = timeout
        self.allow_redirects = allow_redirects

    async def get_token_data(self, metadata: NFTMetadata) -> NFTData:
        try:
            response: requests.Response = self.session.get(
                url=metadata.uri,
                allow_redirects=self.allow_redirects,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                raise FetchTokenDataException(
                    f"Response status code: {response.status_code}. Reason: {response.reason}."
                )
            token_data = response.json()
            return self._transform_token_data(metadata, token_data)
        except (Timeout, HTTPError) as error:
            logger.error(error)
            raise FetchTokenDataException() from error
        except requests.JSONDecodeError as error:
            logger.error(
                f"Failed to fetch and decode token attributes: {error}\n"
                f"Status code: {response.status_code}"
                f"Reason: {response.reason}"
            )
            raise json.JSONDecodeError from error

    def _transform_token_data(
        self, metadata: NFTMetadata, token_data: Dict[str, Any]
    ) -> NFTData:

        if not metadata or not token_data:
            return None

        media_files: List[MediaFile] = []
        image_uri = token_data.get("image", None)
        if image_uri:
            media_files.append(MediaFile(uri=image_uri))

        properties = token_data.get("properties", {})
        property_files = properties.get("files", None)

        if property_files:
            for property_file in property_files:
                if isinstance(property_file, Dict):
                    uri = property_file.get("uri", "")
                    file_type = property_file.get("type", "")
                    if uri == image_uri:
                        media_files[0].file_type = file_type
                        continue
                elif isinstance(property_file, List):
                    for uri_data in property_file:
                        uri = uri_data.get("uri", "")
                        file_type = uri_data.get("type", "")
                        if uri == image_uri:
                            media_files[0].file_type = file_type
                            continue
                else:
                    uri = property_file if isinstance(property_file, str) else ""
                    file_type = ""

                media_files.append(MediaFile(uri=uri, file_type=file_type))

        token_creators = [
            NFTCreator(address=address, verified=bool(verified), share=int(shared))
            for address, verified, shared in zip(
                metadata.creators, metadata.verified, metadata.share
            )
        ]
        token_attributes = self._transform_token_attributes(
            token_data.get("attributes", [])
        )

        try:
            blockchain_name = blockchain_id_to_name(metadata.blockchain_id)
        except UnknownBlockchainException as error:
            logger.error(error)
            blockchain_name = None

        collection_data = token_data.get("collection", None)
        if collection_data:
            collection_name = collection_data["name"]
        else:
            collection_name = None

        blocktime_datetime = datetime.utcfromtimestamp(metadata.blocktime)
        blocktime_formatted = blocktime_datetime.strftime("%Y-%m-%d %H:%M:%S")
        event_time = datetime.utcfromtimestamp(time())
        event_time_formatted = event_time.strftime("%Y-%m-%d %H:%M:%S")

        nft_data = NFTData(
            blockchain_id=metadata.blockchain_id,
            blockchain_name=blockchain_name,
            collection_id=f"bc-{blockchain_name}-{metadata.program_account_key}",
            collection_name=collection_name,
            collection_name_slug=slugify.slugify(collection_name),
            market_id=metadata.market_id,
            token_key=metadata.token_key,
            owner=metadata.owner,
            token_id=f"bc-{blockchain_name}-{metadata.token_key}",
            token_name=metadata.name,
            token_name_slug=slugify.slugify(metadata.name),
            description=token_data.get("description", ""),
            symbol=metadata.symbol,
            primary_sale_happened=metadata.primary_sale_happened,
            last_market_activity=metadata.last_market_activity,
            timestamp_of_market_activity=blocktime_formatted,
            event_timestamp=event_time_formatted,
            metadata_uri=metadata.uri,
            attributes=token_attributes,
            transaction_hash=metadata.transaction_hash,
            price=metadata.price,
            price_currency=base_curency_for_blockchain(metadata.blockchain_id),
            creators=token_creators,
            edition=str(token_data.get("edition", -1)),
            external_url=token_data.get("external_url", ""),
            media_files=media_files,
        )

        return nft_data

    def _transform_token_attributes(self, attributes) -> Dict[str, str]:
        token_attributes = {
            str(attribute["trait_type"]).capitalize(): str(attribute["value"])
            for attribute in attributes
            if "trait_type" in attribute
        }
        return token_attributes


class EthereumTokenDataFetcher(TokenDataFetcher):
    def __init__(self) -> None:
        self.endpoint = settings.blockchain.ethereum.http.endpoint
        self.contract_metadata_endpoint = (
            settings.blockchain.ethereum.http.contract_metadata_endpoint
        )
        self.timeout = settings.blockchain.ethereum.http.timeout

    async def get_token_data(self, metadata: NFTMetadata) -> NFTData:
        token_key = metadata.token_key
        alchemy_params = token_key.split("/")
        contract_address = alchemy_params[0]
        token_id = alchemy_params[1]
        params = {
            "contractAddress": contract_address,
            "tokenId": token_id,
        }
        try:
            response = requests.get(
                url=f"{self.endpoint}/{alchemy_api_key}/getNFTMetadata",
                timeout=self.timeout,
                params=params,
            )
            if response.status_code >= 400:
                raise FetchTokenDataException(
                    f"Response status code: {response.status_code}. Reason: {response.reason}."
                )
            token_data = response.json()

            params = {
                "contractAddress": contract_address,
            }

            response = requests.get(
                url=f"{self.contract_metadata_endpoint}/{alchemy_api_key}/getContractMetadata",
                timeout=self.timeout,
                params=params,
            )

            if response.status_code >= 400:
                raise FetchTokenDataException(
                    f"Response status code: {response.status_code}. Reason: {response.reason}."
                )
            collection_data = response.json()
            return self._transform_token_data(metadata, token_data, collection_data)
        except (Timeout, HTTPError) as error:
            logger.error(error)
            raise FetchTokenDataException() from error
        except requests.JSONDecodeError as error:
            logger.error(error)
            raise json.JSONDecodeError from error

    def _transform_token_data(
        self,
        metadata: NFTMetadata,
        token_data: Dict[str, Any],
        collection_data: Dict[str, Any],
    ) -> NFTData:

        token_creators = []
        media_files: List[MediaFile] = []
        token_metadata = token_data.get("metadata", None)
        description = ""
        external_url = ""
        image_uri = ""
        image_file_type = ""
        token_attributes = {}
        if token_metadata:
            description_data = token_metadata.get("description", None)
            if description_data:
                description = description_data

            external_url_data = token_metadata.get("external_url", None)
            if external_url_data:
                external_url = external_url_data

            image_data = token_metadata.get("image", None)
            if image_data:
                image_uri = image_data
                image_file_type = image_uri.split("/")[-1].split(".")[-1]

            attributes_data = token_metadata.get("attributes", [])
            if attributes_data:
                token_attributes = self._transform_token_attributes(attributes_data)

        media_files.append(MediaFile(uri=image_uri, file_type=image_file_type))

        try:
            blockchain_name = blockchain_id_to_name(metadata.blockchain_id)
        except UnknownBlockchainException as error:
            logger.error(error)
            blockchain_name = None

        contract_metadata = collection_data.get("contractMetadata", None)
        collection_name = None
        if contract_metadata:
            collection_name = contract_metadata.get("name", None)

        blocktime_datetime = datetime.utcfromtimestamp(metadata.blocktime)
        blocktime_formatted = blocktime_datetime.strftime("%Y-%m-%d %H:%M:%S")
        event_time = datetime.utcfromtimestamp(time())
        event_time_formatted = event_time.strftime("%Y-%m-%d %H:%M:%S")

        nft_data = NFTData(
            blockchain_id=metadata.blockchain_id,
            blockchain_name=blockchain_name,
            collection_id=f"bc-{blockchain_name}-{metadata.program_account_key}",
            collection_name=collection_name,
            collection_name_slug=slugify.slugify(collection_name),
            market_id=metadata.market_id,
            token_key=metadata.token_key,
            owner=metadata.owner,
            token_id=f"bc-{blockchain_name}-{metadata.token_key}",
            token_name=metadata.name,
            token_name_slug=slugify.slugify(metadata.name),
            description=description,
            symbol=metadata.symbol,
            primary_sale_happened=metadata.primary_sale_happened,
            last_market_activity=metadata.last_market_activity,
            timestamp_of_market_activity=blocktime_formatted,
            event_timestamp=event_time_formatted,
            metadata_uri=metadata.uri,
            attributes=token_attributes,
            transaction_hash=metadata.transaction_hash,
            price=metadata.price,
            price_currency=base_curency_for_blockchain(metadata.blockchain_id),
            creators=token_creators,
            edition=str(-1),
            external_url=external_url,
            media_files=media_files,
        )

        return nft_data

    def _transform_token_attributes(self, attributes) -> Dict[str, str]:
        token_attributes = {
            str(attribute["trait_type"]).capitalize(): str(attribute["value"])
            for attribute in attributes
            if "trait_type" in attribute
        }
        return token_attributes
