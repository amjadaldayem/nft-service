from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, List, Optional

import base58
import orjson
from pydantic import BaseModel
from src.config import settings


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


@dataclass
class SignatureEvent:
    """Record representing transaction signature that occurred on the market."""

    blockchain_id: int
    market: str
    market_address: int
    market_account: str
    signature: str
    timestamp: int

    @classmethod
    def from_dict(cls, signature_dict: Dict[str, Any]) -> SignatureEvent:
        return cls(
            blockchain_id=signature_dict["blockchain_id"],
            market=signature_dict["market"],
            market_address=signature_dict["market_address"],
            market_account=signature_dict["market_account"],
            signature=signature_dict["signature"],
            timestamp=signature_dict["timestamp"],
        )


class DataClassBase(BaseModel):
    class Config:
        extra = "ignore"
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        underscore_attrs_are_private = True
        allow_population_by_field_name = True


class SecondaryMarketEvent(DataClassBase):
    """Market event data extracted from transaction signature."""

    blockchain_id: int
    market_id: int
    blocktime: int
    timestamp: int
    event_type: int = 0
    token_key: Optional[str]
    price: int = 0
    owner: Optional[str]
    buyer: Optional[str]
    transaction_hash: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blockchain_id": self.blockchain_id,
            "market_id": self.market_id,
            "blocktime": self.blocktime,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "token_key": self.token_key,
            "price": self.price,
            "owner": self.owner,
            "buyer": self.buyer,
            "transaction_hash": self.transaction_hash,
            "data": self.data,
        }


class Instruction:
    def __init__(self, accounts, data, program, index=None):
        self.accounts = accounts
        self.data = data
        self.program = program
        self.index = index

    @classmethod
    def from_dict(
        cls, instruction_dict: Dict[str, Any], accounts: List[int], index=None
    ) -> Instruction:
        account_indexes = instruction_dict["accounts"]
        data = base58.b58decode(instruction_dict["data"])
        program_index = instruction_dict["programIdIndex"]
        instruction_accounts = [accounts[index] for index in account_indexes]
        program_hash = accounts[program_index]

        return cls(instruction_accounts, data, program_hash, index)

    @cached_property
    def is_system_program_instruction(self) -> bool:
        return self.program == settings.blockchain.solana.metaplex.system_program_id

    @cached_property
    def is_token_program_instruction(self) -> bool:
        return self.program == settings.blockchain.solana.metaplex.token_program_id

    def get_function_offset(self, unknown_width=1) -> int:
        """
        Args:
            unknown_width (int): The function offset width in Bytes for
                unknown program.

        Returns:
        """

        # For system program: u32; for token program: u8
        if self.is_token_program_instruction:
            return int(self.data[0])

        if self.is_system_program_instruction:
            return int.from_bytes(self.data[:4], "little")

        return int.from_bytes(self.data[:unknown_width], "little")

    def get_int(self, start: int, length: int = None) -> int:
        """
        Args:
            start: Which byte to start with, e.g., "0b d1 cc 00" if start = 1
                then we get int.from_bytes(bytes.fromhex("d1cc00"), 'little')
            length:

        Returns: Integer value for starting hex bytes
        """

        end = None if length is None else start + length
        return int.from_bytes(self.data[start:end], "little")

    def get_str(self, start, length=None, b58encode=False) -> str:
        end = None if length is None else start + length
        data_slice = self.data[start:end]
        if b58encode:
            data_slice = base58.b58encode(data_slice)

        return data_slice.decode("utf-8")

    def __eq__(self, other: Instruction):
        if not isinstance(self, other.__class__):
            return False

        return (
            self.index == other.index
            and self.data == other.data
            and self.program == other.program
            and self.accounts == other.accounts
        )


class InnerInstructionsGroup:
    def __init__(self, index, instructions):
        self.index = index
        self.instructions = instructions

    @classmethod
    def from_dict(
        cls, accounts: List[int], inner_instructions_dict: Dict[str, Any]
    ) -> InnerInstructionsGroup:
        inner_instructions = [
            Instruction.from_dict(instruction, accounts)
            for instruction in inner_instructions_dict["instructions"]
        ]
        return cls(inner_instructions_dict["index"], inner_instructions)

    def __eq__(self, other: InnerInstructionsGroup):
        if not isinstance(self, other.__class__):
            return False

        return self.index == other.index and self.instructions == other.instructions


