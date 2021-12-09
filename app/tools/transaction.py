import asyncio
import os.path
import time

import asyncclick as click
import orjson
from solana.rpc.api import Client

from app import settings
from app.blockchains.solana import CustomAsyncClient


@click.command(name='get-transaction')
@click.argument('signature')
@click.argument('filename')
async def get_transaction(signature, filename):
    c = Client(settings.SOLANA_RPC_ENDPOINT)
    resp = c.get_confirmed_transaction(signature)
    dir_name = os.path.dirname(filename)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    with open(filename, 'wb') as c:
        c.write(orjson.dumps(resp['result'], option=orjson.OPT_INDENT_2))


@click.command(name='get-transactions-for')
@click.argument('public_key')
@click.argument('filename')
@click.option('-l', '--limit', required=False, default=50, type=int)
@click.option('-b', '--before', required=False, default=None)
@click.option('-u', '--until', required=False, default=None)
async def get_transactions_for(public_key, filename, limit, before, until):
    batch_size = 25

    async def get_transaction(client: CustomAsyncClient, idx, sig):
        resp = await client.get_confirmed_transaction(sig)
        return idx, resp['result']

    c = Client(settings.SOLANA_RPC_ENDPOINT)
    resp = c.get_confirmed_signature_for_address2(
        public_key,
        before=before,
        until=until,
        limit=limit
    )
    signatures = resp['result']

    with CustomAsyncClient(settings.SOLANA_RPC_ENDPOINT) as c:
        size = len(signatures)
        start = 0
        all_result = []

        while start < size:
            segment = signatures[start: start + batch_size]
            tasks = [
                asyncio.ensure_future(
                    get_transaction(c, i, signature)
                    for i, signature in enumerate(segment)
                )
            ]
            segment_result = list(await asyncio.gather(*tasks))
            segment_result.sort()
            all_result.extend(segment_result)
            start += batch_size
            time.sleep(0.25)

        with open(filename, 'wb') as fd:
            fd.write(orjson.dumps(all_result, option=orjson.OPT_INDENT_2))
