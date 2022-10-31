from ftx import FtxClient
from pprint import pprint


ftx = FtxClient()


def main():
    pprint(ftx.get_wallet_balances())
    pass
    # result = api.new_order(
    #     buy='BTC',
    #     sell='USD',
    #     but_price=100000,
    #     buy_size=100000
    # )
    # result = api.account_info()
    # pprint(result)
    # for coin in result:



if __name__ == '__main__':
    main()