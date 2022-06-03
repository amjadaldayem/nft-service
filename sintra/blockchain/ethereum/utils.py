from typing import Dict, List, Tuple

from sintra.config import settings


def ethereum_market_name_map() -> Dict[int, str]:
    open_sea = ethereum_market_addresses()

    return {
        open_sea: "OpenSea",
    }


def ethereum_market_address_map() -> Dict[int, str]:
    open_sea = ethereum_market_addresses()

    return {
        open_sea: settings.blockchain.ethereum.market.open_sea.address,
    }


def ethereum_market_program_id_map() -> Dict[str, int]:
    open_sea = ethereum_market_addresses()

    return {
        settings.blockchain.ethereum.market.open_sea.program_account: open_sea,
        settings.blockchain.ethereum.market.open_sea.program_account_v2: open_sea,
    }


def ethereum_market_accounts() -> List[str]:
    return list(ethereum_market_program_id_map().keys())


def ethereum_market_addresses() -> Tuple[int]:
    ethereum_address = int(settings.blockchain.address.ethereum, 0)
    market_flag = int(settings.blockchain.market.flag, 0)

    open_sea = ethereum_address | market_flag | 0x01

    return open_sea
