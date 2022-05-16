from abc import abstractmethod
from typing import Optional
from sintra.lambdas.solana.transaction import Transaction
from sintra.lambdas.shared.secondary_market_event import SecondaryMarketEvent


class TransactionParserInterface:

    @abstractmethod
    def parse(self, transaction: Transaction) -> Optional[SecondaryMarketEvent]:
        pass
