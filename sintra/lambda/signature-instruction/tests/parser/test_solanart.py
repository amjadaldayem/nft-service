# pylint: disable=unspecified-encoding

import json
from pathlib import Path

import pytest
from src.model import SecondaryMarketEvent, SolanaTransaction
from src.parser.solanart import SolanartParser


class TestSolanartParser:
    @pytest.mark.parametrize(
        "event_name, event_value, blockchain_id, market_id, blocktime, token_key, price, owner, buyer, transaction_hash",
        [
            (
                "listing",
                1,
                65536,
                65796,
                1645665249,
                "5xMBU72azWpXC9VSvrJBBZDTd5F2h6Wztrx386pwr3Uo",
                1000000000,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "",
                "47SMQvy1YrjHzC4iBxUcRubFBP1KRaiVHF3HAqWJTxGUo7JbcP3MMqibu2q2vBzNmdBruQEVEPVM7kysqigfgxG",
            ),
            (
                "delisting",
                2,
                65536,
                65796,
                1645665350,
                "5xMBU72azWpXC9VSvrJBBZDTd5F2h6Wztrx386pwr3Uo",
                0,
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "",
                "2yz48ZsupEwXMjJ7uJLrgsjuiWnZPNecr1rUSoqwSmuvbPFJLqQNnZBxdw69EvQtCvufREGbp2dKN7HeGUJqY2vh",
            ),
            (
                "sale",
                3,
                65536,
                65796,
                1645674107,
                "8hbco5nJC1tSXgkk2XoA94YqaV7w5Y77XETEt6i1AsVC",
                375000000,
                "",
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "3ztDsxKrv6WgcJeibAG3Dn6oCosfUUtJ4rpH9XUpHf3zXQgc6F8uy3kPxhutnA4JpBPkPaNbGdQMzP1yMkoXDigu",
            ),
            (
                "price_update",
                4,
                65536,
                65796,
                1645663983,
                "qrxtayzUUVh3iQXGUskzXapokkoLBEsBirxBpssL2g8",
                20000000,
                "DQ9C6V1RAaUJd9EbLyomgH3bqS7rpJD8AgwkBcpndGFP",
                "",
                "3A6FhqPnNjJBVFAzbLfVrCPRMVxQA5iZMuyTFSZAgAX9PxaypNxDE3Q8JtESNHfPuntF5tPt55XTYXKd6xRzcexN",
            ),
            (
                "bid",
                5,
                65536,
                65796,
                1645663443,
                "8hbco5nJC1tSXgkk2XoA94YqaV7w5Y77XETEt6i1AsVC",
                187500000,
                "",
                "CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4",
                "3MhnpCYyrD7qThqdj79hN7KYQyDceG3F47EJdPynoBe2bm9hn4HJ9EvQqPExL6Zv39GPLHb4tB3wPc1P5qjgJmGX",
            ),
            (
                "sale_auction",
                6,
                65536,
                65796,
                1645660665,
                "HD4oEubiYoiGwkp2kMxpqMYcQfh4EFuW3viTJVZv6Pec",
                175000000000,
                "",
                "7sb2osoKiUNSPQzpU4SK8J5HnVmKRf9UWj5y8ZUjTNL1",
                "2YooURatAAPxZ4av3BXa8y4w3yToDe8oSRWuP1G1pWdjFCj6JY2HrYntg2SafGLMx7hPjNjoKcdbxssUyuvLTGsu",
            ),
            (
                "cancel_bidding",
                7,
                65536,
                65796,
                1645664369,
                "8hbco5nJC1tSXgkk2XoA94YqaV7w5Y77XETEt6i1AsVC",
                0,
                "",
                "HvpKPZE423dAscvC48kMW2hbWR8xXthZzYT2hHnh93w",
                "5egfZHdhr2L5vEpb4Cx8WTK3oBQRTWt9zD3TSMMv368u9ngwuqiv6TRTX59VEoK8PogroGXqB9MkjT7Wk8kEnXyh",
            ),
        ],
    )
    def test_solanart_parser(
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
        solanart_transaction_path: Path,
        solanart_parser: SolanartParser,
    ) -> None:
        with open(solanart_transaction_path / (event_name + ".json"), "r") as json_file:
            json_event = json_file.read()
            transaction_dict = json.loads(json_event)
            transaction = SolanaTransaction.from_dict(transaction_dict)

            secondary_market_event = solanart_parser.parse(transaction)

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
