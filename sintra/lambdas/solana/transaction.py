import base58
from functools import cached_property
from typing import Optional

from sintra.lambdas.solana.market_ids import SYSTEM_PROGRAM_ID, TOKEN_PROGRAM_ID


class Transaction:

    @classmethod
    def from_json(cls, transaction_json) -> Optional['Transaction']:
        slot = transaction_json["slot"]
        meta = transaction_json["meta"]
        block_time = transaction_json["blockTime"]

        account_keys = None
        instructions_part = None
        signature = None
        transaction_part = transaction_json["transaction"]
        if transaction_part:
            signature = transaction_part["signatures"][0]
            message_part = transaction_part["message"]
            if message_part:
                account_keys = message_part["accountKeys"]
                instructions_part = message_part["instructions"]
        instructions = [
            Instruction.from_json(instruction_json, account_keys, index) for
            index, instruction_json in enumerate(instructions_part)
        ]

        if meta:
            fee = meta["fee"]
            post_token_balances = meta["postTokenBalances"]
            inner_instructions = [
                InnerInstructionsGroup.from_json(account_keys, inner_instructions_group) for
                inner_instructions_group in meta["innerInstructions"]
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
            signature
        )

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
            signature
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

    def get_instruction_by_index(self, index: int) -> Optional['Instruction']:
        if index < 0 or len(self.instructions) > index:
            return None
        return self.instructions[index]

    def find_instruction(self, account_key: str, offset: int = None, width: int = 1) -> Optional['Instruction']:
        for instruction in self.instructions:
            if instruction.program == account_key:
                if offset is None or offset == instruction.get_function_offset(width):
                    return instruction
        return None

    def find_inner_instructions(self, instruction: 'Instruction') -> Optional['InnerInstructionsGroup']:
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
        post_token_balances = self.post_token_balances

        for balance in post_token_balances:
            account_index = balance["accountIndex"]
            matched = (
                token_account_to_match is None
                or self.account_keys[account_index] == token_account_to_match
                or balance['owner'] == token_account_to_match
            )
            if matched and balance['uiTokenAmount']['amount'] == '1':
                return balance['mint'], balance['owner'] if 'owner' in balance else None
        return None, None

    def __eq__(self, other: 'Transaction'):
        if not isinstance(self, other.__class__):
            return False

        return self.instructions == other.instructions and \
            self.slot == other.slot and \
            self.meta == other.meta and \
            self.fee == other.fee and \
            self.block_time == other.block_time and \
            self.inner_instructions_groups == other.inner_instructions_groups and \
            self.account_keys == other.account_keys and \
            self.post_token_balances == other.post_token_balances and \
            self.signature == other.signature


class Instruction:

    @classmethod
    def from_json(cls, instruction_json, accounts, index=None) -> 'Instruction':
        account_indexes = instruction_json["accounts"]
        data = base58.b58decode(instruction_json["data"])
        program_index = instruction_json["programIdIndex"]
        instruction_accounts = res = [accounts[index] for index in account_indexes]
        program_hash = accounts[program_index]

        return Instruction(instruction_accounts, data, program_hash, index)

    def __init__(self, accounts, data, program, index=None):
        self.accounts = accounts
        self.data = data
        self.program = program
        self.index = index

    @cached_property
    def is_system_program_instruction(self) -> bool:
        return self.program == SYSTEM_PROGRAM_ID

    @cached_property
    def is_token_program_instruction(self) -> bool:
        return self.program == TOKEN_PROGRAM_ID

    def get_function_offset(self, unknown_width=1):
        """

        Args:
            unknown_width (int): The function offset width in Bytes for
                unknown program.

        Returns:

        """
        # For system program: u32; for token program: u8
        if self.is_token_program_instruction:
            return int(self.data[0])
        elif self.is_system_program_instruction:
            return int.from_bytes(self.data[:4], 'little')
        else:
            return int.from_bytes(self.data[:unknown_width], 'little')

    def get_int(self, start: int, length: int = None) -> int:
        """

        Args:
            start: Which byte to start with, e.g., "0b d1 cc 00" if start = 1
                then we get int.from_bytes(bytes.fromhex("d1cc00"), 'little')
            length:

        Returns:

        """
        end = None if length is None else start + length
        return int.from_bytes(self.data[start:end], 'little')

    def get_str(self, start, length=None, b58encode=False) -> str:
        end = None if length is None else start + length
        data_slice = self.data[start:end]
        return (data_slice if not b58encode else base58.b58encode(data_slice)).decode('utf-8')

    def __eq__(self, other: 'Instruction'):
        if not isinstance(self, other.__class__):
            return False

        return self.index == other.index and \
            self.data == other.data and \
            self.program == other.program and \
            self.accounts == other.accounts


class InnerInstructionsGroup:

    @classmethod
    def from_json(cls, accounts, inner_instructions_json) -> 'InnerInstructionsGroup':
        inner_instructions = [
            Instruction.from_json(instruction, accounts) for
            instruction in inner_instructions_json["instructions"]
        ]

        return InnerInstructionsGroup(inner_instructions_json["index"], inner_instructions)

    def __init__(self, index, instructions):
        self.index = index
        self.instructions = instructions

    def __eq__(self, other: 'InnerInstructionsGroup'):
        if not isinstance(self, other.__class__):
            return False

        return self.instructions == other.index and \
            self.instructions == other.instructions
