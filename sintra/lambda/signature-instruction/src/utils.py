from src.config import settings


def magic_eden_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x01
