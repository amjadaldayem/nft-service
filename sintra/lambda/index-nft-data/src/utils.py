from src.config import settings


def solana_address() -> int:
    return int(settings.blockchain.address.solana, 0)


def ethereum_address() -> int:
    return int(settings.blockchain.address.ethereum, 0)
