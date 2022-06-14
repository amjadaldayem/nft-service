import time
from typing import Optional

from src.config import settings
from src.exception import (
    SecondaryMarketDataMissingException,
    TransactionInstructionMissingException,
    UnknownTransactionException,
)
from src.model import Instruction, SecondaryMarketEvent, Transaction
from src.parser.signature import SignatureParser
from src.utils import alpha_art_id


class AlphaArtParser(SignatureParser):
    def __init__(self):
        self.program_account = (
            settings.blockchain.solana.market.alpha_art.program_account
        )
        self.market_authority_address = (
            settings.blockchain.solana.market.alpha_art.address
        )

    def parse(self, transaction: Transaction) -> SecondaryMarketEvent:
        """
        Delisting event on AlphaArt is done by transferring the token back to the
        original owner, then closing the previous token account.
        Args:
            alpha_art_program_key:
            authority_address:
        Returns:
        """
        instruction = transaction.find_instruction(account_key=self.program_account)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        event = SecondaryMarketEvent(
            blockchain_id=int(settings.blockchain.address.solana, 0),
            market_id=alpha_art_id(),
            blocktime=transaction.block_time,
            timestamp=time.time_ns(),
            event_type=settings.blockchain.solana.market.event.sale,
            transaction_hash=transaction.signature,
        )
        # in the event of sale, the 8th account in the `matched_pi` is the
        # token key
        # TODO: Maybe use this to replace the final token address finding proc?
        # try:
        #     possible_token_key = matched_pi.account_list[7]
        # except:
        #     possible_token_key = None

        # If the inner instruction array contains Sys`transfer`s, this is a
        # sale;
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
                if self.is_token_transfer(inner_instruction):
                    if acc_price > 0:
                        # A sale event for sure, let's update the buyer info
                        # In the event of sale on Alpha Art, the accounts[1]
                        # on `instruction` is the buyer
                        token_account_to_match = inner_instruction.accounts[1]
                        event.buyer = instruction.accounts[0]
                        event.price = acc_price
                    else:
                        # Delisting event
                        # in the event of delisting for Alpha Art,
                        # accounts[0] on `instruction` the owner
                        event.event_type = (
                            settings.blockchain.solana.market.event.delisting
                        )
                        event.owner = instruction.accounts[0]
                elif self.is_set_new_authority(inner_instruction):
                    # If changing authority to AlphaArt address, otherwise it does
                    # not make any sense.
                    new_owner_key = inner_instruction.get_str(
                        3, length=None, b58encode=True
                    )
                    if new_owner_key == self.market_authority_address:
                        # Gets the listing price from the outer matche ParsedInstruction
                        lamports = instruction.get_int(1)
                        event.owner = inner_instruction.accounts[1]
                        event.event_type = (
                            settings.blockchain.solana.market.event.listing
                        )
                        event.price = lamports
                        token_account_to_match = inner_instruction.accounts[0]
                    else:
                        return None
        # Lastly, try to find the mint key (token address)
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

    def is_sale_event(self, inner_instruction) -> bool:
        return (
            inner_instruction.is_system_program_instruction
            and inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.system.transfer
        )

    def is_token_transfer(self, inner_instruction) -> bool:
        return (
            inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.token.transfer
        )

    def is_set_new_authority(self, inner_instruction) -> bool:
        return (
            inner_instruction.get_function_offset()
            == settings.blockchain.solana.internal.token.set_authority
            and inner_instruction.get_int(1, 1)
            == settings.blockchain.solana.internal.authority.account_owner
        )
