import logging
import os
import time
from typing import Optional

from src.config import settings
from src.exception import SecondaryMarketDataMissingException
from src.model import EthereumTransaction, SecondaryMarketEvent
from src.parser.signature import SignatureParser
from src.utils import ethereum_open_sea_id
from web3 import Web3

logger = logging.getLogger(__name__)


class EthereumOpenSeaParser(SignatureParser):
    # List transaction MethodID: 0x75c1631d (Function: listToken)
    listing = 0x75C1631D
    # Delisting transaction MethodID: 0xbed659bc (Function: delistToken)
    delisting = 0xBED659BC
    # Sale transaction MethodID: 0xab834bab (Function: atomicMatch)
    sale = 0xAB834BAB

    def __init__(self):
        api_key = os.getenv("ALCHEMY_API_KEY")
        self.http_provider = Web3.HTTPProvider(
            f"{settings.blockchain.ethereum.http.endpoint}/{api_key}"
        )
        self.w3 = Web3(self.http_provider)
        self.program_account = None

    def parse(self, transaction: EthereumTransaction) -> Optional[SecondaryMarketEvent]:
        buyer, owner = "", ""
        transaction_hash = transaction.signature.hex()
        block_number = transaction.block_number
        block_time = self.w3.eth.get_block(block_number)["timestamp"]
        contract_address = transaction.logs[0]["address"]
        token_id = int(transaction.logs[0]["topics"][-1].hex(), 16)
        offset = transaction.offset_input[:10]
        # {contract_address}/{token_id}
        token_key = f"{contract_address}/{token_id}"
        if int(offset, 16) == self.sale:
            event_type = settings.blockchain.market.event.sale
            buyer = transaction.receipt_from
            # Sale price in the smallest UNIT. E.g., for Ethereum this is weis
            price = transaction.value
        elif int(offset, 16) == self.listing:
            event_type = settings.blockchain.market.event.listing
            owner = transaction.receipt_from
            # Listing price in the smallest UNIT. E.g., for Ethereum this is weis
            price = int(transaction.logs[0]["data"], 0)
        elif int(offset, 16) == self.delisting:
            event_type = settings.blockchain.market.event.delisting
            owner = transaction.receipt_from
            # Fixed delisting price in the smallest UNIT. E.g., for Ethereum this is weis
            price = 0
        else:
            event_type = settings.blockchain.market.event.unknown

        if event_type and token_key and (owner or buyer):
            event = SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.ethereum, 0),
                market_id=ethereum_open_sea_id(),
                blocktime=block_time,
                timestamp=time.time_ns(),
                event_type=event_type,
                transaction_hash=transaction_hash,
                price=price,
                buyer=buyer,
                owner=owner,
                token_key=token_key,
            )
            return event

        raise SecondaryMarketDataMissingException(
            f"Token key missing for transaction: {transaction_hash}."
        )


class EthereumOpenSeaParserV1(EthereumOpenSeaParser):
    def __init__(self):
        super().__init__()
        self.program_account = (
            settings.blockchain.ethereum.market.open_sea.program_account_v1
        )


class EthereumOpenSeaParserV2(EthereumOpenSeaParser):
    def __init__(self):
        super().__init__()
        self.program_account = (
            settings.blockchain.ethereum.market.open_sea.program_account_v2
        )
