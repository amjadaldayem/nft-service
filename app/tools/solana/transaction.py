import asyncio
import os.path
import time

import click
import orjson
from solana.rpc.api import Client

from app import settings
from app.blockchains.solana import CustomAsyncClient
from app.blockchains.solana.client import fetch_transactions_for_pubkey_para


@click.group()
def txn():
    """
    Transaction related commands

    """
    return


@click.command(name='get')
@click.argument('signature')
@click.argument('filename')
def get_transaction(signature, filename):
    c = Client(settings.SOLANA_RPC_ENDPOINT)
    resp = c.get_confirmed_transaction(signature)
    dir_name = os.path.dirname(filename)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    with open(filename, 'wb') as c:
        c.write(orjson.dumps(resp['result'], option=orjson.OPT_INDENT_2))


@click.command(name='for')
@click.argument('public_key')
@click.argument('filename')
@click.option('-l', '--limit', required=False, default=50, type=int)
@click.option('-b', '--before', required=False, default=None)
@click.option('-u', '--until', required=False, default=None)
def get_transactions_for(public_key, filename, limit, before, until):
    """
    Get transactions for a public_key and stores them to `file_name`

    The `before` transaction and `until` transaction are not included in the
    result, only transactions within.

    """
    batch_size = 50

    with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT, timeout=60) as c:
        all_result = fetch_transactions_for_pubkey_para(
            c,
            public_key,
            before=before,
            until=until,
            limit=limit,
            batch_size=batch_size
        )

        dir_name = os.path.dirname(filename)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        with open(filename, 'wb') as fd:
            fd.write(orjson.dumps(all_result, option=orjson.OPT_INDENT_2))


txn.add_command(get_transaction)
txn.add_command(get_transactions_for)
