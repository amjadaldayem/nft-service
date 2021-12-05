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
    with open(filename, 'wb') as c:
        c.write(orjson.dumps(resp['result'], option=orjson.OPT_INDENT_2))
