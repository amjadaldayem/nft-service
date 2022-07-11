# pylint: disable=too-many-return-statements

import struct
import time
import os

import base58
from solana.rpc.api import MemcmpOpt
from src.config import settings
from src.exception import DecodingException
from src.model import NFTMetadata
import logging
import requests


logger = logging.getLogger(__file__)
alchemy_api_key = os.getenv("ALCHEMY_API_KEY")


def transaction_event_type(event_type: int) -> str:
    if event_type == settings.blockchain.market.event.listing:
        return "Listing"

    if event_type == settings.blockchain.market.event.delisting:
        return "Delisting"

    if event_type == settings.blockchain.market.event.sale:
        return "Sale"

    if event_type == settings.blockchain.market.event.update:
        return "Price update"

    if event_type == settings.blockchain.market.event.bid:
        return "Bid"

    if event_type == settings.blockchain.market.event.sale_auction:
        return "Sale auction"

    if event_type == settings.blockchain.market.event.bidding:
        return "Bidding"

    return None


class MetadataUnpacker:
    def memcmp_opts_update_authority_filters(self, update_authority):
        return {
            "memcmp_opts": [
                MemcmpOpt(offset=1, bytes=update_authority),
            ]
        }

    def memcmp_opts_candy_machine_filters(self, candy_machine_public_key):
        return {
            "memcmp_opts": [
                MemcmpOpt(offset=326, bytes=candy_machine_public_key),
            ]
        }

    def memcmp_opts_token_accounts_filters(self, mint):
        """
        Finds all token accounts for a specific mint.
        https://spl.solana.com/token#finding-all-token-accounts-for-a-specific-mint

        """
        return {
            "data_size": 165,
            "memcmp_opts": [
                MemcmpOpt(offset=0, bytes=mint),
            ],
        }

    def solana_metadata_unpack(self, data) -> NFTMetadata:
        if data[0] != 4:
            raise DecodingException("Can't decode NFT metadata.")
        i = 1
        source_account = base58.b58encode(
            bytes(struct.unpack("<" + "B" * 32, data[i : i + 32]))
        )
        i += 32
        mint_account = base58.b58encode(
            bytes(struct.unpack("<" + "B" * 32, data[i : i + 32]))
        )
        i += 32
        name_len = struct.unpack("<I", data[i : i + 4])[0]
        i += 4
        name = struct.unpack("<" + "B" * name_len, data[i : i + name_len])
        i += name_len
        symbol_len = struct.unpack("<I", data[i : i + 4])[0]
        i += 4
        symbol = struct.unpack("<" + "B" * symbol_len, data[i : i + symbol_len])
        i += symbol_len
        uri_len = struct.unpack("<I", data[i : i + 4])[0]
        i += 4
        uri = struct.unpack("<" + "B" * uri_len, data[i : i + uri_len])
        i += uri_len
        fee = struct.unpack("<h", data[i : i + 2])[0]
        i += 2
        has_creator = data[i]
        i += 1
        creators = []
        verified = []
        share = []
        if has_creator:
            creator_len = struct.unpack("<I", data[i : i + 4])[0]
            i += 4
            for _ in range(creator_len):
                creator = base58.b58encode(
                    bytes(struct.unpack("<" + "B" * 32, data[i : i + 32]))
                )
                creators.append(bytes(creator).decode("utf-8"))
                i += 32
                verified.append(data[i])
                i += 1
                share.append(data[i])
                i += 1
        primary_sale_happened = bool(data[i])
        i += 1
        is_mutable = bool(data[i])
        metadata = NFTMetadata(
            program_account_key=bytes(source_account).decode("utf-8"),
            token_key=bytes(mint_account).decode("utf-8"),
            primary_sale_happened=primary_sale_happened,
            timestamp=time.time_ns(),
            is_mutable=is_mutable,
            name=bytes(name).decode("utf-8").strip("\x00"),
            symbol=bytes(symbol).decode("utf-8").strip("\x00"),
            uri=bytes(uri).decode("utf-8").strip("\x00"),
            seller_fee_basis_points=fee,
            creators=creators,
            verified=verified,
            share=share,
        )
        return metadata

    def ethereum_metadata_unpack(self, data) -> NFTMetadata:
        name = data["metadata"]["name"]
        uri = data["tokenUri"]["raw"]
        contract_address = data["contract"]["address"]
        token_id = data["id"]["tokenId"]
        token_key = f"{contract_address}/{token_id}"

        metadata = NFTMetadata(
            name=name,
            uri=uri,
            timestamp=time.time_ns(),
            token_key=token_key,
        )
        return metadata


def solana_address() -> int:
    return int(settings.blockchain.address.solana, 0)


def ethereum_address() -> int:
    return int(settings.blockchain.address.ethereum, 0)
