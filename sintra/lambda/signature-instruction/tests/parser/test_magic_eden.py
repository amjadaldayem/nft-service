# pylint: disable=unspecified-encoding

import json
from pathlib import Path

import pytest
from src.exception import TransactionInstructionMissingException
from src.model import SecondaryMarketEvent, Transaction
from src.parser.magic_eden import (
    MagicEdenParserV1,
    MagicEdenParserV2,
    MagicEdenAuctionParser,
)


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

    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "sale_auction_settle_v1",
                6,
                65536,
                65793,
                1645570521,
                "DgQB3MHh4vr4tK876zv91Zd7GittRwCEJdKpjikRShvF",
                700000000,
                "",
                "52srbq1g4zKyUftKcWngzpFkNmwvUVJW5KG1GwZZL21J",
                "3mk8cj7PCzkQS6ryhhFQAGJWsjctgwnZDqBi5DnZdtMn1CuUm49A2q326ykQ2qwZM7P36zPpeVVoqD36zWPnvVip",
            ),
        ],
    )
    def test_magic_eden_auction_settle_v1_parser(
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
        magic_eden_auction_transaction_path: Path,
        magic_eden_auction_parser: MagicEdenAuctionParser,
    ) -> None:
        with open(
            magic_eden_auction_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = magic_eden_auction_parser.parse(transaction)

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

    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "sale_auction_settle_v2",
                6,
                65536,
                65793,
                1645908611,
                "HSJiW3MPPg5PrUg4qdo9jXxiTkX7WZ9tTt5JFUdDXgUp",
                121000000000,
                "",
                "ppTeamTpw1cbC8ybJpppbnoL7xXD9froJNFb5uvoPvb",
                "RWkQKXYYKSDczac8vV6aJRbLWd4NzcanHcuU875TAt5GbJrb9Z3jjwG6S671BRJzSvskyFsr9e7fAiDQFBk4JAs",
            ),
        ],
    )
    def test_magic_eden_auction_settle_v2_parser(
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
        magic_eden_auction_transaction_path: Path,
        magic_eden_auction_parser: MagicEdenAuctionParser,
    ) -> None:
        with open(
            magic_eden_auction_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = magic_eden_auction_parser.parse(transaction)

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
