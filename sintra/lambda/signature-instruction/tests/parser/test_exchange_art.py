import json
from pathlib import Path

import pytest
from src.model import SecondaryMarketEvent, Transaction
from src.parser.exchange_art import (
    ExchangeArtParserAuction,
    ExchangeArtParserV1,
    ExchangeArtParserV2,
)


class TestExchangeArtParser:
    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                65536,
                65800,
                1651685165,
                "8RaspTAZARrhbG79mxCCK43CMdqF2vV4ivzPiV6YUgND",
                344000000000,
                "JB9ewxYZQgLvTxC5CtKpdpWqcFWrn3FqEzKsWzVfUubN",
                "",
                "3txsaECttCnasWfK9ecq7y6X1goMAi78L6WYcwj9Tcpxj8Un2wqCwke45WNGFYsgCmdYxeKXE7P41E2Rf85gbYau",
            ),
            (
                "sale",
                3,
                65536,
                65800,
                1651652901,
                "8PSdqJYxLp3ZfaM5SqasMqPdTXR9SY2YTtUYJnWGx1Yz",
                6000000000,
                "",
                "8LAnvxpF7kL1iUjDRjmP87xiuyCx4yX3ZRAoDCChKe1L",
                "38JojyTN3cmwtzVLG7swZUvhfTaT2Utsh7eQVhewAqGw7KcNgQwMT3j9T7p7ShVd2rmfx5NbUtergY9rLLxe8FTW",
            ),
        ],
    )
    def test_exchange_art_v1_parser(
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
        exchange_art_transaction_path: Path,
        exchange_art_v1_parser: ExchangeArtParserV1,
    ) -> None:
        with open(
            exchange_art_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = exchange_art_v1_parser.parse(transaction)

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
                "bid",
                5,
                65536,
                65800,
                1653130441,
                "Eyh2QvkmqF66aFhA3vCxe5iCo94jwMUpxsrouSnZGb7T",
                700000000,
                "",
                "8Lr8RZ1ncnjCjJRNDs5unYc9eQNYwHbccKjM89v24uUn",
                "3QBv4bQVKwWRuazsWspTt9vZnViJogse574qxcAX61Q7STFQLNYxAXeVrvbN7dqMLKuecwDtsigdLVejBhJt6URp",
            ),
            (
                "cancel_bidding",
                7,
                65536,
                65800,
                1647291143,
                "3ZLWZRgimx54uXQKcDYSMwvdPMX9JFB1HWVCuX7K8WBo",
                0,
                "",
                "GG9bktoBbe11cno3JfVWDWi5s6Q2Kmx2NnYGckWcfw57",
                "3PYabcqNQy4nedbt6E9WYdqVahhQWTPiZ3iRUGbBU1AnQwDStMSjSdYkMRMMHRoa6PenXJ5kjzxZgDiPdqMZPasd",
            ),
        ],
    )
    def test_exchange_art_v2_parser(
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
        exchange_art_transaction_path: Path,
        exchange_art_v2_parser: ExchangeArtParserV2,
    ) -> None:
        with open(
            exchange_art_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = exchange_art_v2_parser.parse(transaction)

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
                "delisting",
                2,
                65536,
                65800,
                1650578455,
                "DFzHqRFgTSCCeRsh25HNN8AEwvLuSnkmNyyFyuKb5nGq",
                0,
                "6VrGJHzYnWwiMmkuqFejbA6A2evimde31AFRnATLMYQa",
                "",
                "3PZzFpiZZYnkcc4he8PzQYfXCo2agWpkHyHcBc468MThnLXMPZbXMES3dQTje74W81jqgFhN4PxBMPyJHmHjKBd4",
            ),
        ],
    )
    def test_exchange_art_auction_parser(
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
        exchange_art_transaction_path: Path,
        exchange_art_auction_parser: ExchangeArtParserAuction,
    ) -> None:
        with open(
            exchange_art_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = exchange_art_auction_parser.parse(transaction)

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
