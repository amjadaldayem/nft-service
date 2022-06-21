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
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                65536,
                65793,
                1635223673,
                "rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk",
                4000000000,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                None,
                "415NNVREVfHMYciwuCfMX1QYZYRgUQVyMobBbYbeU8GCfJUEt7x6sXiM96igMyGsRb3dxzCMbcvvPufPWrNwZsN5",
            ),
            (
                "delisting",
                2,
                65536,
                65793,
                1637214793,
                "rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk",
                0,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                None,
                "3B9ZCpuMsHm5q1f8JKw8psFq5yq8CNcQytmc47km3qYmLXwHtvqibMGYEnHG9GTnmHyZa3caXxWFD1pFs2hSy2LB",
            ),
            (
                "sale",
                3,
                65536,
                65793,
                1636475946,
                "8ag4raw8snR6GbM6znQYv9k4845zs5NYrDZdoxnxaNwK",
                10000000000,
                None,
                "BXxoKHT6CYtRTboZDaJee1ahrHoQSN6RJk3HAKpUWGHa",
                "5aQpquskPCgjMQU5Rp1EktgBe4mcRtMVnTMKQKjvPFv3PVyW51DhzLWR6nFz6Ptrg3yEB2dg1HvVm7d7tqAapNVo",
            ),
        ],
    )
    def test_magic_eden_v1_parser(
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
            assert secondary_market_event.blockchain_id == blockchain_id
            assert secondary_market_event.market_id == market_id
            assert secondary_market_event.blocktime == blocktime
            assert secondary_market_event.token_key == token_key
            assert secondary_market_event.price == price
            assert secondary_market_event.owner == owner
            assert secondary_market_event.buyer == buyer
            assert secondary_market_event.transaction_hash == transaction_hash

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
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                65536,
                65793,
                1645815709,
                "As1cySAyfeesM4MBrYZhs46DFMfnHH3ySU32C2xfSgPv",
                8000000000,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "",
                "3hWD6HQxUhWLChkHQBCisQHb88qGK2cAWkXh7ixHpe1QfYvuMgr4JHAH6aN8767cCBaNzkjDQv1x2CTTApX5nXsn",
            ),
            (
                "delisting",
                2,
                65536,
                65793,
                1645816064,
                "As1cySAyfeesM4MBrYZhs46DFMfnHH3ySU32C2xfSgPv",
                0,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "",
                "5y2MJLobJ1Z5fXdQN6ojg8b2o9yMV3nMpqn5XV1ArLbq6Fe7iAyDACJn26uAYmx8Cj6Qc588Ku1jvREzTYQrux9s",
            ),
            (
                "sale",
                3,
                65536,
                65793,
                1645817729,
                "CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj",
                30000000,
                "",
                "2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ",
                "2F94RKPUcekFsmK8D4BCcK2y3nadcEerfX3kcPBujBTVNpNrUtPFGSN7uA8FGbxzpeAKWLLaqRNY5BCbg5zY2k8t",
            ),
            (
                "bid",
                5,
                65536,
                65793,
                1645817399,
                "CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj",
                30000000,
                "",
                "2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ",
                "3gzq2Txq7u9W2LJpENaV1BJN1m4NnYxKAUC9Zhs1xz9wdt8XgQa46PxGpEmztyRd18v2YV59FEdRVfHcHysjNiKA",
            ),
        ],
    )
    def test_magic_eden_v2_parser(
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
                "price_update",
                1,
                65536,
                65793,
                1645817644,
                "CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj",
                50000000,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "",
                "3He3nAQ4Xg4veRWUDysPC71YPGvy5QMc8frakkvYL5tQ25VUpmFDuMt7rx5tjGLKvNp8tPhs1ot61hvt8TvYuxqw",
            ),
        ],
    )
    def test_magic_eden_v2_parser_price_update_is_listing(
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
