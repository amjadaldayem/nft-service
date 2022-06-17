from typing import Dict, List, Tuple

from sintra.config import settings


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


def solana_market_address_map() -> Dict[int, str]:
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
        magic_eden: settings.blockchain.solana.market.magic_eden.address,
        alpha_art: settings.blockchain.solana.market.alpha_art.address,
        solanart: settings.blockchain.solana.market.solanart.address,
        digital_eyes: settings.blockchain.solana.market.digital_eyes.address,
        solsea: settings.blockchain.solana.market.solsea.address,
        monkey_business: settings.blockchain.solana.market.monkey_business.address,
        open_sea: settings.blockchain.solana.market.open_sea.address,
        exchange_art: settings.blockchain.solana.market.exchange_art.address,
    }


def solana_market_program_id_map() -> Dict[str, int]:
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
        settings.blockchain.solana.market.magic_eden.program_account: magic_eden,
        settings.blockchain.solana.market.magic_eden.program_account_v2: magic_eden,
        settings.blockchain.solana.market.magic_eden.auction_program_account: magic_eden,
        settings.blockchain.solana.market.alpha_art.program_account: alpha_art,
        settings.blockchain.solana.market.solanart.program_account: solanart,
        settings.blockchain.solana.market.digital_eyes.nft_marketplace_program_account: digital_eyes,
        settings.blockchain.solana.market.digital_eyes.direct_sell_program_account: digital_eyes,
        settings.blockchain.solana.market.solsea.program_account: solsea,
        settings.blockchain.solana.market.monkey_business.program_account: monkey_business,
        settings.blockchain.solana.market.monkey_business.program_account_v2: monkey_business,
        settings.blockchain.solana.market.monkey_business.program_account_v3: monkey_business,
        settings.blockchain.solana.market.open_sea.program_account: open_sea,
        settings.blockchain.solana.market.open_sea.auction_program_account: open_sea,
        settings.blockchain.solana.market.exchange_art.program_account: exchange_art,
        settings.blockchain.solana.market.exchange_art.program_account_v2: exchange_art,
        settings.blockchain.solana.market.exchange_art.auction_program_account: exchange_art,
    }


def solana_market_accounts() -> List[str]:
    return list(solana_market_program_id_map().keys())


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
