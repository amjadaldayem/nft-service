from tests.parsers.solana.test_utils import TestDataCategory, generate_secondary_market_event, load_json
import pytest

from sintra.lambdas.solana.constants import SECONDARY_MARKET_EVENT_SALE, SECONDARY_MARKET_EVENT_LISTING, \
    SOLANA_MAGIC_EDEN, SECONDARY_MARKET_EVENT_DELISTING
from sintra.lambdas.solana.parsers.magic_eden_parsers import MagicEdenParserV1
from sintra.lambdas.solana.transaction import Transaction


@pytest.fixture(scope="module")
def magic_eden_parser_v1() -> MagicEdenParserV1:
    return MagicEdenParserV1()


def test_magic_eden_v1_parser_listing_01(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.LISTING.value, "01.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_LISTING,
        token_key='rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk',
        price=4000000000,
        owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_listing_02(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.LISTING.value, "01.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_LISTING,
        token_key='6NUbZ3cDbf2jMcbhZC6spNgD4TgMkh9g93Vmot5Rx1u7',
        price=350000000,
        owner_or_buyer='A8p1JpCvrbUDvU1RQREc47sjnJataHV7cZaGeBUjdtLP',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_listing_03(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.LISTING.value, "01.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_LISTING,
        token_key='ELZfkWWG6R2LzYPj7Ei7z2ui2dS732xbEexf1SRVnFoY',
        price=60000000,
        owner_or_buyer='3DBVvW16wtGhUDr7uN83ftCe6QbPihm6jESssuZa1rzf',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_sale_01(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "01.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='8ag4raw8snR6GbM6znQYv9k4845zs5NYrDZdoxnxaNwK',
        price=10000000000,
        owner_or_buyer='BXxoKHT6CYtRTboZDaJee1ahrHoQSN6RJk3HAKpUWGHa',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_sale_02(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "02.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='CiF2QP7NUfz3t7ZpoTavtRvZRdWadxaUFQKZK6EA6Tjm',
        price=2000000000,
        owner_or_buyer='2b9MDayv83BYeuChcrD1CJuQMxzcd1ALSXiRQ6o4YgGF',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_sale_03(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "03.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='5jcY8Ekvi8frZVPy9rHTtaNBzDvKNb94L9xH7bGJR68b',
        price=1100000000,
        owner_or_buyer='4rfMxcVTKwsx8jexi52nSQG8eCtr8B9yAjcormoVwGFL',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_sale_04(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "04.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='AF5i9bGy8f7bwfidwEPxjfB6qTzpWzGh3kqxwJpSAirH',
        price=3880000000,
        owner_or_buyer='6ddfgCBy9UzFFkr918FsnLvduA2gXsdEDZxxDyMMWtYk',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_sale_05(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "05.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='AddspwH8RRsS8Z3r3gzzPWw2YeYjC5rRk9cnzxfajcGX',
        price=1400000000,
        owner_or_buyer='8hqVU9JpMykEGv1cfVkvDr2hzhDHrHa89mk1hQchDmrR',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_sale_09(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.SALE.value, "09.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_SALE,
        token_key='2EvZ77q5ot3e63nUpGkZaCFKZaQm4u2ciWyRwiKMF1rX',
        price=3400000000,
        owner_or_buyer='2ivnxDtJ3KbyYF2EivgMNFfKZrUNMviumPqnvL9T77aZ',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event


def test_magic_eden_v1_parser_delisting_01(magic_eden_parser_v1: MagicEdenParserV1) -> None:
    # Given
    transaction_json = load_json(TestDataCategory.DELISTING.value, "01.json")
    transaction = Transaction.from_json(transaction_json)
    expected_secondary_market_event = generate_secondary_market_event(
        SOLANA_MAGIC_EDEN,
        SECONDARY_MARKET_EVENT_DELISTING,
        token_key='rp9gXpW4zAetpWBvJY62uTSw1bRwqNd39b2f3hzaNwk',
        price=0,
        owner_or_buyer='CA6WUwiH8E9Z6ZYJvjNkKAV6QPq7ySWvLTT8fW4CNPw4',
        timestamp=transaction.block_time,
        signature=transaction.signature
    )

    # When
    secondary_market_event = magic_eden_parser_v1.parse(transaction)

    # Then
    assert secondary_market_event == expected_secondary_market_event
