# Entry point for Kinesis producers (Async) for event captures
import asyncio

import asyncclick as click

from app.indexers.solana import solana_sme


@click.group()
async def sme():
    """
    Secondary market producer.

    Returns:

    """
    pass

sme.add_command(solana_sme)


@click.group()
async def main():
    pass


main.add_command(sme)

if __name__ == '__main__':
    asyncio.run(main())
