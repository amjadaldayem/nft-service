from functools import cached_property
from typing import Optional, Mapping

import base58

from app.blockchains.solana import (
    SYSTEM_PROGRAM_ID,
    TOKEN_PROGRAM_ID
)

T_KEY_PROGRAM_INDEX = 'programIdIndex'
T_KEY_DATA = 'data'
T_KEY_ACCOUNTS = 'accounts'
T_KEY_INSTRUCTIONS = 'instructions'
T_KEY_INDEX = 'index'
T_KEY_INNER_INSTRUCTIONS = 'innerInstructions'


class ParsedInstruction:

    @classmethod
    def from_instruction_dict(cls, instruction_dict, account_keys: Mapping) -> Optional['ParsedInstruction']:
        """
        E.g.,
            {
              "accounts": [
                4,
                0
              ],
              "data": "3Bxs4Z2qcg1RTCf9",
              "programIdIndex": 10
            },
        Args:
            instruction_dict:
            account_keys:

        Returns:

        """
        try:
            inst = cls(instruction_dict, account_keys)
            return inst
        except:
            return None

    def __init__(self, instruction_dict, account_keys):
        program_account_index = instruction_dict[T_KEY_PROGRAM_INDEX]
        self.program_account_key = account_keys[program_account_index]
        accounts = instruction_dict[T_KEY_ACCOUNTS]
        self.account_list = [account_keys[ai] for ai in accounts]
        self.data = instruction_dict[T_KEY_DATA]  # Data in raw passed in format.
        self.data_decoded = None

    @cached_property
    def is_system_program_instruction(self):
        return self.program_account_key == SYSTEM_PROGRAM_ID

    @cached_property
    def is_token_program_instruction(self):
        return self.program_account_key == TOKEN_PROGRAM_ID

    @cached_property
    def function_offset(self):
        self.data_decoded = self.data_decoded or base58.b58decode(self.data)  # type: bytes
        # For system program: u32; for token program: u8
        if self.is_token_program_instruction:
            return int(self.data_decoded[0])
        elif self.is_system_program_instruction:
            return int.from_bytes(self.data_decoded[:4], 'little')
        else:
            # TODO: This need to change, tentatively use u32
            #   for any other program?
            return int(self.data_decoded[3::-1])

    def get_int(self, start, length=None):
        self.data_decoded = self.data_decoded or base58.b58decode(self.data)
        end = None if length is None else start + length
        return int.from_bytes(self.data_decoded[start:end], 'little')

    def get_str(self, start, length=None, b58encode=False):
        self.data_decoded = self.data_decoded or base58.b58decode(self.data)
        end = None if length is None else start + length
        s = self.data_decoded[start:end]
        return (s if not b58encode else base58.b58encode(s)).decode('utf-8')
