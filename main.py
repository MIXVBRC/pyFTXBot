import asyncio
from ftx import FtxClient
from ftxTester import Tester


async def task_manager():

    ftx = FtxClient(min_daily_volume=50000, update_time=1)
    tester = Tester(ftx=ftx, usd=10, rounds=1000, maker=True)

    task_list = (
        ftx.actual_price(),
        tester.calc(),
    )

    await asyncio.gather(*task_list)


def main():
    asyncio.run(task_manager())


if __name__ == '__main__':
    main()