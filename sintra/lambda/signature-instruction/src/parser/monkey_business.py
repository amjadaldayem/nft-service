import time
from typing import Optional

from ..config import settings
from ..exception import TransactionInstructionMissingException
from ..model import SecondaryMarketEvent, SolanaTransaction
from ..utils import monkey_business_id
from .signature import SignatureParser


class MonkeyBusinessParser(SignatureParser):
    sale = int.from_bytes(bytes.fromhex("95e23468068ee627"), "little")
    listing = int.from_bytes(bytes.fromhex("856e4aaf709ff59f"), "little")
    delisting = int.from_bytes(bytes.fromhex("5f81edf00831df84"), "little")

    def __init__(self) -> None:
        self.program_account = None

    def parse(self, transaction: SolanaTransaction) -> Optional[SecondaryMarketEvent]:
        instruction = transaction.find_instruction(
            account_key=self.program_account, offset=self.sale, width=8
        )
        if not instruction:
            instruction = transaction.find_instruction(
                account_key=self.program_account, offset=self.listing, width=8
            )
        if not instruction:
            instruction = transaction.find_instruction(
                account_key=self.program_account, offset=self.delisting, width=8
            )
        if not instruction:
            instruction = transaction.find_instruction(
                account_key=self.program_account,
            )
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
            price = instruction.get_int(8, 5)
            token_key = instruction.accounts[1]
        elif offset == self.listing:
            event_type = settings.blockchain.market.event.listing
            owner = instruction.accounts[0]
            price = instruction.get_int(16, 6)
            token_key = instruction.accounts[1]
        elif offset == self.delisting:
            # Delisting event on SMB is done by transferring the token back to the
            # original owner, then closing the previous token account.
            event_type = settings.blockchain.market.event.delisting
            owner = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[1]
        else:
            event_type = settings.blockchain.market.event.unknown

        event = SecondaryMarketEvent(
            blockchain_id=int(settings.blockchain.address.solana, 0),
            market_id=monkey_business_id(),
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


class MonkeyBusinessParserV1(MonkeyBusinessParser):
    def __init__(self) -> None:
        super().__init__()
        self.program_account = (
            settings.blockchain.solana.market.monkey_business.program_account_v1
        )


class MonkeyBusinessParserV2(MonkeyBusinessParser):
    def __init__(self) -> None:
        super().__init__()
        self.program_account = (
            settings.blockchain.solana.market.monkey_business.program_account_v2
        )


class MonkeyBusinessParserV3(MonkeyBusinessParser):
    def __init__(self) -> None:
        super().__init__()
        self.program_account = (
            settings.blockchain.solana.market.monkey_business.program_account_v3
        )
