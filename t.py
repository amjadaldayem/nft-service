import asyncio

from solana.rpc.websocket_api import connect


async def main():
    async with connect("wss://ssc-dao.genesysgo.net") as client:
        # await client.account_subscribe(
        #     PublicKey('GUfCR9mK6azb9vcpsxgXyj7XRPAKJd4KMHTTVvtncGgp')
        # )
        await client.logs_subscribe(
            {
                'mentions': [
                    'MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8'
                ]
            }
        )
        resp = await client.recv()
        sub_id = resp.result
        try:
            async for msg in client:
                try:
                    signature = msg.result.value.signature
                    print(signature)
                except Exception as e:
                    print(str(e))
        finally:
            await client.logs_unsubscribe(sub_id)


if __name__ == '__main__':
    asyncio.run(main())
