import json
from pathlib import Path

import pytest
from src.model import SecondaryMarketEvent, Transaction
from src.parser.solsea import SolseaParser


class TestSolseaParser:
    @pytest.mark.parametrize(
        "event_name, event_value", [("sale", 3), ("listing", 1), ("delisting", 2)]
    )
    def test_solsea_parser(
        self,
        event_name: str,
        event_value: int,
        solsea_transaction_path: Path,
        solsea_parser: SolseaParser,
    ) -> None:
        with open(solsea_transaction_path / (event_name + ".json"), "r") as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = solsea_parser.parse(transaction)

            assert secondary_market_event.event_type == event_value
            assert isinstance(secondary_market_event, SecondaryMarketEvent)
