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
from src.utils import magic_eden_id


class MagicEdenParserV1(SignatureParser):

    BID_EVENT = 0x925C97C85B944DEE

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.magic_eden.program_account_v1
        )
        self.market_authority_address = "GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp"

    def parse(self, transaction: SolanaTransaction) -> SecondaryMarketEvent:
        # If the inner instruction array contains `transfer`s, this is a
        # sale; otherwise, if the length of the array is 2, it is a listing or
        # delisting

        instruction = transaction.find_instruction(account_key=self.program_account)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        offset = instruction.get_function_offset(8)

        event_type = settings.blockchain.market.event.sale
        if offset == self.BID_EVENT:
            # Let's not capture Bid events because it is not quite easy
            # now to figure out the token address
            raise UnknownTransactionException(
                "Bid event not supported by Magic Eden V1 parser."
            )

        event = SecondaryMarketEvent(
            blockchain_id=int(settings.blockchain.address.solana, 0),
            market_id=magic_eden_id(),
            blocktime=transaction.block_time,
            timestamp=time.time_ns(),
            event_type=event_type,
            transaction_hash=transaction.signature,
        )

        acc_price = 0
        token_account_to_match = None  # for finding token address.
        inner_instructions_group = transaction.find_inner_instructions(instruction)

        if not inner_instructions_group:
            raise TransactionInstructionMissingException(
                "Inner instruction group missing."
            )

        for inner_instruction in inner_instructions_group.instructions:
            if self.is_sale_event(inner_instruction):
                acc_price += inner_instruction.get_int(4, 8)
            elif inner_instruction.is_token_program_instruction:
                # Could be set new authority
                if self.is_set_new_authority(inner_instruction):
                    if acc_price > 0:
                        # A sale event for sure, let's update the buyer info
                        buyer_account = inner_instruction.get_str(
                            3, length=None, b58encode=True
                        )
                        event.buyer = buyer_account
                        event.price = acc_price
                    else:
                        # If changing authority to MagicEden address,
                        # it is a listing event otherwise it is an delisting one
                        new_owner_key = inner_instruction.get_str(
                            3, length=None, b58encode=True
                        )
                        if new_owner_key == self.market_authority_address:
                            # Gets the listing price from the outer matche ParsedInstruction
                            lamports = instruction.get_int(8, 8)
                            event.owner = inner_instruction.accounts[1]
                            event.event_type = (
                                settings.blockchain.market.event.listing
                            )
                            event.price = lamports

                            token_account_to_match = inner_instruction.accounts[0]
                        else:
                            event.event_type = (
                                settings.blockchain.market.event.delisting
                            )
                            event.owner = new_owner_key
                            token_account_to_match = inner_instruction.accounts[0]
        # Lastly, try find the mint key (token address)
        # Because usually the token has to be carried by a "Token Account",
        # which is a PDA from the Market Place Authority, so the balance change
        # will have to reflect on that account.
        event.token_key, _ = transaction.find_token_address_and_owner(
            token_account_to_match
        )
        if event.token_key:
            return event

        raise SecondaryMarketDataMissingException(
            f"Token key missing for transaction: {transaction.signature}."
        )

    @staticmethod
    def is_sale_event(inner_instruction):
        return (
            inner_instruction.is_system_program_instruction
            and inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.system.transfer
        )

    @staticmethod
    def is_set_new_authority(inner_instruction):
        return (
            inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.token.set_authority
            and inner_instruction.get_int(1, 1)
            == settings.blockchain.solana.internal.authority.account_owner
        )


