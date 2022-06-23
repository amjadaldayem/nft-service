from typing import Dict, Tuple

from data_api.config import settings


def solana_market_name_map() -> Dict[int, str]:
    (
        magic_eden,
        alpha_art,
        solanart,
        digital_eyes,
        solsea,
        monkey_business,
        open_sea,
        exchange_art,
    ) = solana_market_addresses()

    return {
        magic_eden: "MagicEden",
        alpha_art: "AlphaArt",
        solanart: "Solanart",
        digital_eyes: "DigitalEyes",
        solsea: "Solsea",
        monkey_business: "Solana Monkey Business",
        open_sea: "OpenSea",
        exchange_art: "ExchangeArt",
    }


def solana_market_urls(token_key: str) -> Dict[int, str]:
    (
        magic_eden,
        alpha_art,
        solanart,
        digital_eyes,
        solsea,
        monkey_business,
        open_sea,
        exchange_art,
    ) = solana_market_addresses()

    return {
        magic_eden: f"https://www.magiceden.io/item-details/{token_key}",
        alpha_art: f"https://www.alpha.art/t/{token_key}",
        solanart: f"https://solanart.io/nft/{token_key}",
        digital_eyes: f"https://digitaleyes.market/item/_/{token_key}",
        solsea: f"https://solsea.io/nft/{token_key}",
        monkey_business: "",
        open_sea: "",
        exchange_art: "",
    }


def solana_market_addresses() -> Tuple[int, int, int, int, int, int, int, int]:
    solana_address = int(settings.blockchain.address.solana, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    magic_eden = solana_address | market_flag | 0x01
    alpha_art = solana_address | market_flag | 0x02
    solanart = solana_address | market_flag | 0x03
    digital_eyes = solana_address | market_flag | 0x04
    solsea = solana_address | market_flag | 0x05
    monkey_business = solana_address | market_flag | 0x06
    open_sea = solana_address | market_flag | 0x07
    exchange_art = solana_address | market_flag | 0x08

    return (
        magic_eden,
        alpha_art,
        solanart,
        digital_eyes,
        solsea,
        monkey_business,
        open_sea,
        exchange_art,
    )
