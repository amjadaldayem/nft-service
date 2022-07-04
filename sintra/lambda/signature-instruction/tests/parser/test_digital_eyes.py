# pylint: disable=unspecified-encoding

import json
from pathlib import Path

import pytest
from src.model import SecondaryMarketEvent, SolanaTransaction
from src.parser.digital_eyes import DigitalEyesParserV1, DigitalEyesParserV2


class TestDigitalEyesParser:
    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                65536,
                65795,
                1634127119,
                "Kyt8aPm6xEWHv4KxcgPJZzYYhqGL3NLJ4YjG2ip8Pfx",
                33000000000,
                "6EeR8NS7zFCWAspSKVcE6UcEj4TZH4wpEtC6Pd9CffEP",
                "",
                "57uj4DYAJMsoU6T74iS8qJr85WAsbUQFm8svRgCStcYvyPaR2fKy6SMmWU6uvBx8w3t8H3j4ek6z7t1PrYLda4YA",
            ),
            (
                "delisting",
                2,
                65536,
                65795,
                1645747205,
                "Kyt8aPm6xEWHv4KxcgPJZzYYhqGL3NLJ4YjG2ip8Pfx",
                0,
                "6EeR8NS7zFCWAspSKVcE6UcEj4TZH4wpEtC6Pd9CffEP",
                "",
                "3h3unm7sKQ2BB542CiWf26LaitDgNAWmURiNfkzQ8xRNEtEXbXyAXZX28Xp457PZTtQkKbRTo8XxFJFC59SCdnNA",
            ),
            (
                "sale",
                3,
                65536,
                65795,
                1637041474,
                "HVqyPbQp7J1FncpshWvPuau3TspjF7ZfRHc67xVuAiFS",
                190000000,
                "",
                "GnsvipETHL3eWp1VZ8Pu9TvbtYFtiTqNQDoH61ms6dPj",
                "2LkGa78ujy3bX5tzGh6vbZkZeKKwvJGftD5YLeCgsUkECMgzvxwGC8daUJmr8ubEvdB8CRBXNWnhhHCf4frpJUqY",
            ),
        ],
    )
    def test_digital_eyes_v1_parser(
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
        digital_eyes_v1_transaction_path: Path,
        digital_eyes_v1_parser: DigitalEyesParserV1,
    ) -> None:
        with open(
            digital_eyes_v1_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = SolanaTransaction.from_dict(transaction_dict)

            secondary_market_event = digital_eyes_v1_parser.parse(transaction)

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
                "listing",
                1,
                65536,
                65795,
                1638511913,
                "DZFnfQzVJtukamiUDaB82r95iDnkCB7uYPoxcAFyJ7Dz",
                100000000,
                "EzvdttH8j8LmrpBzx8vK73rBuYBJy3ggJ1taA1mwe69o",
                "",
                "3YmpfaA97acxQEVn5x3PVrxq8Fa1DstdY2N78mZcPMvkqYhdRiZSfuKLHFz6ptPB5ffazrdNgCZwjvV2gjuCnVbd",
            ),
            (
                "delisting",
                2,
                65536,
                65795,
                1638512678,
                "CuTQhEBTtKf6TEp6kTgHRuG9an2RexW9WzUeGY2jcuzj",
                0,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "",
                "381rw28ZsDygWWLsxroFQ4Nde87NUU94cu2TxABJB1GkPG6BEaZEnXMo27SodEjxaE3oemB9FagM6sptmbJGNq9f",
            ),
            (
                "sale",
                3,
                65536,
                65795,
                1645751092,
                "872JekNfK9MtsKs28XBNfkHxg5GwzqNXyWWt6mhex7RH",
                90000000,
                "",
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "4T6BGM3cRiHVAtJMTMf3TihrC9V7SWE7eYbTrKG4nxGZYv8H8EWCGqroc9H8by34tLoYNNF8YNV8C6RpUwzYLFix",
            ),
            (
                "price_update",
                4,
                65536,
                65795,
                1639175420,
                "Cbvj3kCDfiqX8ZdQFch1xfZvBWKhuG7tzTX7wLAUZ4fn",
                400000000,
                "77vqf9kk2JbMAjNkGf7Au2HwQ8K9fMyi5FLEgbbQwDXD",
                "",
                "5h1JAYkx6QEZjnfHmVyvBC5GknUzb6tWCuHvHTJmKheBV3q2K32cutBnEqbNxLzsZgxQxALWHF76JBRyxaa8gHgD",
            ),
        ],
    )
    def test_digital_eyes_v2_parser(
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
        digital_eyes_v2_transaction_path: Path,
        digital_eyes_v2_parser: DigitalEyesParserV2,
    ) -> None:
        with open(
            digital_eyes_v2_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = SolanaTransaction.from_dict(transaction_dict)

            secondary_market_event = digital_eyes_v2_parser.parse(transaction)

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
