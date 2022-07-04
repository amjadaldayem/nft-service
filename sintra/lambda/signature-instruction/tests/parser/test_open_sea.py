# pylint: disable=unspecified-encoding

import json
from pathlib import Path

import pytest
from src.model import SecondaryMarketEvent, SolanaTransaction
from src.parser.open_sea import OpenSeaParser, OpenSeaParserAuction


class TestSolanartParser:
    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                65536,
                65799,
                1651803437,
                "BmMaS4ZFVFLybcrXJ6bwXePvcVYzHyj3cFDHC3RCf11X",
                15000000000,
                "DpQcuWkCBnSkGZyonXRPp6yRpM4B5Av27tNsPbHiwr79",
                "",
                "3SkxQrw4sX5jBgQQmNuVFq9P88N5t2oDB39tXS2sMbTzLudHEEm5qJuNXoeHFtVk7eGk9qJ1qfVSMnP8ERt9WUkP",
            ),
            (
                "delisting",
                2,
                65536,
                65799,
                1652771435,
                "7RHQcsDvYBmvMiCv1KLKu6m9SCY8b2h6GU8sJJDpgvx9",
                0,
                "AgDzhL7GnFKFz1QAhDLWusi9ZNznCj7Qa4CarqwXi8c",
                "",
                "2fxmK3LA3KKACuKJda4SGXh8nrb3cJQ7RGBThbUiU7KJ2iAz9WQAFQHv4fHERBxMVNhKvwz5EsysKiwW5BLAZLeD",
            ),
            (
                "sale",
                3,
                65536,
                65799,
                1649890798,
                "7RsJRvyuCsxQE4H7QuutrjnjonMsZAgX7YVY56fG4Kyk",
                951000000000,
                "",
                "836AqkEnj1JQNW6uSULjQ7y8bGBrpQHWzPkKi8mCYkP4",
                "FLw9VPGEuZU49G6HUxnhY5Y9KeccvEHe5N4298TEkGxtTKeMJhxUHjGn2xyaffUiVWSJDzyTxN8pXqKL7GEp9wX",
            ),
            (
                "bid",
                5,
                65536,
                65799,
                1652862306,
                "HkUgSJhzVzxcfyViMAvJUMcW8JkzSK5VuHsFtze7REZQ",
                1400000000,
                "",
                "4fpwG8SEfuufN5zg1x8p12zS2oCFKQBrEWMLTUV6ZWTd",
                "5HpjpVTiiwvFMJKrZwCQg8G7PwrDBQSqBKWJcxv7W2RheUr3of3kaFpeLkJy9sWR1KGk11tE6yKBV6BKugH3aTi8",
            ),
            (
                "cancel_bidding",
                7,
                65536,
                65799,
                1652862306,
                "4kcxqNCKDj3SW2wqSwEGWVLeX3gCPVv5ExKj3QKunvAN",
                0,
                "",
                "BdMnaspQQRfFMxfbgXpbuEcCr4oXtC1u3sm4fdhBBiDT",
                "4e62S1b8ueTRGgMEgrDH2zjnJUZWQVr6WdbABJehrHNFNFeWRHKUm7ippyiziWVrGJT48Mdr1Zuw89opEJoCHnv6",
            ),
        ],
    )
    def test_open_sea_parser(
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
        open_sea_transaction_path: Path,
        open_sea_parser: OpenSeaParser,
    ) -> None:
        with open(open_sea_transaction_path / (event_name + ".json"), "r") as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = SolanaTransaction.from_dict(transaction_dict)

            secondary_market_event = open_sea_parser.parse(transaction)

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
                65799,
                1652862125,
                "FWQyd2rd3YQd19L5jzEQnTLFAVf6Xn2THtVTnxLraWiu",
                290000000,
                "",
                "DXGB1QU3bKxFmk7v58UPm1gEatdnZgd8RxR6vZkU7kfC",
                "3q6tj7zy5vC5AvRGsVLfF7XDU7zgFgD7aQ61AU7Gk6W5iZqfowkG4sX5pMT9dXvTW5Ubj1Yduq6T4tauzKaMnDeG",
            ),
            (
                "sale_auction",
                6,
                65536,
                65799,
                1652862053,
                "88aeHZbPwaa8W1EGTxiAUDwLQYMBdHTwiDSXEWGDhxce",
                750000000,
                "",
                "D2J2rUDi6yZQw8MHMfnM2Gfb1ou19FMpTWRKXMTqjEQY",
                "5sSdbPWkdN868Ah5RX1XUDJbU3mVwDjgeMwcc6Sh5QMuwHrqXevdZU76kR3JbfcygSCknBQAz3J9UZFpWsgB3R6w",
            ),
        ],
    )
    def test_open_sea_auction_parser(
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
        open_sea_auction_transaction_path: Path,
        open_sea_parser_auction: OpenSeaParserAuction,
    ) -> None:
        with open(
            open_sea_auction_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = SolanaTransaction.from_dict(transaction_dict)

            secondary_market_event = open_sea_parser_auction.parse(transaction)

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
