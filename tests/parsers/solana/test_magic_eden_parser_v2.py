from tests.parsers.solana.test_utils import TestDataCategory, generate_secondary_market_event, load_json
import pytest

from sintra.lambdas.solana.constants import SECONDARY_MARKET_EVENT_SALE, SECONDARY_MARKET_EVENT_LISTING, \
    SOLANA_MAGIC_EDEN, SECONDARY_MARKET_EVENT_DELISTING, SECONDARY_MARKET_EVENT_CANCEL_BIDDING, \
    SECONDARY_MARKET_EVENT_BID
from sintra.lambdas.solana.parsers.magic_eden_parsers import MagicEdenParserV2
from sintra.lambdas.solana.transaction import Transaction


@pytest.fixture(scope="module")
def magic_eden_parser_v2() -> MagicEdenParserV2:
    return MagicEdenParserV2()


def test_magic_eden_v2_parser_listing_04(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.LISTING.value, "04.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_LISTING,
        token_key='As1cySAyfeesM4MBrYZhs46DFMfnHH3ySU32C2xfSgPv',
        price=8000000000,
        owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_listing_05(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.LISTING.value, "05.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_LISTING,
        token_key='CX1uZr5eLcjD4vkcW158TZeAb7sgceYoHDGYwTpqNvSN',
        price=2500000000,
        owner_or_buyer='Hm7DNow95Ln5NYkTVb6WK4jprcxhZxrdzAnNEqRCRxtx',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_listing_06(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.LISTING.value, "06.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_LISTING,
        token_key='8qhdQC6pS7GjvAMA2xWV4EPsQkHPuDeei2UWPJSZ4CYD',
        price=2250000000,
        owner_or_buyer='7kyRyzHy1jdXKoGHsgbLSdAGdbKmw2hsSvEGNAfG8qBh',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_sale_06(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "06.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
        price=30000000,
        owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_sale_07(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "07.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='BLPdBeUbVD4pX6H9kURxyhgaJR9XHFRWB3WixwwKqRm3',
        price=12300000000,
        owner_or_buyer='5MtT8THrJYLNbxgbpPZUjZchMdmvMTkCT8VR8TQzorMk',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_sale_08(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "08.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
        price=30000000,
        owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_delisting_02(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.DELISTING.value, "02.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_DELISTING,
        token_key='As1cySAyfeesM4MBrYZhs46DFMfnHH3ySU32C2xfSgPv',
        price=0,
        owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_bid_01(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.BID.value, "01.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_BID,
        token_key='CqkUbXgnYhwxfzJRqPVJGparRRsrzMJKGGUuL59Gsajj',
        price=30000000,
        owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_cancel_bidding_01(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.CANCEL_BIDDING.value, "01.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
        token_key='8hUyid6kgBRwTe54wBmQEEGZpbdneWei6e3ZXJcN6oRb',
        price=0,
        owner_or_buyer='75EAivjBWfHZ5LnM1VfqqMZCsgeiAAWZQiqgFQkQQUwm',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v2_parser_cancel_bidding_02(magic_eden_parser_v2: MagicEdenParserV2) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.CANCEL_BIDDING.value, "02.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
        token_key='52tS6BhUM4eFKHm6TJuemVU1QLmmocZ1JQNQiNojE8GH',
        price=0,
        owner_or_buyer='4PaeHjgX7nKUYpRhE7eb2TChkxQYDwKXs8wgYsJ7xxUV',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v2.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event
