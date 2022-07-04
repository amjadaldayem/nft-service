import time
from typing import Optional

from src.config import settings
from src.exception import (
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
)
from src.model import SecondaryMarketEvent, SolanaTransaction
from src.parser.signature import SignatureParser
from src.utils import exchange_art_id


class ExchangeArtParserV1(SignatureParser):
    sale = int.from_bytes(bytes.fromhex("01"), "little")
    listing = int.from_bytes(bytes.fromhex("00"), "little")
    delisting = int.from_bytes(bytes.fromhex("02"), "little")
    bid = int.from_bytes(bytes.fromhex("d66261233b0c2cb2"), "little")
    cancel_bidding = int.from_bytes(bytes.fromhex("5ccbdf285c593577"), "little")

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.exchange_art.program_account_v1
        )

    def parse(self, transaction: SolanaTransaction) -> Optional[SecondaryMarketEvent]:
        instruction = transaction.find_instruction(account_key=self.program_account)
        inner_instructions = transaction.find_inner_instructions(instruction)

        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        buyer, owner = "", ""
        price = 0
        token_key = ""
        offset = instruction.get_function_offset()

        if offset == self.sale:
            event_type = settings.blockchain.market.event.sale
            buyer = instruction.accounts[0]
            token_key = instruction.accounts[6]
            accumulated_price = 0
            for inner_instruction in inner_instructions.instructions:
                if (
                    inner_instruction.is_system_program_instruction
                    and inner_instruction.get_function_offset()
                    == settings.blockchain.solana.internal.system.transfer
                ):
                    accumulated_price += inner_instruction.get_int(4, 8)
            price = int(round(accumulated_price, 3))
        elif offset == self.listing:
            event_type = settings.blockchain.market.event.listing
            owner = instruction.accounts[0]
            price = instruction.get_int(1, 6)
            token_key = instruction.accounts[2]
        elif offset == self.delisting:
            event_type = settings.blockchain.market.event.delisting
            owner = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[6]
        elif offset == self.bid:
            event_type = settings.blockchain.market.event.bid
            buyer = instruction.accounts[0]
            price = instruction.get_int(8, 5)
            token_key = instruction.accounts[1]
        elif offset == self.cancel_bidding:
            event_type = settings.blockchain.market.event.cancel_bidding
            buyer = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[1]
        else:
            event_type = settings.blockchain.market.event.unknown

        if event_type and token_key and (owner or buyer):
            event = SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=exchange_art_id(),
                blocktime=transaction.block_time,
                timestamp=time.time_ns(),
                event_type=event_type,
                transaction_hash=transaction.signature,
                price=price,
                buyer=buyer,
                owner=owner,
                token_key=token_key,
            )
            return event

        raise SecondaryMarketDataMissingException(
            f"Token key missing for transaction: {transaction.signature}."
        )


class ExchangeArtParserV2(SignatureParser):
    sale = int.from_bytes(bytes.fromhex("01"), "little")
    listing = int.from_bytes(bytes.fromhex("00"), "little")
    delisting = int.from_bytes(bytes.fromhex("02"), "little")
    bid = int.from_bytes(bytes.fromhex("d66261233b0c2cb2"), "little")
    cancel_bidding = int.from_bytes(bytes.fromhex("5ccbdf285c593577"), "little")

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.exchange_art.program_account_v2
        )

    def parse(self, transaction: SolanaTransaction) -> Optional[SecondaryMarketEvent]:
        instruction = transaction.find_instruction(account_key=self.program_account)
        inner_instructions = transaction.find_inner_instructions(instruction)

        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        buyer, owner = "", ""
        price = 0
        token_key = ""
        offset = instruction.get_function_offset(8)

        if offset == self.sale:
            event_type = settings.blockchain.market.event.sale
            buyer = instruction.accounts[0]
            token_key = instruction.accounts[6]
            accumulated_price = 0
            for inner_instruction in inner_instructions.instructions:
                if (
                    inner_instruction.is_system_program_instruction
                    and inner_instruction.get_function_offset()
                    == settings.blockchain.solana.internal.system.transfer
                ):
                    accumulated_price += inner_instruction.get_int(4, 8)
            price = int(round(accumulated_price, 3))
        elif offset == self.listing:
            event_type = settings.blockchain.market.event.listing
            owner = instruction.accounts[0]
            price = instruction.get_int(1, 6)
            token_key = instruction.accounts[2]
        elif offset == self.delisting:
            event_type = settings.blockchain.market.event.delisting
            owner = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[6]
        elif offset == self.bid:
            event_type = settings.blockchain.market.event.bid
            buyer = instruction.accounts[0]
            price = instruction.get_int(8, 5)
            token_key = instruction.accounts[1]
        elif offset == self.cancel_bidding:
            event_type = settings.blockchain.market.event.cancel_bidding
            buyer = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[1]
        else:
            event_type = settings.blockchain.market.event.unknown

        if event_type and token_key and (owner or buyer):
            event = SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=exchange_art_id(),
                blocktime=transaction.block_time,
                timestamp=time.time_ns(),
                event_type=event_type,
                transaction_hash=transaction.signature,
                price=price,
                buyer=buyer,
                owner=owner,
                token_key=token_key,
            )
            return event

        raise SecondaryMarketDataMissingException(
            f"Token key missing for transaction: {transaction.signature}."
        )


class ExchangeArtParserAuction(SignatureParser):
    sale = int.from_bytes(bytes.fromhex("01"), "little")
    listing = int.from_bytes(bytes.fromhex("00"), "little")
    delisting = int.from_bytes(bytes.fromhex("02"), "little")
    bid = int.from_bytes(bytes.fromhex("d66261233b0c2cb2"), "little")
    cancel_bidding = int.from_bytes(bytes.fromhex("5ccbdf285c593577"), "little")

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.exchange_art.auction_program_account
        )

    def parse(self, transaction: SolanaTransaction) -> Optional[SecondaryMarketEvent]:
        instruction = transaction.find_instruction(account_key=self.program_account)

        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        buyer, owner = "", ""
        price = 0
        token_key = ""
        offset = instruction.get_function_offset()

        if offset == self.sale:
            event_type = settings.blockchain.market.event.sale
            buyer = instruction.accounts[0]
            price = instruction.get_int(1, 6)
            token_key = instruction.accounts[1]
        elif offset == self.listing:
            event_type = settings.blockchain.market.event.listing
            owner = instruction.accounts[0]
            price = instruction.get_int(1, 6)
            token_key = instruction.accounts[2]
        elif offset == self.delisting:
            event_type = settings.blockchain.market.event.delisting
            owner = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[6]
        elif offset == self.bid:
            event_type = settings.blockchain.market.event.bid
            buyer = instruction.accounts[0]
            price = instruction.get_int(8, 5)
            token_key = instruction.accounts[1]
        elif offset == self.cancel_bidding:
            event_type = settings.blockchain.market.event.cancel_bidding
            buyer = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[1]
        else:
            event_type = settings.blockchain.market.event.unknown

        if event_type and token_key and (owner or buyer):
            event = SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=exchange_art_id(),
                blocktime=transaction.block_time,
                timestamp=time.time_ns(),
                event_type=event_type,
                transaction_hash=transaction.signature,
                price=price,
                buyer=buyer,
                owner=owner,
                token_key=token_key,
            )
            return event

        raise SecondaryMarketDataMissingException(
            f"Token key missing for transaction: {transaction.signature}."
        )
