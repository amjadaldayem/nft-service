from src.config import settings


def magic_eden_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x01


def alpha_art_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x02


def solsea_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x05


def solanart_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x04


def exchange_art_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x08


def digital_eyes_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x03


def monkey_business_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x06


def open_sea_id() -> int:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    return solana_address | market_flag | 0x07
