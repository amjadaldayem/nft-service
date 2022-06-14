# pylint: disable=unspecified-encoding

import json
from pathlib import Path

import pytest
from src.exception import TransactionInstructionMissingException
from src.model import SecondaryMarketEvent, Transaction
from src.parser.alpha_art import AlphaArtParser
from tests.factories import TransactionFactory


class TestAlphaArtParser:
    @pytest.mark.parametrize("event_name, event_value", [("sale", 3)])
    def test_alpha_art_parser(
        self,
        event_name,
        event_value,
        alpha_art_parser: AlphaArtParser,
    ) -> None:
        transaction = TransactionFactory()
        secondary_market_event = alpha_art_parser.parse(transaction)
        assert secondary_market_event.event_type == event_value
        assert isinstance(secondary_market_event, SecondaryMarketEvent)
