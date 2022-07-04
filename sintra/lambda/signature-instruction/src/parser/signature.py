from abc import ABC, abstractmethod
from typing import Optional, Union

from src.model import SecondaryMarketEvent, SolanaTransaction, EthereumTransaction


class SignatureParser(ABC):
    @abstractmethod
    def parse(
        self, transaction: Union[SolanaTransaction, EthereumTransaction]
    ) -> Optional[SecondaryMarketEvent]:
        pass
