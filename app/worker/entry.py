import asyncclick as click


@click.command(name='start')
@click.argument('public_key')
@click.argument('filename')
@click.option('-l', '--limit', required=False, default=50, type=int, nu)
@click.option('-b', '--before', required=False, default=None)
@click.option('-u', '--until', required=False, default=None)
async def start():
    pass
