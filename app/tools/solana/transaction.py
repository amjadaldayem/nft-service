import asyncio
import logging
import os.path
import time

import click
import orjson
from solana.rpc.api import Client

from app import settings
from app.blockchains.solana import CustomClient
from app.blockchains.solana.client import fetch_transactions_for_pubkey_para, get_multi_transactions
from app.utils import partition

logger = logging.getLogger(__name__)


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
    batch_size = 25

    c = CustomClient(settings.SOLANA_RPC_ENDPOINT, timeout=60)
    all_result = fetch_transactions_for_pubkey_para(
        c,
        public_key,
        before=before,
        until=until,
        limit=limit,
        batch_size=batch_size
    )

    failed_signatures = [sig for sig, val in all_result.items() if not val]

    if failed_signatures:
        num_failed_signatures = len(failed_signatures)
        logger.warning(
            "There are %s failed fetches. Retrying those.", num_failed_signatures
        )
        time.sleep(1)
        retried_result = get_multi_transactions(
            signatures=failed_signatures,
            batch_size=min(num_failed_signatures, batch_size)
        )
        # Stiches back
        succeeded, failed = partition(lambda t: t[1], retried_result.items())
        for k, v in succeeded:
            all_result[k] = v
        failed, _ = zip(*failed)
        num_total = len(all_result)
        num_failed = len(failed)
        logger.info("%s/%s transactions retrieved.", num_total - num_failed, num_total)
        logger.warning("Failed signatures: %s", '\n'.join(failed))

    dir_name = os.path.dirname(filename)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    with open(filename, 'wb') as fd:
        fd.write(orjson.dumps(all_result, option=orjson.OPT_INDENT_2))


#
txn.add_command(get_transaction)
txn.add_command(get_transactions_for)
