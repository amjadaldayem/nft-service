# pylint: disable=unspecified-encoding

import json
from pathlib import Path
from typing import Any, Dict

import pytest
from hexbytes import HexBytes
from src.model import EthereumTransaction, SecondaryMarketEvent
from src.parser.ethereum.open_sea import EthereumOpenSeaParser


class TestEthereumOpenSeaParser:
    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                196608,
                196865,
                1617122248,
                "0xaf6D892177BBabCD71623f55728eb7bc1E919B8e/15",
                6500000000000000000,
                "0x9A3e204bd2f012122B228FA68Bf97539dA965D3b",
                "",
                "0x67e68505498206d75c80c545e6832934082439290649ba59f6efde545c23c77a",
            ),
            (
                "delisting",
                2,
                196608,
                196865,
                1620338386,
                "0xaf6D892177BBabCD71623f55728eb7bc1E919B8e/21",
                0,
                "0xE24c9e37819e514fe954c2B377342ECCDB3FBd8a",
                "",
                "0x09a560d35160b883ae950ee5d75acbb4b4d481cfcf98a986c19444be2ec1483a",
            ),
            (
                "sale",
                3,
                196608,
                196865,
                1653554100,
                "0x34d85c9CDeB23FA97cb08333b511ac86E1C4E258/76365",
                6000000000000000000,
                "",
                "0xf15D7066B78a4e969deefa1e4cA945212ddd3171",
                "0x1a8d41d06cc7f5728788a3df4363d3107a91591f1cf6b17d0b42656112ec4545",
            ),
        ],
    )
    def test_ethereum_open_sea_parser(
        self,
        event_name,
        event_value,
        blockchain_id,
        market_id,
        blocktime,
        token_key,
        price,
        owner,
        buyer,
        transaction_hash,
        ethereum_open_sea_transaction_path: Path,
        ethereum_open_sea_parser: EthereumOpenSeaParser,
    ) -> None:
        transaction_details: Dict[str, Any]
        transaction_receipt_event_logs: Dict[str, Any]

        with open(
            ethereum_open_sea_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_details = json.loads(json_event)

        with open(
            ethereum_open_sea_transaction_path / (event_name + "_logs.json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_receipt_event_logs = json.loads(json_event)

        transaction_receipt_event_logs["transactionHash"] = HexBytes(
            transaction_receipt_event_logs["transactionHash"]
        )
        transaction_receipt_event_logs["logs"][0]["topics"][-1] = HexBytes(
            transaction_receipt_event_logs["logs"][0]["topics"][-1]
        )

        transaction = EthereumTransaction.from_dict(
            transaction_details, transaction_receipt_event_logs
        )

        secondary_market_event = ethereum_open_sea_parser.parse(transaction)

        assert secondary_market_event.event_type == event_value
        assert secondary_market_event.blockchain_id == blockchain_id
        assert secondary_market_event.market_id == market_id
        assert secondary_market_event.blocktime == blocktime
        assert secondary_market_event.token_key == token_key
        assert secondary_market_event.price == price
        assert secondary_market_event.owner == owner
        assert secondary_market_event.buyer == buyer
        assert secondary_market_event.transaction_hash == transaction_hash

        assert isinstance(secondary_market_event, SecondaryMarketEvent)
