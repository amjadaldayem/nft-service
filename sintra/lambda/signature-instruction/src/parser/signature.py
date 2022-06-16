from abc import ABC, abstractmethod
from typing import Optional

from ..model import SecondaryMarketEvent, Transaction


class SignatureParser(ABC):
    @abstractmethod
    def parse(self, transaction: Transaction) -> Optional[SecondaryMarketEvent]:
        pass
