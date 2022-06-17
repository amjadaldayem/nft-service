import time

from ..config import settings
from ..exception import TransactionInstructionMissingException
from ..model import SecondaryMarketEvent, Transaction
from ..utils import solsea_id
from .signature import SignatureParser


class SolseaParser(SignatureParser):

    listing_event = 0x00
    delisting_event = 0x01
    sale_event = 0x02

    def __init__(self):
        self.program_account = settings.blockchain.solana.market.solsea.program_account
        self.market_authority_address = settings.blockchain.solana.market.solsea.address

    def parse(self, transaction: Transaction) -> SecondaryMarketEvent:
        instruction = transaction.find_instruction(account_key=self.program_account)
        if not instruction:
            raise TransactionInstructionMissingException(
                f"No instruction for this program account: {self.program_account}."
            )

        offset = instruction.get_function_offset(1)

        inner_instructions_group = transaction.find_inner_instructions(instruction)

        if not inner_instructions_group:
            raise TransactionInstructionMissingException(
                "Inner instruction group missing."
            )

        buyer, owner = "", ""
        price = 0
        token_key = ""
        event_type = None

        if offset == self.listing_event:
            event_type = settings.blockchain.solana.market.event.listing
            price = instruction.get_int(1, 8)
            token_key = instruction.accounts[2]
            token_offset = settings.blockchain.solana.internal.token.transfer
            for inner_instruction in inner_instructions_group.instructions:
                if (
                    inner_instruction.is_token_program_instruction
                    and inner_instruction.get_function_offset()
                ) == token_offset:
                    owner = inner_instruction.accounts[2]
                    break
        elif offset == self.delisting_event:
            event_type = settings.blockchain.solana.market.event.delisting
            post_token_balances = transaction.post_token_balances
            for balance in post_token_balances:
                if balance["uiTokenAmount"]["amount"] == "1":
                    owner = balance["owner"]
                    token_key = balance["mint"]
                    break
        elif offset == self.sale_event:
            event_type = settings.blockchain.solana.market.event.sale
            sys_transfer_offset = settings.blockchain.solana.internal.system.transfer
            for inner_instruction in inner_instructions_group.instructions:
                if (
                    inner_instruction.is_system_program_instruction
                    and inner_instruction.get_function_offset()
                ) == sys_transfer_offset:
                    price += inner_instruction.get_int(4, 8)
                    if not buyer:
                        buyer = inner_instruction.accounts[0]
            price = round(price, 3)
            token_key, _ = transaction.find_token_address_and_owner(buyer)
        else:
            event_type = settings.blockchain.solana.market.unknown

        return SecondaryMarketEvent(
            blockchain_id=int(settings.blockchain.address.solana, 0),
            market_id=solsea_id(),
            blocktime=transaction.block_time,
            timestamp=time.time_ns(),
            event_type=event_type,
            transaction_hash=transaction.signature,
            owner=owner,
            buyer=buyer,
            price=price,
            token_key=token_key,
        )
