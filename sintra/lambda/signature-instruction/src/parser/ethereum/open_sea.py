import time
from typing import Optional

from src.config import settings
from src.exception import (
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
)
from src.model import SecondaryMarketEvent, EthereumTransaction
from src.parser.signature import SignatureParser
from src.utils import ethereum_open_sea_id
from web3 import Web3
import logging
from sintra.config import settings
import os

alchemy_api_key = os.getenv("ALCHEMY_API_KEY")


logger = logging.getLogger(__name__)


class EthereumOpenSeaParser(SignatureParser):
    # List transaction MethodID: 0x75c1631d (Function: listToken)
    listing = 0x75C1631D
    # Delisting transaction MethodID: 0xbed659bc (Function: delistToken)
    delisting = 0xBED659BC
    # Sale transaction MethodID: 0xab834bab (Function: atomicMatch)
    sale = 0xAB834BAB

    def __init__(self):
        try:
            self.http_provider = Web3.HTTPProvider(
                f"{settings.blockchain.ethereum.http.endpoint}/{alchemy_api_key}"
            )
            self.w3 = Web3(self.http_provider)
        except Exception as error:
            logger.error(
                f"Error: {error} occurred while connecting to Alchemy HTTP provider."
            )
        else:
            logger.info(
                "A connection was successfully established with Alchemy HTTP provider."
            )

    def parse(self, transaction: EthereumTransaction) -> Optional[SecondaryMarketEvent]:
        buyer, owner = "", ""
        transaction_hash = transaction.signature.hex()
        block_number = transaction.block_number
        block_time = self.w3.eth.getBlock(block_number)["timestamp"]
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
