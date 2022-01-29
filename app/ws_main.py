import asyncio

from app.indexers.solana.aio_transaction_listeners import iter_events_for


async def main():
    async for signagure in iter_events_for():
        print(signagure)


if __name__ == '__main__':
    # Entry point for Websocket client
    asyncio.run(main())
