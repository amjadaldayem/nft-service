from typing import Dict, List

from strenum import StrEnum

from sintra.blockchain.solana.utils import (
    solana_market_accounts,
    solana_market_address_map,
    solana_market_name_map,
    solana_market_program_id_map,
)


class BlockchainName(StrEnum):
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    TERRA = "terra"


def market_name_map(blockchain: str) -> Dict[int, str]:
    if blockchain == BlockchainName.SOLANA:
        return solana_market_name_map()
    if blockchain == BlockchainName.ETHEREUM:
        pass
    if blockchain == BlockchainName.TERRA:
        pass

    raise NotImplementedError("Blockchain value not existing.")


def market_address_map(blockchain: str) -> Dict[int, str]:
    if blockchain == BlockchainName.SOLANA:
        return solana_market_address_map()
    if blockchain == BlockchainName.ETHEREUM:
        pass
    if blockchain == BlockchainName.TERRA:
        pass

    raise NotImplementedError("Blockchain value not existing.")


def market_program_id_map(blockchain: str) -> Dict[str, int]:
    if blockchain == BlockchainName.SOLANA:
        return solana_market_program_id_map()
    if blockchain == BlockchainName.ETHEREUM:
        pass
    if blockchain == BlockchainName.TERRA:
        pass

    raise NotImplementedError("Blockchain value not existing.")


def market_accounts(blockchain: str) -> List[str]:
    if blockchain == BlockchainName.SOLANA:
        return solana_market_accounts()
    if blockchain == BlockchainName.ETHEREUM:
        pass
    if blockchain == BlockchainName.TERRA:
        pass

    raise NotImplementedError("Blockchain value not existing.")
