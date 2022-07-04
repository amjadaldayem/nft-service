import time
from typing import Optional

from src.config import settings
from src.exception import (
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
    UnknownTransactionException,
)
from src.model import Instruction, SecondaryMarketEvent, SolanaTransaction
from src.parser.signature import SignatureParser
from src.utils import solanart_id


class SolanartParser(SignatureParser):

    create_auction_event = 0x00
    auction_bid_event = 0x01
    close_auction_event = 0x02
    cancel_bidding_event = 0x03
    listing_event = 0x04
    sale_delisting_event = 0x05
    price_update_event = 0x06

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.solanart.program_account
        )

    def parse(self, transaction: SolanaTransaction):
        """
        Solnart Program:
         - u8: instruction offset
            0x00 - create auction
            0x01 - auction bid
            0x02 - close auction
            0x03 - cancel bidding
            0x04 - Listing
                - u64: listing price
            0x05 - Sale/delisting:
                - u64: sales price. If 0, it is delisting
            0x06 - Price update
                - u64: updated price
         - u64:
        Args:
            solanart_program_key:
            authority_address:
        Returns:
        """

        instruction = transaction.find_instruction(account_key=self.program_account)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        inner_instructions_group = transaction.find_inner_instructions(instruction)

        # For Solanart, Buy now will contain only 1 instruction matching the program
        # But there is another "winning" an auction, where there will be 2 instructions
        # and the first one is similar to Buy, while the 2nd one is Close Auction
        buyer, owner = "", ""
        token_key = ""
        price = instruction.get_int(1)
        offset = instruction.get_function_offset()

        if offset == self.create_auction_event or offset == self.auction_bid_event:
            # 0x00 for creating auction (first bid)
            # 0x01 for next biddings
            buyer = instruction.accounts[0]
            token_key = instruction.accounts[3]
            event_type = settings.blockchain.market.event.bid
        elif offset == self.cancel_bidding_event:
            # Cancel Bidding
            event_type = settings.blockchain.market.event.cancel_bidding
            # Who cancelled it
            buyer = instruction.accounts[0]
            token_key = instruction.accounts[3]
        elif offset == self.listing_event:
            # Listing
            event_type = settings.blockchain.market.event.listing
            owner = instruction.accounts[0]
            token_key = instruction.accounts[4]
        elif offset == self.sale_delisting_event:
            # For Solanart, Auction Buy is done through 2 steps.
            # The actual data is carried in the second step: Close Auction
            # Delisting is the same offset as buy, only that the buyer (0) and seller (4)
            # are the same one.
            buyer = instruction.accounts[0]
            seller = instruction.accounts[3]

            # Close Auction!
            close_auction_instruction = transaction.find_instruction(
                account_key=self.program_account, offset=self.close_auction_event
            )

            close_auction_inner_instructions_group = (
                transaction.find_inner_instructions(instruction)
            )

            if buyer == seller and not close_auction_instruction:
                # De-listing
                event_type = settings.blockchain.market.event.delisting
                price = 0
                # Figure out the token key from the Token Transfer inner ins
                inner_instruction = inner_instructions_group.instructions[0]
                if inner_instruction:
                    token_key, _ = transaction.find_token_address_and_owner(
                        inner_instruction.accounts[1]
                    )
                    owner = instruction.accounts[0]
                    buyer = ""
            else:
                if close_auction_instruction:
                    # Auction Buy, price is from the 2nd instruction
                    event_type = settings.blockchain.market.event.sale_auction
                    price = close_auction_instruction.get_int(1)
                    for (
                        close_auction_inner_instruction
                    ) in close_auction_inner_instructions_group.instructions:
                        if self.is_cancel_bidding_event(
                            close_auction_inner_instruction
                        ):
                            # Tries to find the token address from the eventual owner
                            token_key, buyer = transaction.find_token_address_and_owner(
                                close_auction_instruction.accounts[2]
                            )
                            break
                else:
                    event_type = settings.blockchain.market.event.sale
                    buyer = instruction.accounts[0]
                    token_key = instruction.accounts[3]
                    for inner_instruction in inner_instructions_group.instructions:
                        if self.is_cancel_bidding_event(inner_instruction):
                            # Tries to find the token address from the eventual owner
                            token_key, _ = transaction.find_token_address_and_owner(
                                inner_instruction.accounts[1]
                            )
                            break
        elif offset == self.price_update_event:
            event_type = settings.blockchain.market.event.price_update
            owner = instruction.accounts[0]
            token_key = instruction.accounts[2]
            price = instruction.get_int(1)
        else:
            event_type = settings.blockchain.market.event.unknown

        if token_key and (owner or buyer):
            return SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=solanart_id(),
                blocktime=transaction.block_time,
                timestamp=time.time_ns(),
                event_type=event_type,
                price=price,
                owner=owner,
                buyer=buyer,
                transaction_hash=transaction.signature,
                token_key=token_key,
            )

        raise SecondaryMarketDataMissingException(
            f"Token key or event_type missing for transaction: {transaction.signature}."
        )

    def is_cancel_bidding_event(self, inner_instruction) -> bool:
        return (
            inner_instruction.is_token_program_instruction
            and inner_instruction.get_function_offset() == self.cancel_bidding_event
        )
