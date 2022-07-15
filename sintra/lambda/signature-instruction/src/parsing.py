from typing import Union

from src.exception import TransactionParserNotFoundException
from src.model import EthereumTransaction, SecondaryMarketEvent, SolanaTransaction
from src.parser.alpha_art import AlphaArtParser
from src.parser.digital_eyes import DigitalEyesParserV1, DigitalEyesParserV2
from src.parser.ethereum.open_sea import (
    EthereumOpenSeaParserV1,
    EthereumOpenSeaParserV2,
)
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
from src.parser.monkey_business import (
    MonkeyBusinessParserV1,
    MonkeyBusinessParserV2,
    MonkeyBusinessParserV3,
)
from src.parser.open_sea import OpenSeaParser, OpenSeaParserAuction
from src.parser.solanart import SolanartParser
from src.parser.solsea import SolseaParser


class TransactionParsing:
    def __init__(self):
        self.parsers = {}
        for parser in self._create_parsers():
            self.parsers[parser.program_account] = parser

    def parse(
        self,
        transaction: Union[SolanaTransaction, EthereumTransaction],
        market_account: str,
    ) -> SecondaryMarketEvent:
        parser = self.parsers.get(market_account, None)
        if parser:
            return parser.parse(transaction)

        raise TransactionParserNotFoundException(
            f"Transaction parser doesn't exist for market account: {market_account}."
        )

    def _create_parsers(self):
        return [
            SolseaParser(),
            MagicEdenParserV1(),
            MagicEdenParserV2(),
            MagicEdenAuctionParser(),
            AlphaArtParser(),
            SolanartParser(),
            ExchangeArtParserV1(),
            ExchangeArtParserV2(),
            ExchangeArtParserAuction(),
            DigitalEyesParserV1(),
            DigitalEyesParserV2(),
            MonkeyBusinessParserV1(),
            MonkeyBusinessParserV2(),
            MonkeyBusinessParserV3(),
            OpenSeaParser(),
            OpenSeaParserAuction(),
            EthereumOpenSeaParserV1(),
            EthereumOpenSeaParserV2(),
        ]
