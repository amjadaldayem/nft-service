from functools import cached_property
from typing import Optional, Tuple, Dict, List

# Constants for type of instructions
import cachetools

from app.blockchains import (
    SOLANA_MAGIC_EDEN,
    SOLANA_ALPHA_ART,
    SOLANA_DIGITAL_EYES,
    SOLANA_SOLANART,
    SOLANA_SOLSEA,
    BLOCKCHAIN_SOLANA,
    SECONDARY_MARKET_EVENT_LISTING,
    SECONDARY_MARKET_EVENT_DELISTING,
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_SALE_AUCTION,
    SECONDARY_MARKET_EVENT_PRICE_UPDATE,
    EMPTY_PUBLIC_KEY,
    SECONDARY_MARKET_EVENT_UNKNOWN,
    SECONDARY_MARKET_EVENT_BID,
    SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
)
from app.blockchains.solana import (
    MARKET_PROGRAM_ID_MAP,
    MARKET_ADDRESS_MAP,
    SYS_TRANSFER,
    TOKEN_SET_AUTHORITY,
    TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER,
    TOKEN_TRANSFER,
    DIGITAL_EYES_NFT_MARKETPLACE_PROGRAM_ACCOUNT, MAGIC_EDEN_PROGRAM_ACCOUNT, MAGIC_EDEN_PROGRAM_ACCOUNT_V2,
    MAGIC_EDEN_AUCTION_PROGRAM_ACCOUNT,
)
from app.blockchains.solana.instruction import (
    T_KEY_INDEX,
    T_KEY_INSTRUCTIONS,
    ParsedInstruction
)
from app.models import SecondaryMarketEvent

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
        self.signature = self.transaction['signatures'][0]
        message = transaction['message']
        self.account_keys = message['accountKeys']
        self.instructions = message['instructions']
        self.post_token_balances = meta[T_KEY_POST_TOKEN_BALANCES]

    @cachetools.cached(cache={})
    def _parse(self) -> Optional[SecondaryMarketEvent]:
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
            return self._parse_magic_eden(account_key, market_authority_address)
        elif secondary_market_id == SOLANA_ALPHA_ART:
            return self._parse_alpha_art(account_key, market_authority_address)
        elif secondary_market_id == SOLANA_SOLANART:
            return self._parse_solanart(account_key, market_authority_address)
        elif secondary_market_id == SOLANA_DIGITAL_EYES:
            return self._parse_digital_eyes(account_key, market_authority_address)
        elif secondary_market_id == SOLANA_SOLSEA:
            return self._parse_solsea(account_key, market_authority_address)

    def _parse_magic_eden(self, magic_eden_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
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
        if not matched_pi or (inner_ins_array is None):
            return None

        if magic_eden_program_key == MAGIC_EDEN_PROGRAM_ACCOUNT:
            event = self._parse_magic_eden_v1(matched_pi, inner_ins_array, authority_address)
        elif magic_eden_program_key == MAGIC_EDEN_PROGRAM_ACCOUNT_V2:
            event = self._parse_magic_eden_v2(magic_eden_program_key)
        elif magic_eden_program_key == MAGIC_EDEN_AUCTION_PROGRAM_ACCOUNT:
            event = self._parse_magic_eden_auction(magic_eden_program_key)
        else:
            return None

        return event

    def _parse_magic_eden_v1(self, matched_pi: ParsedInstruction, inner_ins_array, authority_address):
        # If the inner instruction array contains `transfer`s, this is a
        # sale; otherwise, if the length of the array is 2, it is a listing or
        # delisting

        offset = matched_pi.get_function_offset(8)

        event_type = SECONDARY_MARKET_EVENT_SALE  # Default value
        if offset == 0x925c97c85b944dee:
            event_type = SECONDARY_MARKET_EVENT_BID
            # Let's not capture Bid events because it is not quite easy
            # now to figure out the token address
            return None

        event = SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_MAGIC_EDEN,
            timestamp=self.block_time,
            event_type=event_type,
            transaction_hash=self.signature
        )
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
                        # it is a listing event otherwise it is an delisting one
                        new_owner_key = pi.get_str(3, length=None, b58encode=True)
                        if new_owner_key == authority_address:
                            # Gets the listing price from the outer matche ParsedInstruction
                            lamports = matched_pi.get_int(8, 8)
                            event.owner = pi.account_list[1]
                            event.event_type = SECONDARY_MARKET_EVENT_LISTING
                            event.price = lamports

                            token_account_to_match = pi.account_list[0]
                        else:
                            event.event_type = SECONDARY_MARKET_EVENT_DELISTING
                            event.owner = new_owner_key
                            token_account_to_match = pi.account_list[0]
        # Lastly, try find the mint key (token address)
        # Because usually the token has to be carried by a "Token Account",
        # which is a PDA from the Market Place Authority, so the balance change
        # will have to reflect on that account.
        event.token_key, _ = self.find_token_address_and_owner(token_account_to_match)
        return event if event.token_key else None

    def _parse_magic_eden_v2(self, program_key):
        magic_eden_listing = 0xad837f01a485e633
        magic_eden_delisting = 0x4baf5fa3cb82c6c6
        magic_eden_bid = 0xeaebda01123d0666
        magic_eden_cancel_bidding = 0xe9e0b184da244cee
        magic_eden_sale = 0x623314f9dd94a25

        # So for sales event there could be variable number of
        # instructions that all match, we need to check and match to see if
        # any of the instruction matches.
        # There could be a case that a single event contains "bid" and "sale"
        # instructions both, in this case we categorize them as "sale".
        # The matching precendence will be sale comes before bid.
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key,
            offset=magic_eden_sale,
            width=8
        )
        if not matched_pi:
            matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
                program_key,
                offset=magic_eden_cancel_bidding,
                width=8
            )

        if not matched_pi:
            matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
                program_key,
            )
            if not matched_pi:
                return None

        offset = matched_pi.get_function_offset(8)
        buyer, owner = EMPTY_PUBLIC_KEY, EMPTY_PUBLIC_KEY
        price = 0
        token_key = EMPTY_PUBLIC_KEY
        event_type = None

        if offset == magic_eden_listing:
            owner = matched_pi.account_list[0]
            token_key = matched_pi.account_list[4]
            price = matched_pi.get_int(10, 8)
            event_type = SECONDARY_MARKET_EVENT_PRICE_UPDATE
            # Try find if there is any set authority inner instruction,
            # if so, it is a listing otherwise it is a price update
            for ins in inner_ins_array:
                pi = ParsedInstruction(
                    ins,
                    self.account_keys
                )
                if (pi and pi.is_token_program_instruction
                        and pi.get_function_offset() == TOKEN_SET_AUTHORITY):
                    event_type = SECONDARY_MARKET_EVENT_LISTING
                    break
        elif offset == magic_eden_delisting:
            owner = matched_pi.account_list[0]
            token_key = matched_pi.account_list[3]
            event_type = SECONDARY_MARKET_EVENT_DELISTING
        elif offset == magic_eden_bid:
            buyer = matched_pi.account_list[0]
            price = matched_pi.get_int(10, 8)
            event_type = SECONDARY_MARKET_EVENT_BID
            token_key = matched_pi.account_list[2]
        elif offset == magic_eden_sale:
            event_type = SECONDARY_MARKET_EVENT_SALE
            buyer = matched_pi.account_list[0]
            price = matched_pi.get_int(10, 8)
            token_key = matched_pi.account_list[4]
        elif offset == magic_eden_cancel_bidding:
            event_type = SECONDARY_MARKET_EVENT_CANCEL_BIDDING
            buyer = matched_pi.account_list[0]
            price = 0
            token_key = matched_pi.account_list[2]

        return SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_MAGIC_EDEN,
            timestamp=self.block_time,
            event_type=event_type,
            transaction_hash=self.signature,
            owner=owner,
            buyer=buyer,
            price=price,
            token_key=token_key
        ) if event_type and token_key and (owner or buyer) else None

    def _parse_magic_eden_auction(self, program_key):
        # TODO: Later we should capture PlaceBid and PlaceBidv2
        #   Now only captures the settlements.
        magic_eden_auction_settle_v1 = 0xd466839057b92aaf
        magic_eden_auction_settle_v2 = 0x912751db8dee2905

        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key,
            offset=magic_eden_auction_settle_v2,
            width=8
        )
        if not matched_pi:
            matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
                program_key,
                offset=magic_eden_auction_settle_v1,
                width=8
            )

        if not matched_pi:
            return None

        owner = EMPTY_PUBLIC_KEY
        buyer = matched_pi.account_list[0]
        event_type = SECONDARY_MARKET_EVENT_SALE_AUCTION

        price = 0
        token_account = None

        for instruction_dict in inner_ins_array:
            pi = ParsedInstruction(instruction_dict, self.account_keys)
            if not pi:
                return None
            if (pi.is_token_program_instruction
                    and pi.get_function_offset() == TOKEN_TRANSFER):
                token_account = matched_pi.account_list[0]
            elif (pi.is_system_program_instruction
                  and pi.get_function_offset() == SYS_TRANSFER):
                if pi.account_list[0] != buyer:
                    # Exclude the tiny amount directly transferred from buyer
                    # for fee.
                    price += pi.get_int(4, 8)

        token_key, _ = self.find_token_address_and_owner(token_account)
        return SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_MAGIC_EDEN,
            timestamp=self.block_time,
            event_type=event_type,
            transaction_hash=self.signature,
            owner=owner,
            buyer=buyer,
            price=price,
            token_key=token_key
        ) if token_key and (buyer or owner) else None

    def _parse_alpha_art(self, alpha_art_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
        """
        Delisting event on AlphaArt is done by transferring the token back to the
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
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_ALPHA_ART,
            timestamp=self.block_time,
            event_type=SECONDARY_MARKET_EVENT_SALE,
            transaction_hash=self.signature
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
                        # Delisting event
                        # in the event of delisting for Alpha Art,
                        # accounts[0] on `matched_pi` the owner
                        event.event_type = SECONDARY_MARKET_EVENT_DELISTING
                        event.owner = matched_pi.account_list[0]
                elif (pi.get_function_offset() == TOKEN_SET_AUTHORITY
                      and pi.get_int(1, 1) == TOKEN_AUTHORITY_TYPE_ACCOUNT_OWNER):
                    # If changing authority to AlphaArt address, otherwise it does
                    # not make any sense.
                    new_owner_key = pi.get_str(3, length=None, b58encode=True)
                    if new_owner_key == authority_address:
                        # Gets the listing price from the outer matche ParsedInstruction
                        lamports = matched_pi.get_int(1)
                        event.owner = pi.account_list[1]
                        event.event_type = SECONDARY_MARKET_EVENT_LISTING
                        event.price = lamports
                        token_account_to_match = pi.account_list[0]
                    else:
                        return None
        # Lastly, try to find the mint key (token address)
        # Because usually the token has to be carried by a "Token Account",
        # which is a PDA from the Market Place Authority, so the balance change
        # will have to reflect on that account.
        event.token_key, _ = self.find_token_address_and_owner(token_account_to_match)
        return event if event.token_key else None

    def _parse_solanart(self, solanart_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
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
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key=solanart_program_key,
        )
        if not matched_pi:
            return None

        # For Solanart, Buy now will contain only 1 instruction matching the program
        # But there is another "winning" an auction, where there will be 2 instructions
        # and the first one is similar to Buy, while the 2nd one is Close Auction
        owner, buyer = EMPTY_PUBLIC_KEY, EMPTY_PUBLIC_KEY
        token_key = EMPTY_PUBLIC_KEY
        price = matched_pi.get_int(1)
        offset = matched_pi.get_function_offset()
        if offset == 0x00 or offset == 0x01:
            # 0x00 for creating auction (first bid)
            # 0x01 for next biddings
            buyer = matched_pi.account_list[0]
            token_key = matched_pi.account_list[3]
            event_type = SECONDARY_MARKET_EVENT_BID
        elif offset == 0x03:
            # Cancel Bidding
            event_type = SECONDARY_MARKET_EVENT_CANCEL_BIDDING
            # Who cancelled it
            buyer = matched_pi.account_list[0]
            token_key = matched_pi.account_list[3]
        elif offset == 0x04:
            # Listing
            event_type = SECONDARY_MARKET_EVENT_LISTING
            owner = matched_pi.account_list[0]
            token_key = matched_pi.account_list[4]
        elif offset == 0x05:
            # For Solanart, Auction Buy is done through 2 steps.
            # The actual data is carried in the second step: Close Auction
            # Delisting is the same offset as buy, only that the buyer (0) and seller (4)
            # are the same one.
            buyer = matched_pi.account_list[0]
            seller = matched_pi.account_list[3]

            close_auction_pi, close_auction_inner_ins_array = self.find_secondary_market_program_instructions(
                program_key=solanart_program_key,
                # Close Auction!
                offset=0x02
            )

            if buyer == seller and not close_auction_pi:
                # De-listing
                event_type = SECONDARY_MARKET_EVENT_DELISTING
                price = 0
                # Figure out the token key from the Token Transfer inner ins
                ii = ParsedInstruction.from_instruction_dict(
                    inner_ins_array[0],
                    self.account_keys
                )
                if ii:
                    token_key, _ = self.find_token_address_and_owner(ii.account_list[1])
                    # Sets the owner and unsets the buyer
                    owner = matched_pi.account_list[0]
                    buyer = EMPTY_PUBLIC_KEY
            else:
                if close_auction_pi:
                    # Auction Buy, price is from the 2nd instruction
                    event_type = SECONDARY_MARKET_EVENT_SALE_AUCTION
                    price = close_auction_pi.get_int(1)
                    for ins_dict in close_auction_inner_ins_array:
                        ii = ParsedInstruction.from_instruction_dict(
                            ins_dict,
                            self.account_keys
                        )
                        if (ii.is_token_program_instruction
                                and ii.get_function_offset() == 0x03):
                            # Tries to find the token address from the eventual owner
                            token_key, buyer = self.find_token_address_and_owner(ii.account_list[1])
                            break
                else:
                    # Buy Now
                    event_type = SECONDARY_MARKET_EVENT_SALE
                    buyer = matched_pi.account_list[0]
                    token_key = matched_pi.account_list[3]
                    for ins_dict in inner_ins_array:
                        ii = ParsedInstruction.from_instruction_dict(
                            ins_dict,
                            self.account_keys
                        )
                        if (ii.is_token_program_instruction
                                and ii.get_function_offset() == 0x03):
                            # Tries to find the token address from the eventual owner
                            token_key, _ = self.find_token_address_and_owner(ii.account_list[1])
                            break
        elif offset == 0x06:
            # Price update!
            event_type = SECONDARY_MARKET_EVENT_PRICE_UPDATE
            owner = matched_pi.account_list[0]
            token_key = matched_pi.account_list[2]
            price = matched_pi.get_int(1)
        else:
            return None

        return SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_SOLANART,
            timestamp=self.block_time,
            event_type=event_type,
            price=price,
            owner=owner,
            buyer=buyer,
            transaction_hash=self.signature,
            token_key=token_key
        ) if token_key and (owner or buyer) else None

    def _parse_digital_eyes(self, digital_eyes_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
        """
        DigitalEyes has two program account: Direct Sale and NFT marketplace.

        Args:
            digital_eyes_program_key:
            authority_address:

        Returns:

        """
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key=digital_eyes_program_key
        )
        if not matched_pi:
            return None

        event_type = SECONDARY_MARKET_EVENT_UNKNOWN
        data = None
        token_key = None
        owner = EMPTY_PUBLIC_KEY  # Not use this as default value instead of None
        buyer = EMPTY_PUBLIC_KEY
        price = 0

        if digital_eyes_program_key == DIGITAL_EYES_NFT_MARKETPLACE_PROGRAM_ACCOUNT:
            func_offset = matched_pi.get_function_offset(1)
            if func_offset == 0x00:
                event_type = SECONDARY_MARKET_EVENT_LISTING
                owner = matched_pi.account_list[0]
                token_key = matched_pi.account_list[2]
                price = matched_pi.get_int(1)
            elif func_offset == 0x01:
                # This is an Escrow exchange event, can be delisting or
                # sale, if there is any SOL transfer, then this is a sale
                # otherwise it is delisting
                token_key = matched_pi.account_list[6]
                # Add up all SOL transfers, and round up to 4th digit after the dot
                acc_price = 0
                has_sol_transfer = False
                for ins in inner_ins_array:
                    pii = ParsedInstruction.from_instruction_dict(ins, self.account_keys)
                    if (pii.is_system_program_instruction
                            and pii.get_function_offset() == SYS_TRANSFER):
                        has_sol_transfer = True
                        acc_price += pii.get_int(4, 8)

                price = int(round(acc_price, 3))

                if has_sol_transfer:
                    # Okay, there are lots of events without any transfers
                    # apparently they are not counted as a Sale.
                    event_type = SECONDARY_MARKET_EVENT_SALE
                    buyer = matched_pi.account_list[0]
                else:
                    event_type = SECONDARY_MARKET_EVENT_DELISTING
                    owner = matched_pi.account_list[0]
        else:
            # Implict digital_eyes_program_key == DIGITAL_EYES_DIRECT_SALE_PROGRAM_ACCOUNT
            # For listing/ulisting event, the account[2] is the mint key
            # For price_update event, the account[1] is the mint key
            direct_sale_listing_func_offset = 0xad837f01a485e633
            direct_sale_price_update_func_offset = 0x19977ce0408fbd00
            direct_sale_delisting_func_offset = 0xbedcecdb29dfdbe8
            direct_sale_sale_func_offset = 0xeaebda01123d0666
            direct_sale_delisting_with_authority = 0x102aee56ce64b81e

            func_offset = matched_pi.get_function_offset(8)
            if func_offset == direct_sale_listing_func_offset:
                # if the lasts 2bytes == feff, then the price is not visible
                # it will display as "contact owner"
                event_type = SECONDARY_MARKET_EVENT_LISTING
                token_key = matched_pi.account_list[2]
                owner = matched_pi.account_list[0]
                price = matched_pi.get_int(8, 8)
            elif func_offset == direct_sale_price_update_func_offset:
                event_type = SECONDARY_MARKET_EVENT_PRICE_UPDATE
                token_key = matched_pi.account_list[1]
                price = matched_pi.get_int(8, 8)
                owner = matched_pi.account_list[0]
            elif func_offset == direct_sale_delisting_func_offset:
                event_type = SECONDARY_MARKET_EVENT_DELISTING
                token_key = matched_pi.account_list[2]
                owner = matched_pi.account_list[0]
            elif func_offset == direct_sale_sale_func_offset:
                event_type = SECONDARY_MARKET_EVENT_SALE
                token_key = matched_pi.account_list[4]
                buyer = matched_pi.account_list[0]
                price = matched_pi.get_int(8, 8)
            elif func_offset == direct_sale_delisting_with_authority:
                event_type = SECONDARY_MARKET_EVENT_DELISTING
                token_key = matched_pi.account_list[2]
                owner = matched_pi.account_list[1]
                price = matched_pi.get_int(8, 8)

        return SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            market_id=SOLANA_DIGITAL_EYES,
            event_type=event_type,
            token_key=token_key,
            owner=owner,
            buyer=buyer,
            price=price,
            data=data,
            timestamp=self.block_time,
            transaction_hash=self.signature
        ) if event_type and token_key and (owner or buyer) else None

    def _parse_solsea(self, solsea_program_key, authority_address) -> Optional[SecondaryMarketEvent]:
        """
        There is no price update events for Solsea either.
        Args:
            solsea_program_key:
            authority_address:

        Returns:

        """
        matched_pi, inner_ins_array = self.find_secondary_market_program_instructions(
            program_key=solsea_program_key
        )
        if not matched_pi:
            return None
        owner, buyer = EMPTY_PUBLIC_KEY, EMPTY_PUBLIC_KEY
        price = 0
        token_key = None
        func_offset = matched_pi.get_function_offset(1)
        if func_offset == 0x00:
            # Listing
            event_type = SECONDARY_MARKET_EVENT_LISTING
            price = matched_pi.get_int(1, 8)
            token_key = matched_pi.account_list[2]
            for ins in inner_ins_array:
                pii = ParsedInstruction.from_instruction_dict(ins, self.account_keys)
                if (pii.is_token_program_instruction
                        and pii.get_function_offset()) == TOKEN_TRANSFER:
                    owner = pii.account_list[2]
                    break
        elif func_offset == 0x01:
            # Delisting
            event_type = SECONDARY_MARKET_EVENT_DELISTING
            # Iterate through the postBalance and find the entry with
            # `amount` == 1
            post_token_balances = self.post_token_balances
            for balance in post_token_balances:
                if balance['uiTokenAmount']['amount'] == '1':
                    owner = balance['owner']
                    token_key = balance['mint']
                    break
        elif func_offset == 0x02:
            # Sale
            event_type = SECONDARY_MARKET_EVENT_SALE
            for ins in inner_ins_array:
                pii = ParsedInstruction.from_instruction_dict(ins, self.account_keys)
                if (pii.is_system_program_instruction
                        and pii.get_function_offset() == SYS_TRANSFER):
                    price += pii.get_int(4, 8)
                    if not buyer:
                        # The buyer is the one transferring out from.
                        buyer = pii.account_list[0]
            price = round(price, 3)
            token_key, _ = self.find_token_address_and_owner(buyer)
        else:
            event_type = None

        return SecondaryMarketEvent(
            blockchain_id=BLOCKCHAIN_SOLANA,
            event_type=event_type,
            market_id=SOLANA_SOLSEA,
            owner=owner,
            buyer=buyer,
            price=price,
            timestamp=self.block_time,
            token_key=token_key,
            transaction_hash=self.signature
        ) if event_type and token_key and (owner or buyer) else None

    @cached_property
    def event(self):
        return self._parse()

    def find_token_address_and_owner(self, token_account_to_match: Optional[str]):
        """
        Common method to figure out the actual token address reglardless of the
        market. This is inferred from the "token account", usually the 2nd param
        from the Token transfer program, that for any post balances if its index
        matches the token account index, we know this balance is for the "receiver".

        This works for events with token transfer happened.

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
                or balance['owner'] == token_account_to_match
            )
            if matched and balance['uiTokenAmount']['amount'] == '1':
                return balance['mint'], balance['owner'] if 'owner' in balance else None
        return None, None

    def find_secondary_market_program_instructions(self, program_key, offset=None, width=1) -> \
            Tuple[Optional[ParsedInstruction], Optional[List[Dict]]]:
        """
        Find the first instruction from the secondary market program and its inner
        instructions (list of dict) that matches the program key.
        Or the one that matches the specific function offset.

        Args:
            program_key:
            offset:the offset value
            width: Function offset width
        Returns:

        """
        for ins_index, ins in enumerate(self.instructions):
            matched_pi = ParsedInstruction.from_instruction_dict(ins, self.account_keys)
            if matched_pi.program_account_key == program_key:
                if offset is None or offset == matched_pi.get_function_offset(width):
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
