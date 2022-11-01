from pprint import pprint
from ftx import FtxClient
from ftxTester import Tester


ftx = FtxClient(min_daily_volume=50000, update_time=1)
tester = Tester(ftx=ftx, usd=10, rounds=1000, maker=True)


def main():
    # pprint(ftx.price_list,sort_dicts=False)
    # pprint(tester.calc(), sort_dicts=False)
    # tester.calc()
    pass


if __name__ == '__main__':
    main()