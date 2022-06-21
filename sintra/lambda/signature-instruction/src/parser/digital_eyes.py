import time

from src.config import settings
from src.exception import (
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
)
from src.model import SecondaryMarketEvent, Transaction
from src.parser.signature import SignatureParser
from src.utils import digital_eyes_id


class DigitalEyesParserV1(SignatureParser):

    listing_event = 0x00
    escrow_exchange_event = 0x01

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.digital_eyes.program_account_v1
        )

    def parse(self, transaction: Transaction):
        """
        DigitalEyes has two program account: Direct Sale and NFT marketplace. This one is NFT marketplace.
        Args:
            digital_eyes_program_key:
            authority_address:
        Returns:
        """

        instruction = transaction.find_instruction(account_key=self.program_account)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        inner_instructions_group = transaction.find_inner_instructions(instruction)

        token_key = None
        buyer, owner = "", ""  # Not use this as default value instead of None
        price = 0
        offset = instruction.get_function_offset(1)

        if offset == self.listing_event:
            event_type = settings.blockchain.solana.market.event.listing
            owner = instruction.accounts[0]
            token_key = instruction.accounts[2]
            price = instruction.get_int(1)
        elif offset == self.escrow_exchange_event:
            # This is an Escrow exchange event, can be delisting or
            # sale, if there is any SOL transfer, then this is a sale
            # otherwise it is delisting
            token_key = instruction.accounts[6]
            # Add up all SOL transfers, and round up to 4th digit after the dot
            accumulated_price = 0
            has_sol_transfer = False
            for inner_instruction in inner_instructions_group.instructions:
                if self.is_system_transfer(inner_instruction):
                    has_sol_transfer = True
                    accumulated_price += inner_instruction.get_int(4, 8)

            price = int(round(accumulated_price, 3))

            if has_sol_transfer:
                event_type = settings.blockchain.solana.market.event.sale
                buyer = instruction.accounts[0]
            else:
                event_type = settings.blockchain.solana.market.event.delisting
                owner = instruction.accounts[0]
        else:
            event_type = settings.blockchain.solana.market.event.unknown

        if event_type and token_key and (owner or buyer):
            return SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=digital_eyes_id(),
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

    def is_system_transfer(self, inner_instruction) -> bool:
        return (
            inner_instruction.is_system_program_instruction
            and inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.system.transfer
        )


class DigitalEyesParserV2(SignatureParser):

    # Implict digital_eyes_program_key == DIGITAL_EYES_DIRECT_SALE_PROGRAM_ACCOUNT
    # For listing/ulisting event, the account[2] is the mint key
    # For price_update event, the account[1] is the mint key
    direct_sale_listing_func_offset = 0xAD837F01A485E633
    direct_sale_price_update_func_offset = 0x19977CE0408FBD00
    direct_sale_delisting_func_offset = 0xBEDCECDB29DFDBE8
    direct_sale_sale_func_offset = 0xEAEBDA01123D0666
    direct_sale_delisting_with_authority = 0x102AEE56CE64B81E

    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.digital_eyes.program_account_v2
        )

    def parse(self, transaction: Transaction):
        """
        DigitalEyes has two program account: Direct Sale and NFT marketplace. This one is Direct Sale.
        Args:
            digital_eyes_program_key:
            authority_address:
        Returns:
        """

        instruction = transaction.find_instruction(account_key=self.program_account)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        token_key = None
        buyer, owner = "", ""  # Not use this as default value instead of None
        price = 0
        offset = instruction.get_function_offset(8)

        if offset == self.direct_sale_listing_func_offset:
            # if the lasts 2bytes == feff, then the price is not visible
            # it will display as "contact owner"
            event_type = settings.blockchain.solana.market.event.listing
            token_key = instruction.accounts[2]
            owner = instruction.accounts[0]
            price = instruction.get_int(8, 8)
        elif offset == self.direct_sale_price_update_func_offset:
            event_type = settings.blockchain.solana.market.event.price_update
            token_key = instruction.accounts[1]
            price = instruction.get_int(8, 8)
            owner = instruction.accounts[0]
        elif offset == self.direct_sale_delisting_func_offset:
            event_type = settings.blockchain.solana.market.event.delisting
            token_key = instruction.accounts[2]
            owner = instruction.accounts[0]
        elif offset == self.direct_sale_sale_func_offset:
            event_type = settings.blockchain.solana.market.event.sale
            token_key = instruction.accounts[4]
            buyer = instruction.accounts[0]
            price = instruction.get_int(8, 8)
        elif offset == self.direct_sale_delisting_with_authority:
            event_type = settings.blockchain.solana.market.event.delisting
            token_key = instruction.accounts[2]
            owner = instruction.accounts[1]
            price = instruction.get_int(8, 8)
        else:
            event_type = settings.blockchain.solana.market.event.unknown

        if token_key and (owner or buyer):
            return SecondaryMarketEvent(
                blockchain_id=int(settings.blockchain.address.solana, 0),
                market_id=digital_eyes_id(),
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
