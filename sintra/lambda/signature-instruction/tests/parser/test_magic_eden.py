# pylint: disable=unspecified-encoding

import json
from pathlib import Path

import pytest
from src.exception import TransactionInstructionMissingException
from src.model import SecondaryMarketEvent, Transaction
from src.parser.magic_eden import MagicEdenParserV1, MagicEdenParserV2


class TestMagicEdenParser:
    @pytest.mark.parametrize(
        "event_name, event_value", [("sale", 3), ("listing", 1), ("delisting", 2)]
    )
    def test_magic_eden_v1_parser(
        self,
        event_name,
        event_value,
        magic_eden_v1_transaction_path: Path,
        magic_eden_v1_parser: MagicEdenParserV1,
    ) -> None:
        with open(
            magic_eden_v1_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = magic_eden_v1_parser.parse(transaction)

            assert secondary_market_event.event_type == event_value
            assert isinstance(secondary_market_event, SecondaryMarketEvent)

    def test_magic_eden_v1_parser_bid_event(
        self,
        magic_eden_v1_transaction_path: Path,
        magic_eden_v1_parser: MagicEdenParserV1,
    ) -> None:
        with open(magic_eden_v1_transaction_path / "bid.json", "r") as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            with pytest.raises(TransactionInstructionMissingException):
                magic_eden_v1_parser.parse(transaction)

    @pytest.mark.parametrize(
        "event_name, event_value",
        [("bid", 5), ("sale", 3), ("listing", 1), ("delisting", 2)],
    )
    def test_magic_eden_v2_parser(
        self,
        event_name,
        event_value,
        magic_eden_v2_transaction_path: Path,
        magic_eden_v2_parser: MagicEdenParserV2,
    ) -> None:
        with open(
            magic_eden_v2_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = magic_eden_v2_parser.parse(transaction)

            assert secondary_market_event.event_type == event_value
            assert isinstance(secondary_market_event, SecondaryMarketEvent)

    def test_magic_eden_v2_parser_price_update_is_listing(
        self,
        magic_eden_v2_transaction_path: Path,
        magic_eden_v2_parser: MagicEdenParserV2,
    ) -> None:
        with open(
            magic_eden_v2_transaction_path / "price_update.json", "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = magic_eden_v2_parser.parse(transaction)

            assert secondary_market_event.event_type == 1
            assert isinstance(secondary_market_event, SecondaryMarketEvent)
