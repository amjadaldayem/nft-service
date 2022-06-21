import json
from pathlib import Path

import pytest
from src.model import SecondaryMarketEvent, Transaction
from src.parser.monkey_business import MonkeyBusinessParserV2


class TestMonkeyBusinessParser:
    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "sale",
                3,
                65536,
                65798,
                1649986315,
                "4gPYVax8i241xE7cGZNpPb4NTyNNFYK3MiHrFLzo3mv8",
                217000000000,
                "",
                "HG7NsdZTwNFY2ypJzWbcbS2zBtjLQ2VkSFj1MYCT7o1i",
                "2hr931pZZ8qCWBehsLGD5EqXAAJDESafcYVJdrKsM3fwuv3a2RFoyvF9ers1GQ5PGH56wgxjfjPAVeWw3h6bgLcH",
            ),
            (
                "listing",
                1,
                65536,
                65798,
                1648508904,
                "BkhMttZcjx8iJ2dprgEUsremijtFP37BwRvdfUdQ6RLx",
                7500000000000,
                "FwsaNwq4JBANWPDfPNK3GmHoLVauStcyrX8fk12DnyBQ",
                "",
                "32oJTuy5TgsKMp4JogxCKdwaryzWgCyEEVnBdU86ViySjscEHh5x5s9UWNVqyXmsiDmA4rtesE2HDgVTjo3FRYhu",
            ),
            (
                "delisting",
                2,
                65536,
                65798,
                1647697829,
                "GdWUMvgyveFp1LLwSAxTbaHobuf15CYa7YEVg5X6e4uw",
                0,
                "3viTAEqxnK6DPTVvJx4eg9E5ZU3Smkv1XdNzc4256B4A",
                "",
                "3snRJVtiZteJGGry5RE1E8wQouaao63TS6Qve5QZ5PZU9955cZCbBUi1hmnBYQw7CCVQ3UjRakKfjfHYq9gzWLq5",
            ),
        ],
    )
    def test_monkey_business_v2_parser(
        self,
        event_name: str,
        event_value: int,
        blockchain_id: int,
        market_id: int,
        blocktime: int,
        token_key: str,
        price: float,
        owner: str,
        buyer: str,
        transaction_hash: str,
        monkey_business_v2_transaction_path: Path,
        monkey_business_v2_parser: MonkeyBusinessParserV2,
    ) -> None:
        with open(
            monkey_business_v2_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = monkey_business_v2_parser.parse(transaction)

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