class MagicEdenParserV2(SignatureParser):

    listing_event = 0xAD837F01A485E633
    delisting_event = 0x4BAF5FA3CB82C6C6
    bid_event = 0xEAEBDA01123D0666
    cancel_bidding_event = 0xE9E0B184DA244CEE
    sale_event = 0x623314F9DD94A25

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.magic_eden.program_account_v2
        )

    def find_magic_eden_v2_instruction(
        self, transaction: SolanaTransaction
    ) -> Optional[Instruction]:
        instruction = transaction.find_instruction(
            self.program_account, offset=self.sale_event, width=8
        )

        if not instruction:
            instruction = transaction.find_instruction(
                self.program_account, offset=self.cancel_bidding_event, width=8
            )

        if not instruction:
            instruction = transaction.find_instruction(self.program_account)

        return instruction

    def parse(self, transaction: SolanaTransaction):
        # So for sales event there could be variable number of
        # instructions that all match, we need to check and match to see if
        # any of the instruction matches.
        # There could be a case that a single event contains "bid" and "sale"
        # instructions both, in this case we categorize them as "sale".
        # The matching precedence will be sale comes before bid.

        instruction = self.find_magic_eden_v2_instruction(transaction)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        inner_instructions_group = transaction.find_inner_instructions(instruction)

        offset = instruction.get_function_offset(8)
        buyer, owner = "", ""
        price = 0
        token_key = ""
        event_type = None

        if offset == self.listing_event:
            owner = instruction.accounts[0]
            token_key = instruction.accounts[4]
            price = instruction.get_int(10, 8)
            event_type = settings.blockchain.market.event.listing
            # Try to find if there is any set authority inner instruction,
            # if so, it is a listing otherwise it is a price update
            if inner_instructions_group:
                for inner_instruction in inner_instructions_group.instructions:
                    if (
                        inner_instruction.is_token_program_instruction
                        and inner_instruction.get_function_offset()
                        == settings.blockchain.solana.internal.token.set_authority
                    ):
                        event_type = settings.blockchain.market.event.listing
                        break
        elif offset == self.delisting_event:
            owner = instruction.accounts[0]
            token_key = instruction.accounts[3]
            event_type = settings.blockchain.market.event.delisting
        elif offset == self.bid_event:
            buyer = instruction.accounts[0]
            price = instruction.get_int(10, 8)
            event_type = settings.blockchain.market.event.bid
            token_key = instruction.accounts[2]
        elif offset == self.sale_event:
            event_type = settings.blockchain.market.event.sale
            buyer = instruction.accounts[0]
            price = instruction.get_int(10, 8)
            token_key = instruction.accounts[4]
        elif offset == self.cancel_bidding_event:
            event_type = settings.blockchain.market.event.bidding
            buyer = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[2]

        if event_type and token_key and (owner or buyer):
            return SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=magic_eden_id(),
                blocktime=transaction.block_time,
                timestamp=time.time_ns(),
                event_type=event_type,
                transaction_hash=transaction.signature,
                owner=owner,
                buyer=buyer,
                price=price,
                token_key=token_key,
            )

        raise SecondaryMarketDataMissingException(
            f"Token key or event_type missing for transaction: {transaction.signature}."
        )


class MagicEdenAuctionParser(SignatureParser):

    # TODO: Later we should capture PlaceBid and PlaceBidv2
    #   Now only captures the settlements.
    magic_eden_auction_settle_v1 = 0xD466839057B92AAF
    magic_eden_auction_settle_v2 = 0x912751DB8DEE2905

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.magic_eden.auction_program_account
        )

    def find_magic_eden_auction_instruction(
        self, transaction: SolanaTransaction
    ) -> Optional[Instruction]:
        instruction = transaction.find_instruction(
            self.program_account, offset=self.magic_eden_auction_settle_v2, width=8
        )

        if not instruction:
            instruction = transaction.find_instruction(
                self.program_account, offset=self.magic_eden_auction_settle_v1, width=8
            )

        if not instruction:
            instruction = transaction.find_instruction(self.program_account)

        return instruction

    def parse(self, transaction: SolanaTransaction):
        instruction = self.find_magic_eden_auction_instruction(transaction)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        inner_instructions_group = transaction.find_inner_instructions(instruction)
        if not inner_instructions_group:
            raise TransactionInstructionMissingException(
                "Inner instruction group missing."
            )

        owner = ""
        buyer = instruction.accounts[0]
        event_type = settings.blockchain.market.event.sale_auction
        price = 0
        token_account = None
        for inner_instruction in inner_instructions_group.instructions:

            if self.is_token_transfer(inner_instruction):
                token_account = instruction.accounts[0]
            elif self.is_system_transfer(inner_instruction):
                if inner_instruction.accounts[0] != buyer:
                    # Exclude the tiny amount directly transferred from buyer
                    # for fee.
                    price += inner_instruction.get_int(4, 8)

        token_key, _ = transaction.find_token_address_and_owner(token_account)

        if token_key and (owner or buyer):
            return SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=magic_eden_id(),
                blocktime=transaction.block_time,
                timestamp=time.time_ns(),
                event_type=event_type,
                transaction_hash=transaction.signature,
                owner=owner,
                buyer=buyer,
                price=price,
                token_key=token_key,
            )

        raise SecondaryMarketDataMissingException(
            f"Token key or event_type missing for transaction: {transaction.signature}."
        )

    def is_token_transfer(self, inner_instruction) -> bool:
        return (
            inner_instruction.is_token_program_instruction
            and inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.token.transfer
        )

    def is_system_transfer(self, inner_instruction) -> bool:
        return (
            inner_instruction.is_system_program_instruction
            and inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.system.transfer
        )
