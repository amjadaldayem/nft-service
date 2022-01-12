from typing import Optional

import click

from app import settings
from app.blockchains.solana import MARKET_ADDRESS_MAP, CustomClient
from app.blockchains.solana.client import fetch_transactions_for_pubkey_para


def sme_get_last_indexed_transaction_hash() -> Optional[str]:
    pass


def sme_save_last_indexed_transaction_hash(latest_transaction_hash):
    pass


def sme_parse_transactions():
    pass


@click.command(name='index-secondary-market')
@click.argument('secondary_market_id')
def sme_index_secondary_market(secondary_market_id):
    """
    Index the given secondary market into database. Side effect is that the
    database backing the indexer will be updated.
    """
    # Reads in the last indexed transaction hash

    secondary_market_pubkey = MARKET_ADDRESS_MAP[secondary_market_id]
    until = sme_get_last_indexed_transaction_hash()
    limit = 200 if not until else None

    c = CustomClient(settings.SOLANA_RPC_ENDPOINT, timeout=60)

    results = fetch_transactions_for_pubkey_para(
        c,
        secondary_market_pubkey,
        before=None,
        until=until,
        limit=limit,
        batch_size=50,
    )
    if results:
        latest_transaction_hash = results[0]

        sme_save_last_indexed_transaction_hash(latest_transaction_hash)
