from typing import Optional
from sintra.lambdas.shared.secondary_market_event import SecondaryMarketEvent
from sintra.lambdas.solana.transaction import Transaction
from sintra.lambdas.solana.market_ids import MarketplaceAccounts
from sintra.lambdas.solana.parsers.magic_eden_parsers import MagicEdenParserV1, MagicEdenParserV2


class SolanaTransactionParsingService:

    @staticmethod
    def create_parsers():
        return [
            MagicEdenParserV1(),
            MagicEdenParserV2()
        ]

    def __init__(self):
        self.parsers = {}
        for parser in self.create_parsers():
            self.parsers[parser.type] = parser

    def parse(self, transaction_json) -> Optional[SecondaryMarketEvent]:
        transaction = Transaction.from_json(transaction_json)

        for marketplace_account in MarketplaceAccounts:
            if marketplace_account.value in transaction.account_keys:
                parser = self.parsers[marketplace_account.value]
                if parser is not None:
                    return parser.parse(transaction)

        return None