class Transaction:
    def __init__(
        self,
        slot,
        meta,
        fee,
        block_time,
        instructions,
        inner_instructions_groups,
        account_keys,
        post_token_balances,
        signature,
    ):
        self.slot = slot
        self.meta = meta
        self.fee = fee
        self.block_time = block_time
        self.inner_instructions_groups = inner_instructions_groups
        self.instructions = instructions
        self.account_keys = account_keys
        self.post_token_balances = post_token_balances
        self.signature = signature

    @classmethod
    def from_dict(cls, transaction_dict) -> Transaction:
        slot = transaction_dict["slot"]
        meta = transaction_dict["meta"]
        block_time = transaction_dict["blockTime"]

        account_keys = None
        instructions_part = None
        signature = None
        transaction_part = transaction_dict["transaction"]
        if transaction_part:
            signature = transaction_part["signatures"][0]
            message_part = transaction_part["message"]
            if message_part:
                account_keys = message_part["accountKeys"]
                instructions_part = message_part["instructions"]
        instructions = [
            Instruction.from_dict(instruction_json, account_keys, index)
            for index, instruction_json in enumerate(instructions_part)
        ]

        if meta:
            fee = meta["fee"]
            post_token_balances = meta["postTokenBalances"]
            inner_instructions = [
                InnerInstructionsGroup.from_dict(account_keys, inner_instructions_group)
                for inner_instructions_group in meta["innerInstructions"]
            ]
        else:
            fee = None
            post_token_balances = None
            inner_instructions = None

        return cls(
            slot,
            meta,
            fee,
            block_time,
            instructions,
            inner_instructions,
            account_keys,
            post_token_balances,
            signature,
        )

    def get_instruction_by_index(self, index: int) -> Optional[Instruction]:
        if index < 0 or len(self.instructions) > index:
            return None
        return self.instructions[index]

    def find_instruction(
        self, account_key: str, offset: int = None, width: int = 1
    ) -> Optional[Instruction]:
        for instruction in self.instructions:
            instruction_offset = instruction.get_function_offset(width)
            if instruction.program == account_key:
                if offset is None or offset == instruction_offset:
                    return instruction
        return None

    def find_inner_instructions(
        self, instruction: Instruction
    ) -> Optional[InnerInstructionsGroup]:
        for inner_instructions_group in self.inner_instructions_groups:
            if inner_instructions_group.index == instruction.index:
                return inner_instructions_group

        return None

    def find_token_address_and_owner(self, token_account_to_match: Optional[str]):
        """
        Method to figure out the actual token address regardless of the
        market. This is inferred from the "token account", usually the 2nd param
        from the Token transfer program, that for any post balances if its index
        matches the token account index, we know this balance is for the "receiver".

        This works for events with token transfer happened.

        Args:
            token_account_to_match:

        Returns:

        """

        for balance in self.post_token_balances:
            account_index = balance["accountIndex"]
            matched = (
                token_account_to_match is None
                or self.account_keys[account_index] == token_account_to_match
                or balance["owner"] == token_account_to_match
            )

            if matched and balance["uiTokenAmount"]["amount"] == "1":
                return balance["mint"], balance["owner"] if "owner" in balance else None

        return None, None

    def __eq__(self, other: Transaction):
        if not isinstance(self, other.__class__):
            return False

        return (
            self.instructions == other.instructions
            and self.slot == other.slot
            and self.meta == other.meta
            and self.fee == other.fee
            and self.block_time == other.block_time
            and self.inner_instructions_groups == other.inner_instructions_groups
            and self.account_keys == other.account_keys
            and self.post_token_balances == other.post_token_balances
            and self.signature == other.signature
        )


