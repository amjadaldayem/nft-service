from src.config import settings
from src.exception import UnknownBlockchainException


def base_curency_for_blockchain(blockchain_id: int) -> str:
    if int(settings.blockchain.address.solana, 0) == blockchain_id:
        return "Lamport"

    if int(settings.blockchain.address.ethereum, 0) == blockchain_id:
        return "Wei"


def solana_address() -> int:
    return int(settings.blockchain.address.solana, 0)


def ethereum_address() -> int:
    return int(settings.blockchain.address.ethereum, 0)


def blockchain_id_to_name(blockchain_id: int) -> str:
    if int(settings.blockchain.address.solana, 0) == blockchain_id:
        return "Solana"

    if int(settings.blockchain.address.ethereum, 0) == blockchain_id:
        return "Ethereum"

    raise UnknownBlockchainException(f"Blockchain id: {blockchain_id} not recognized.")
