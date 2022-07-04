import time
from typing import Optional

from src.config import settings
from src.exception import (
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
)
from src.model import SecondaryMarketEvent, Instruction, SolanaTransaction
from src.parser.signature import SignatureParser
from src.utils import open_sea_id


class OpenSeaParser(SignatureParser):

    sale = int.from_bytes(bytes.fromhex("254ad99d4f312306"), "little")
    listing = int.from_bytes(bytes.fromhex("33e685a4017f83ad"), "little")
    delisting = int.from_bytes(bytes.fromhex("c6c682cba35faf4b"), "little")
    bid = int.from_bytes(bytes.fromhex("66063d1201daebea"), "little")
    cancel_bidding = int.from_bytes(bytes.fromhex("ee4c24da84b1e0e9"), "little")

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.open_sea.program_account
        )

    def find_open_sea_instruction(
        self, transaction: SolanaTransaction
    ) -> Optional[Instruction]:
        instruction = transaction.find_instruction(
            self.program_account, offset=self.sale, width=8
        )

        if not instruction:
            instruction = transaction.find_instruction(
                self.program_account, offset=self.listing, width=8
            )
        if not instruction:
            instruction = transaction.find_instruction(
                self.program_account, offset=self.delisting, width=8
            )
        if not instruction:
            instruction = transaction.find_instruction(
                self.program_account, offset=self.bid, width=8
            )

        if not instruction:
            instruction = transaction.find_instruction(
                self.program_account, offset=self.cancel_bidding, width=8
            )

        if not instruction:
            instruction = transaction.find_instruction(self.program_account)

        return instruction

    def parse(self, transaction: SolanaTransaction) -> Optional[SecondaryMarketEvent]:
        instruction = self.find_open_sea_instruction(transaction)

        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        buyer, owner = "", ""
        price = 0
        token_key = ""
        offset = instruction.get_function_offset(8)

        if offset == self.sale:
            # Sale event on OpenSea is equal to ExecuteSale event.
            event_type = settings.blockchain.market.event.sale
            buyer = instruction.accounts[0]
            # Sale price in the smallest UNIT. E.g., for Solana this is lamports
            price = instruction.get_int(10, 5)
            # Token address / Mint key
            token_key = instruction.accounts[4]
        elif offset == self.listing:
            # Listing event on OpenSea has same offset as Sale event.
            event_type = settings.blockchain.market.event.listing
            owner = instruction.accounts[0]
            # Listing price in the smallest UNIT. E.g., for Solana this is lamports
            price = instruction.get_int(10, 5)
            # Token address / Mint key
            token_key = instruction.accounts[4]
        elif offset == self.delisting:
            # Delisting event on OpenSea is equal to CancelSell event.
            event_type = settings.blockchain.market.event.delisting
            owner = instruction.accounts[0]
            # Fixed price for delisting transactions
            price = 0
            # Token address / Mint key
            token_key = instruction.accounts[3]
        elif offset == self.bid:
            # Bid event on OpenSea is equal to Buy event.
            event_type = settings.blockchain.market.event.bid
            buyer = instruction.accounts[0]
            # Bid price in the smallest UNIT. E.g., for Solana this is lamports
            price = instruction.get_int(10, 5)
            # Iterate through the postBalance and find the entry with `amount` == 1
            post_token_balances = transaction.post_token_balances
            if post_token_balances:
                for balance in post_token_balances:
                    if balance["uiTokenAmount"]["amount"] == "1":
                        # Token address / Mint key
                        token_key = balance["mint"]
                        break
            else:
                token_key = instruction.accounts[2]
        elif offset == self.cancel_bidding:
            # Cancel bidding event on OpenSea is equal to CancelBuy event.
            event_type = settings.blockchain.market.event.cancel_bidding
            buyer = instruction.accounts[0]
            # Fixed price for cancel bidding transactions
            price = 0
            # Token address / Mint key
            token_key = instruction.accounts[2]
        else:
            event_type = settings.blockchain.market.event.unknown

        if event_type and token_key and (owner or buyer):
            event = SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=open_sea_id(),
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


class OpenSeaParserAuction(SignatureParser):
    bid = int.from_bytes(bytes.fromhex("66063d1201daebea"), "little")
    listing = int.from_bytes(bytes.fromhex("33e685a4017f83ad"), "little")

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.open_sea.auction_program_account
        )

    def find_open_sea_auction_instruction(
        self, transaction: SolanaTransaction
    ) -> Optional[Instruction]:
        instruction = transaction.find_instruction(
            self.program_account, offset=self.bid, width=8
        )

        if not instruction:
            instruction = transaction.find_instruction(self.program_account)

        return instruction

    def parse(self, transaction: SolanaTransaction) -> Optional[SecondaryMarketEvent]:
        instruction = self.find_open_sea_auction_instruction(transaction)

        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        buyer, owner = "", ""
        price = 0
        token_key = ""
        offset = instruction.get_function_offset(8)

        if offset == self.bid:
            # Bid event on OpenSea is equal to Buy event.
            event_type = settings.blockchain.market.event.bid
            buyer = instruction.accounts[0]
            # Bid price in the smallest UNIT. E.g., for Solana this is lamports
            price = instruction.get_int(10, 5)
            # Iterate through the postBalance and find the entry with `amount` == 1
            post_token_balances = transaction.post_token_balances
            if post_token_balances:
                for balance in post_token_balances:
                    if balance["uiTokenAmount"]["amount"] == "1":
                        # Token address / Mint key
                        token_key = balance["mint"]
                        break
            else:
                token_key = instruction.accounts[2]
        elif offset == self.listing:
            # Auction event on OpenSea has same offset as Sale event.
            event_type = settings.blockchain.market.event.sale_auction
            # Auction price in the smallest UNIT. E.g., for Solana this is lamports
            price = instruction.get_int(11, 5)
            # Iterate through the postBalance and find the entry with `amount` == 1
            post_token_balances = transaction.post_token_balances
            for balance in post_token_balances:
                if balance["uiTokenAmount"]["amount"] == "1":
                    buyer = balance["owner"]
                    # Token address / Mint key
                    token_key = balance["mint"]
                    break
        else:
            event_type = settings.blockchain.market.event.unknown

        if event_type and token_key and (owner or buyer):
            event = SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=open_sea_id(),
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
