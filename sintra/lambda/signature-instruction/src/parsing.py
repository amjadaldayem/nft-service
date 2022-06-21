from src.exception import TransactionParserNotFoundException
from src.model import SecondaryMarketEvent, Transaction
from src.parser.alpha_art import AlphaArtParser
from src.parser.exchange_art import (
    ExchangeArtParserAuction,
    ExchangeArtParserV1,
    ExchangeArtParserV2,
)
from src.parser.magic_eden import (
    MagicEdenAuctionParser,
    MagicEdenParserV1,
    MagicEdenParserV2,
)
from src.parser.solanart import SolanartParser
from src.parser.digital_eyes import DigitalEyesV1, DigitalEyesV2


class TransactionParsing:
    def __init__(self):
        self.parsers = {}
        for parser in self._create_parsers():
            self.parsers[parser.program_account] = parser

    def parse(
        self, transaction: Transaction, market_account: str
    ) -> SecondaryMarketEvent:
        parser = self.parsers.get(market_account, None)
        if parser:
            return parser.parse(transaction)

        raise TransactionParserNotFoundException(
            f"Transaction parser doesn't exist for market account: {market_account}."
        )

    def _create_parsers(self):
        return [
            MagicEdenParserV1(),
            MagicEdenParserV2(),
            MagicEdenAuctionParser(),
            AlphaArtParser(),
            SolanartParser(),
            ExchangeArtParserV1(),
            ExchangeArtParserV2(),
            ExchangeArtParserAuction(),
            DigitalEyesV1(),
            DigitalEyesV2(),
        ]
