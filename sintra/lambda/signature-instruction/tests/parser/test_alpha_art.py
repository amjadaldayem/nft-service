# pylint: disable=unspecified-encoding

import json
from pathlib import Path

import pytest
from src.model import SecondaryMarketEvent, Transaction
from src.parser.alpha_art import AlphaArtParser


class TestAlphaArtParser:
    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                65536,
                65794,
                1638743111,
                "2Pw69uefPXeqD2PvLjDMD3CohKWFixKVwkf5yJSzAu5K",
                38000000000,
                "okkVSrkBXGfMHvEfKGUW73XmJYbP4ojPbWsBXbYjvZf",
                None,
                "4Yh4AoVgLSWQQoFD75vq3r14Qxqc9vnkWSxjfDAUHAGwK698TDrn869ZTN1h1Bn3fHtsbn5VrQEaQZqXWrUfNrpw",
            ),
            (
                "delisting",
                2,
                65536,
                65794,
                1638293105,
                "2Pw69uefPXeqD2PvLjDMD3CohKWFixKVwkf5yJSzAu5K",
                0,
                "okkVSrkBXGfMHvEfKGUW73XmJYbP4ojPbWsBXbYjvZf",
                None,
                "3CWrdrMfaLYyF5ncRjFgm24RJhyDDCnKtwXwPHF1GXHC38VWZhG9bHW6GWCBZPwVAYQAfHjQ8dWNiw93gDXJCFcX",
            ),
            (
                "sale",
                3,
                65536,
                65794,
                1638838606,
                "Fqc4ts9nN1Hp1mZR6CEx6yG7T4eZH8FN39ruAGc2fTuC",
                950000000,
                None,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "vWJh84c573fzeYdb8xNVAXNu7uTCCNY6HjarN7i8eDHWBZJdvyS4hrH8sSd5GaGZzfUqSgKhhSCRMiFJmC863d3",
            ),
        ],
    )
    def test_alpha_art_parser(
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
        alpha_art_transaction_path: Path,
        alpha_art_parser: AlphaArtParser,
    ) -> None:
        with open(
            alpha_art_transaction_path / (event_name + ".json"), "r"
        ) as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = Transaction.from_dict(transaction_dict)

            secondary_market_event = alpha_art_parser.parse(transaction)

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
