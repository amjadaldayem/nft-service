import os.path

import asyncclick as click
import orjson
from solana.rpc.api import Client

from app import settings


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
