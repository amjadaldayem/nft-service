from typing import Optional
from sintra.lambdas.shared.secondary_market_event import SecondaryMarketEvent
from sintra.lambdas.solana.constants import SECONDARY_MARKET_EVENT_SALE, SYS_TRANSFER, TOKEN_SET_AUTHORITY, \
    TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER, SECONDARY_MARKET_EVENT_LISTING, SECONDARY_MARKET_EVENT_DELISTING, \
    SECONDARY_MARKET_EVENT_PRICE_UPDATE, SECONDARY_MARKET_EVENT_BID, SECONDARY_MARKET_EVENT_CANCEL_BIDDING
from sintra.lambdas.solana.transaction import Transaction, Instruction
from sintra.lambdas.solana.market_ids import MarketplaceAccounts
from sintra.lambdas.solana.parsers.parser import TransactionParserInterface
from sintra.lambdas.solana.constants import BLOCKCHAIN_SOLANA
from sintra.lambdas.solana.constants import SOLANA_MAGIC_EDEN


class MagicEdenParserV1(TransactionParserInterface):

    bid_event = 0x925c97c85b944dee

    def __init__(self):
        self.type = MarketplaceAccounts.MAGIC_EDEN_PROGRAM_ACCOUNT_V1
        self.market_authority_address = "GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp"

    def parse(self, transaction: Transaction) -> Optional[SecondaryMarketEvent]:
        # If the inner instruction array contains `transfer`s, this is a
        # sale; otherwise, if the length of the array is 2, it is a listing or
        # delisting

        instruction = transaction.find_instruction(account_key=self.type.value[0])
        if not instruction:
            return None

        offset = instruction.get_function_offset(8)

        event_type = SECONDARY_MARKET_EVENT_SALE  # Default value
        if offset == self.bid_event:
            # Let's not capture Bid events because it is not quite easy
            # now to figure out the token address
            return None

        event = SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_MAGIC_EDEN,
            timestamp=transaction.block_time,
            event_type=event_type,
            transaction_hash=transaction.signature
        )

        acc_price = 0
        token_account_to_match = None  # for finding token address.
        inner_instructions_group = transaction.find_inner_instructions(instruction)

        if not inner_instructions_group:
            return None

        for inner_instruction in inner_instructions_group.instructions:
            if self.is_sale_event(inner_instruction):
                acc_price += inner_instruction.get_int(4, 8)
            elif inner_instruction.is_token_program_instruction:
                # Could be set new authority
                if self.is_set_new_authority(inner_instruction):
                    if acc_price > 0:
                        # A sale event for sure, let's update the buyer info
                        buyer_account = inner_instruction.get_str(3, length=None, b58encode=True)
                        event.buyer = buyer_account
                        event.price = acc_price
                    else:
                        # If changing authority to MagicEden address,
                        # it is a listing event otherwise it is an delisting one
                        new_owner_key = inner_instruction.get_str(3, length=None, b58encode=True)
                        if new_owner_key == self.market_authority_address:
                            # Gets the listing price from the outer matche ParsedInstruction
                            lamports = instruction.get_int(8, 8)
                            event.owner = inner_instruction.accounts[1]
                            event.event_type = SECONDARY_MARKET_EVENT_LISTING
                            event.price = lamports

                            token_account_to_match = inner_instruction.accounts[0]
                        else:
                            event.event_type = SECONDARY_MARKET_EVENT_DELISTING
                            event.owner = new_owner_key
                            token_account_to_match = inner_instruction.accounts[0]
        # Lastly, try find the mint key (token address)
        # Because usually the token has to be carried by a "Token Account",
        # which is a PDA from the Market Place Authority, so the balance change
        # will have to reflect on that account.
        event.token_key, _ = transaction.find_token_address_and_owner(token_account_to_match)

        return event if event.token_key else None

    @staticmethod
    def is_sale_event(inner_instruction):
        return inner_instruction.is_system_program_instruction \
               and inner_instruction.get_function_offset() == SYS_TRANSFER

    @staticmethod
    def is_set_new_authority(inner_instruction):
        return inner_instruction.get_function_offset() == TOKEN_SET_AUTHORITY \
               and inner_instruction.get_int(1, 1) == TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER


class MagicEdenParserV2(TransactionParserInterface):

    listing_event = 0xad837f01a485e633
    delisting_event = 0x4baf5fa3cb82c6c6
    bid_event = 0xeaebda01123d0666
    cancel_bidding_event = 0xe9e0b184da244cee
    sale_event = 0x623314f9dd94a25

    def __init__(self):
        self.type = MarketplaceAccounts.MAGIC_EDEN_PROGRAM_ACCOUNT_V2

    def find_magic_eden_v2_instruction(self, transaction: Transaction) -> Optional[Instruction]:
        instruction = transaction.find_instruction(self.type.value[0], offset=self.sale_event, width=8)

        if not instruction:
            instruction = transaction.find_instruction(self.type.value[0], offset=self.cancel_bidding_event, width=8)

        if not instruction:
            instruction = transaction.find_instruction(self.type.value[0])

        return instruction

    def parse(self, transaction: Transaction):
        # So for sales event there could be variable number of
        # instructions that all match, we need to check and match to see if
        # any of the instruction matches.
        # There could be a case that a single event contains "bid" and "sale"
        # instructions both, in this case we categorize them as "sale".
        # The matching precedence will be sale comes before bid.

        instruction = self.find_magic_eden_v2_instruction(transaction)
        if not instruction:
            return None

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
            event_type = SECONDARY_MARKET_EVENT_PRICE_UPDATE
            # Try to find if there is any set authority inner instruction,
            # if so, it is a listing otherwise it is a price update
            if inner_instructions_group:
                for inner_instruction in inner_instructions_group.instructions:
                    if inner_instruction.is_token_program_instruction \
                            and inner_instruction.get_function_offset() == TOKEN_SET_AUTHORITY:
                        event_type = SECONDARY_MARKET_EVENT_LISTING
                        break
        elif offset == self.delisting_event:
            owner = instruction.accounts[0]
            token_key = instruction.accounts[3]
            event_type = SECONDARY_MARKET_EVENT_DELISTING
        elif offset == self.bid_event:
            buyer = instruction.accounts[0]
            price = instruction.get_int(10, 8)
            event_type = SECONDARY_MARKET_EVENT_BID
            token_key = instruction.accounts[2]
        elif offset == self.sale_event:
            event_type = SECONDARY_MARKET_EVENT_SALE
            buyer = instruction.accounts[0]
            price = instruction.get_int(10, 8)
            token_key = instruction.accounts[4]
        elif offset == self.cancel_bidding_event:
            event_type = SECONDARY_MARKET_EVENT_CANCEL_BIDDING
            buyer = instruction.accounts[0]
            price = 0
            token_key = instruction.accounts[2]

        return SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_MAGIC_EDEN,
            timestamp=transaction.block_time,
            event_type=event_type,
            transaction_hash=transaction.signature,
            owner=owner,
            buyer=buyer,
            price=price,
            token_key=token_key
        ) if event_type and token_key and (owner or buyer) else None