class SolanaTransaction:
    def __init__(
        self,
        slot,
        meta,
        fee,
        block_time,
        instructions,
        inner_instructions_groups,
        account_keys,
        post_token_balances,
        signature,
    ):
        self.slot = slot
        self.meta = meta
        self.fee = fee
        self.block_time = block_time
        self.inner_instructions_groups = inner_instructions_groups
        self.instructions = instructions
        self.account_keys = account_keys
        self.post_token_balances = post_token_balances
        self.signature = signature

    @classmethod
    def from_dict(cls, transaction_dict) -> SolanaTransaction:
        slot = transaction_dict["slot"]
        meta = transaction_dict["meta"]
        block_time = transaction_dict["blockTime"]

        account_keys = None
        instructions_part = None
        signature = None
        transaction_part = transaction_dict["transaction"]
        if transaction_part:
            signature = transaction_part["signatures"][0]
            message_part = transaction_part["message"]
            if message_part:
                account_keys = message_part["accountKeys"]
                instructions_part = message_part["instructions"]
        instructions = [
            Instruction.from_dict(instruction_json, account_keys, index)
            for index, instruction_json in enumerate(instructions_part)
        ]

        if meta:
            fee = meta["fee"]
            post_token_balances = meta["postTokenBalances"]
            inner_instructions = [
                InnerInstructionsGroup.from_dict(account_keys, inner_instructions_group)
                for inner_instructions_group in meta["innerInstructions"]
            ]
        else:
            fee = None
            post_token_balances = None
            inner_instructions = None

        return cls(
            slot,
            meta,
            fee,
            block_time,
            instructions,
            inner_instructions,
            account_keys,
            post_token_balances,
            signature,
        )

    def get_instruction_by_index(self, index: int) -> Optional[Instruction]:
        if index < 0 or len(self.instructions) > index:
            return None
        return self.instructions[index]

    def find_instruction(
        self, account_key: str, offset: int = None, width: int = 1
    ) -> Optional[Instruction]:
        for instruction in self.instructions:
            instruction_offset = instruction.get_function_offset(width)
            if instruction.program == account_key:
                if offset is None or offset == instruction_offset:
                    return instruction
        return None

    def find_inner_instructions(
        self, instruction: Instruction
    ) -> Optional[InnerInstructionsGroup]:
        for inner_instructions_group in self.inner_instructions_groups:
            if inner_instructions_group.index == instruction.index:
                return inner_instructions_group

        return None

    def find_token_address_and_owner(self, token_account_to_match: Optional[str]):
        """
        Method to figure out the actual token address regardless of the
        market. This is inferred from the "token account", usually the 2nd param
        from the Token transfer program, that for any post balances if its index
        matches the token account index, we know this balance is for the "receiver".

        This works for events with token transfer happened.

        Args:
            token_account_to_match:

        Returns:

        """

        for balance in self.post_token_balances:
            account_index = balance["accountIndex"]
            matched = (
                token_account_to_match is None
                or self.account_keys[account_index] == token_account_to_match
                or balance["owner"] == token_account_to_match
            )

            if matched and balance["uiTokenAmount"]["amount"] == "1":
                return balance["mint"], balance["owner"] if "owner" in balance else None

        return None, None

    def __eq__(self, other: SolanaTransaction):
        if not isinstance(self, other.__class__):
            return False

        return (
            self.instructions == other.instructions
            and self.slot == other.slot
            and self.meta == other.meta
            and self.fee == other.fee
            and self.block_time == other.block_time
            and self.inner_instructions_groups == other.inner_instructions_groups
            and self.account_keys == other.account_keys
            and self.post_token_balances == other.post_token_balances
            and self.signature == other.signature
        )


class EthereumTransaction:
    def __init__(
        self, signature, block_number, logs, offset_input, value, receipt_from
    ):
        self.signature = signature
        self.block_number = block_number
        self.logs = logs
        self.offset_input = offset_input
        self.value = value
        self.receipt_from = receipt_from

    @classmethod
    def from_dict(
        cls,
        transaction_details: Dict[str, Any],
        transaction_receipt_event_logs: Dict[str, Any],
    ) -> EthereumTransaction:
        signature = transaction_receipt_event_logs["transactionHash"]
        block_number = transaction_receipt_event_logs["blockNumber"]
        logs = transaction_receipt_event_logs["logs"]
        offset_input = transaction_details["input"]
        value = transaction_details["value"]
        receipt_from = transaction_receipt_event_logs["from"]

        return cls(signature, block_number, logs, offset_input, value, receipt_from)

    def __eq__(self, other: EthereumTransaction):
        if not isinstance(self, other.__class__):
            return False

        return (
            self.signature == other.signature
            and self.block_number == other.block_number
            and self.logs == other.logs
            and self.offset_input == other.offset_input
            and self.value == other.value
            and self.receipt_from == other.receipt_from
        )
