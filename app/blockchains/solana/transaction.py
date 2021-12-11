from functools import cached_property
from typing import Optional, Tuple, Dict, List

# Constants for type of instructions
import cachetools

from app.blockchains import (
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SOLANA_DIGITAL_EYES, SOLANA_SOLANART,
)
from app.blockchains.shared import (
    SecondaryMarketEvent,
    SECONDARY_MARKET_EVENT_LISTING,
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_UNLISTING, SECONDARY_MARKET_EVENT_PRICE_UPDATE,
)
from app.blockchains.solana import (
    MARKET_PROGRAM_ID_MAP,
    MARKET_ADDRESS_MAP,
    SYSTEM_PROGRAM_ID,
    SYS_TRANSFER, TOKEN_SET_AUTHORITY, TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER, MAGIC_EDEN_ADDRESS, TOKEN_TRANSFER,
)
from app.blockchains.solana.instruction import (
    T_KEY_PROGRAM_INDEX,
    T_KEY_DATA,
    T_KEY_INDEX,
    T_KEY_INSTRUCTIONS,
    ParsedInstruction
)

T_KEY_POST_TOKEN_BALANCES = 'postTokenBalances'
T_KEY_ACCOUNT_INDEX = 'accountIndex'


class ParsedTransaction:
    @classmethod
    def from_transaction_dict(cls, transaction_dict) -> Optional['ParsedTransaction']:
        """
        Returns a `ParsedTransaction` instance if the input is a valid and successful
        transaction dict.

        Args:
            transaction_dict:

        Returns:
            If there is an error in the transaction input, will return None.
        """
        try:
            slot, meta, block_time, transaction = \
                transaction_dict['slot'], \
                transaction_dict['meta'], \
                transaction_dict['blockTime'], \
                transaction_dict['transaction']
            if not meta['err']:
                return cls(slot, meta, block_time, transaction)
        except:
            return None

    def __init__(self, slot, meta, block_time, transaction):
        self.slot = slot
        self.meta = meta
        self.fee = meta['fee']
        self.inner_instructions = meta['innerInstructions']
        self.block_time = block_time
        self.transaction = transaction
        message = transaction['message']
        self.account_keys = message['accountKeys']
        self.instructions = message['instructions']
        self.post_token_balances = meta[T_KEY_POST_TOKEN_BALANCES]

    @cachetools.cached(cache={})
    async def _parse(self) -> Optional[SecondaryMarketEvent]:
        # See if any secondary market account involved
        secondary_market_id = None
        account_key = None
        # Finds the Program Account Key
        for account_key in self.account_keys:
            if account_key in MARKET_PROGRAM_ID_MAP:
                # Grab the Blockchain ID (our own ID)
                secondary_market_id = MARKET_PROGRAM_ID_MAP[account_key]
                break

        market_authority_address = MARKET_ADDRESS_MAP[secondary_market_id]

        if secondary_market_id == SOLANA_MAGIC_EDEN:
            return await self._parse_magic_eden(account_key, market_authority_address)
        elif secondary_market_id == SOLANA_ALPHA_ART:
            return await self._parse_alpha_art(account_key, market_authority_address)
        elif secondary_market_id == SOLANA_SOLANART:
            return await self._parse_solanart(account_key, market_authority_address)
        elif secondary_market_id == SOLANA_DIGITAL_EYES:
            return await self._parse_digital_eyes(account_key, market_authority_address)

    async def _parse_magic_eden(self, magic_eden_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
        """
        There is no price update event for MagicEden secondary market.

        Args:
            magic_eden_program_key:
            authority_address:

        Returns:

        """
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key=magic_eden_program_key
        )
        if not matched_pi or not inner_ins_array:
            return None
        event = SecondaryMarketEvent(
            market_id=SOLANA_MAGIC_EDEN,
            timestamp=self.block_time,
            event_type=SECONDARY_MARKET_EVENT_SALE
        )
        # If the inner instruction array contains `transfer`s, this is a
        # sale; otherwise, if the length of the array is 2, it is a listing or
        # unlisting
        acc_price = 0
        token_account_to_match = None  # for finding token address.
        for ins in inner_ins_array:
            pi = ParsedInstruction(ins, self.account_keys)
            if not pi:
                # TODO: Capture this exception
                raise
            # For sale event
            if (pi.is_system_program_instruction
                    and pi.get_function_offset() == SYS_TRANSFER):
                acc_price += pi.get_int(4, 8)
            elif pi.is_token_program_instruction:
                # Could be set new authority
                if (pi.get_function_offset() == TOKEN_SET_AUTHORITY
                        and pi.get_int(1, 1) == TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER):
                    if acc_price > 0:
                        # A sale event for sure, let's update the buyer info
                        buyer_account = pi.get_str(3, length=None, b58encode=True)
                        event.buyer = buyer_account
                        event.price = acc_price
                    else:
                        # If changing authority to MagicEden address,
                        # it is a listing event otherwise it is an unlisting one
                        new_owner_key = pi.get_str(3, length=None, b58encode=True)
                        if new_owner_key == authority_address:
                            # Gets the listing price from the outer matche ParsedInstruction
                            lamports = matched_pi.get_int(8, 8)
                            event.owner = pi.account_list[1]
                            event.event_type = SECONDARY_MARKET_EVENT_LISTING
                            event.price = lamports

                            token_account_to_match = pi.account_list[0]
                        else:
                            event.event_type = SECONDARY_MARKET_EVENT_UNLISTING
                            event.owner = new_owner_key
                            token_account_to_match = pi.account_list[0]
        # Lastly, try find the mint key (token address)
        # Because usually the token has to be carried by a "Token Account",
        # which is a PDA from the Market Place Authority, so the balance change
        # will have to reflect on that account.
        event.token_key = self.find_token_address(token_account_to_match)
        return event if event.token_key and (event.owner or event.buyer) else None

    async def _parse_alpha_art(self, alpha_art_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
        """
        Unlisting event on AlphaArt is done by transferring the token back to the
        original owner, then closing the previous token account.

        Args:
            alpha_art_program_key:
            authority_address:

        Returns:

        """
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key=alpha_art_program_key
        )
        if not matched_pi or not inner_ins_array:
            return None
        event = SecondaryMarketEvent(
            market_id=SOLANA_ALPHA_ART,
            timestamp=self.block_time,
            event_type=SECONDARY_MARKET_EVENT_SALE
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
        for ins in inner_ins_array:
            pi = ParsedInstruction(ins, self.account_keys)
            if not pi:
                # TODO: Capture this exception
                raise
            # For sale event
            if (pi.is_system_program_instruction
                    and pi.get_function_offset() == SYS_TRANSFER):
                acc_price += pi.get_int(4, 8)
            elif pi.is_token_program_instruction:
                if pi.get_function_offset() == TOKEN_TRANSFER:
                    if acc_price > 0:
                        # A sale event for sure, let's update the buyer info
                        # In the event of sale on Alpha Art, the accounts[1]
                        # on `matched_pi` is the buyer
                        token_account_to_match = pi.account_list[1]
                        event.buyer = matched_pi.account_list[0]
                        event.price = acc_price
                    else:
                        # Unlisting event
                        # in the event of Unlisting for Alpha Art,
                        # accounts[0] on `matched_pi` the owner
                        event.event_type = SECONDARY_MARKET_EVENT_UNLISTING
                        event.owner = matched_pi.account_list[0]
                elif (pi.get_function_offset() == TOKEN_SET_AUTHORITY
                      and pi.get_int(1, 1) == TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER):
                    # If changing authority to MagicEden address,
                    # it is a listing event otherwise it is an unlisting one
                    new_owner_key = pi.get_str(3, length=None, b58encode=True)
                    if new_owner_key == authority_address:
                        # Gets the listing price from the outer matche ParsedInstruction
                        lamports = matched_pi.get_int(1)
                        event.owner = pi.account_list[1]
                        event.event_type = SECONDARY_MARKET_EVENT_LISTING
                        event.price = lamports
                        token_account_to_match = pi.account_list[0]
                    else:
                        event = None
        # Lastly, try find the mint key (token address)
        # Because usually the token has to be carried by a "Token Account",
        # which is a PDA from the Market Place Authority, so the balance change
        # will have to reflect on that account.
        event.token_key = self.find_token_address(token_account_to_match)
        return event

    async def _parse_solanart(self, solanart_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
        """
        Solnart Program:
         - u8: instruction offset
            04 - Listing
                - u64: listing price
            05 - Sale:
                - u64: sales price
            06 - Price update
                - u64: updated price
         - u64:
        Args:
            solanart_program_key:
            authority_address:

        Returns:

        """
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key=solanart_program_key
        )
        if not matched_pi:
            return None

        price = matched_pi.get_int(1)
        if matched_pi.get_function_offset() == 0x04:
            event_type = SECONDARY_MARKET_EVENT_LISTING
            owner = matched_pi.account_list[0]
            buyer = ''
        elif matched_pi.get_function_offset() == 0x05:
            event_type = SECONDARY_MARKET_EVENT_SALE
            buyer = matched_pi.account_list[0]
            owner = ''
        elif matched_pi.get_function_offset() == 0x06:
            event_type = SECONDARY_MARKET_EVENT_PRICE_UPDATE
            owner = matched_pi.account_list[0]
            buyer = ''
        # elif TODO: Need to figure out the Unlisting event
        else:
            return None

        event = SecondaryMarketEvent(
            market_id=SOLANA_SOLANART,
            timestamp=self.block_time,
            event_type=event_type,
            price=price,
            owner=owner,
            buyer=buyer
        )

        if (event_type == SECONDARY_MARKET_EVENT_LISTING
                or event_type == SECONDARY_MARKET_EVENT_SALE):
            token_account_to_match = None  # for finding token address.
            for ins in inner_ins_array:
                pi = ParsedInstruction(ins, self.account_keys)
                if not pi:
                    # TODO: Capture this exception
                    raise
                if pi.is_token_program_instruction:
                    if (pi.get_function_offset() == TOKEN_SET_AUTHORITY
                            and pi.get_int(1, 1) == TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER
                            and event_type == SECONDARY_MARKET_EVENT_LISTING):
                        token_account_to_match = pi.account_list[0]
                        break
                    elif (pi.get_function_offset() == TOKEN_TRANSFER
                          and event_type == SECONDARY_MARKET_EVENT_SALE):
                        token_account_to_match = pi.account_list[1]
                        break

            event.token_key = self.find_token_address(token_account_to_match)
        elif event_type == SECONDARY_MARKET_EVENT_PRICE_UPDATE:
            event.token_key = matched_pi.account_list[-1]
        else:
            return None
        return event if event.token_key and (event.owner or event.buyer) else None

    async def _parse_digital_eyes(self, digital_eyes_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key=digital_eyes_program_key
        )
        if not matched_pi:
            return None
        # For listing/ulisting event, the account[2] is the mint key
        # For price_update event, the account[1] is the mint key
        event_type = None
        data = None
        token_key = None
        owner = None
        price = 0
        func_offset = matched_pi.get_function_offset(8)
        if func_offset == 12502976635542562355:  # 0x33e685a4017f83ad
            # if the lasts 2bytes == feff, then the price is not visible
            # it will displayed as "contact owner"
            event_type = SECONDARY_MARKET_EVENT_LISTING
            token_key = matched_pi.account_list[2]
            owner = matched_pi.account_list[0]
            price = matched_pi.get_int(8, 8)
        elif func_offset == 1844079875029187840:  # 0x00bd8f40e07c9719
            event_type = SECONDARY_MARKET_EVENT_PRICE_UPDATE
            token_key = matched_pi.account_list[1]
            price = matched_pi.get_int(8, 8)
            owner = matched_pi.account_list[0]
        elif func_offset == 13753127788127181800:  # 0xe8dbdf29dbecdcbe
            event_type = SECONDARY_MARKET_EVENT_UNLISTING
            token_key = matched_pi.account_list[2]
            owner = matched_pi.account_list[0]

        event = SecondaryMarketEvent(
            market_id=SOLANA_DIGITAL_EYES,
            event_type=event_type,
            token_key=token_key,
            owner=owner,
            price=price,
            data=data,
            timestamp=self.block_time
        )
        return event

    @cached_property
    async def event(self):
        return await self._parse()

    def find_token_address(self, token_account_to_match: Optional[str]):
        """
        Common method to figure out the actual token address reglardless of the
        market.

        Args:
            token_account_to_match:

        Returns:

        """
        post_token_balances = self.post_token_balances

        for balance in post_token_balances:
            idx = balance[T_KEY_ACCOUNT_INDEX]
            matched = (
                    token_account_to_match is None
                    or self.account_keys[idx] == token_account_to_match
            )
            if matched and balance['uiTokenAmount']['amount'] == '1':
                return balance['mint']
        return None

    def find_secondary_market_program_instructions(self, program_key) -> \
            Tuple[Optional[ParsedInstruction], Optional[List[Dict]]]:
        """
        Find the instruction from the secondary market program and its inner
        instructions (list of dict)

        Args:
            program_key:

        Returns:

        """
        for ins_index, ins in enumerate(self.instructions):
            matched_pi = ParsedInstruction.from_instruction_dict(ins, self.account_keys)
            if matched_pi.program_account_key == program_key:
                break
        else:
            return None, None

        inner_ins_array = []
        for inner_ins in self.inner_instructions:
            if inner_ins[T_KEY_INDEX] == ins_index:
                # Got the inner instructions for the secondary market program instruction
                inner_ins_array = inner_ins[T_KEY_INSTRUCTIONS]
                break
        return matched_pi, inner_ins_array
