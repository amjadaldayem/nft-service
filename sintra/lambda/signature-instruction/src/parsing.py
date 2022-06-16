from .exception import TransactionParserNotFoundException
from .model import SecondaryMarketEvent, Transaction
from .parser.magic_eden import MagicEdenParserV1, MagicEdenParserV2


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
        return [MagicEdenParserV1(), MagicEdenParserV2()]
