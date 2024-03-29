import sys
from pprint import pprint
import config
import json
import hmac
import time
from requests import Request, Session
from typing import Optional, Dict, Any


class FtxClient:

    @property
    def wallet(self):
        return self._wallet

    @property
    def price_list(self):
        return self._price_list

    @property
    def commission_maker(self):
        return self._account['makerFee']

    @property
    def commission_taker(self):
        return self._account['takerFee']

    @property
    def min_provide_size(self):
        return self._min_provide_size

    @property
    def pairs(self):
        return self._pairs

    @property
    def pairs_reverse(self):
        return self._pairs_reverse

    @property
    def update_time(self):
        return self._update_time

    def __init__(self, min_daily_volume=0, update_time=5):
        self._session = Session()
        self._account = self._account_info()
        self._coins = list()
        self._wallet = {}
        self._market_list = {}
        self._standard_list = list()
        self._min_provide_size = {}
        self._price_list = {}
        self._pairs = {}
        self._pairs_reverse = {}
        self._min_daily_volume = min_daily_volume
        self._update_time = update_time

        self._account['makerFee'] *= 100
        self._account['takerFee'] *= 100

        self._actual_price()
        self._generate_pairs()
        # print(MarketManager.get_market_list_from_base_currency_name('BRZ'))
        # print(MarketManager.get_market_list_from_quote_currency_name('BRZ'))
        # print(MarketManager.get_market_list())
        # print(MarketManager.get_market_from_name('BTC/BRZ'))

        MarketManager.buy_currency(buy='BTC', sell='BRZ', buy_size=10)

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None, method='GET', login=False):

        ts = int(time.time() * 1000)

        if method == 'GET':
            request = Request(method, f'{config.ftx_api_url}{path}')
        else:
            request = Request(method, f'{config.ftx_api_url}{path}', json=params)

        prepared = request.prepare()

        prepared.headers['Accept'] = 'application/json'
        prepared.headers['Content-Type'] = 'application/json'

        if login is True:

            signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()

            if prepared.body:
                signature_payload += prepared.body

            signature_payload = signature_payload
            signature = hmac.new(config.ftx_secret_key.encode(), signature_payload, 'sha256').hexdigest()

            prepared.headers['FTX-KEY'] = config.ftx_api_key
            prepared.headers['FTX-SIGN'] = signature
            prepared.headers['FTX-TS'] = str(ts)

        response = json.loads(self._session.send(prepared).text)

        if response.get('success') is not True:
            # raise Exception(response.get('error'))
            print(response.get('error'))
            return {}

        return response.get('result')

    def _account_info(self): return self._request(path='account', login=True)

    def _actual_price(self):

        response = self._request(path='markets')

        # with open('coins.json', 'w') as file:
        #     file.write(response)

        for market in response:

            if market['volumeUsd24h'] < self._min_daily_volume: continue
            if market['isEtfMarket']: continue
            if not market['baseCurrency']: continue
            if not market['quoteCurrency']: continue

            base_currency = market['baseCurrency']
            quote_currency = market['quoteCurrency']
            min_provide_size = market['minProvideSize']
            price = market['price']
            MarketManager.add_market(market)
            if f'{base_currency}/{quote_currency}' == 'BTC/USD':
                pass
                # new_market = Market(market)
                # print(new_market.get_buy_size(buy=base_currency, size=0.00001))
                # print(new_market.get_buy_size(buy=quote_currency, size=1))
                # print(new_market.get_buy_size(buy=base_currency, size=0.00009))
                # print(new_market.get_buy_size(buy=quote_currency, size=0.00001))
                # pprint(market)
                # sys.exit()

            # if f'{base_currency}/{quote_currency}' == 'DOGE/BTC':
            #     print(price)
            #     print(1 / price)
            #     pprint(market)
            #     sys.exit()

            if base_currency not in self._market_list:
                self._market_list[base_currency] = [quote_currency]
            else:
                self._market_list[base_currency].append(quote_currency)

            self._coins.append(base_currency)
            self._wallet[base_currency] = 0

            self._standard_list.append(f'{base_currency}/{quote_currency}')

            self._min_provide_size[f'{base_currency}/{quote_currency}'] = min_provide_size
            self._min_provide_size[f'{quote_currency}/{base_currency}'] = min_provide_size

            self._price_list[f'{base_currency}/{quote_currency}'] = price
            self._price_list[f'{quote_currency}/{base_currency}'] = 1 / price

    def _generate_pairs(self):
        for coin_a in self._coins:
            for coin_b in self._coins:
                for coin_c in self._coins:
                    if coin_a == coin_b or coin_a == coin_c or coin_b == coin_c: continue
                    if f'{coin_a}/{coin_b}' not in self._price_list: continue
                    if f'{coin_a}/{coin_c}' not in self._price_list: continue
                    if f'{coin_b}/{coin_c}' not in self._price_list: continue
                    if f'{coin_b}/{coin_c}/{coin_a}' in self._pairs: continue
                    if f'{coin_c}/{coin_a}/{coin_b}' in self._pairs: continue
                    self._pairs[f'{coin_a}/{coin_b}/{coin_c}'] = {
                        coin_a: coin_b,
                        coin_b: coin_c,
                        coin_c: coin_a,
                    }
                    self._pairs_reverse[f'{coin_a}/{coin_b}/{coin_c}'] = {
                        coin_a: coin_c,
                        coin_c: coin_b,
                        coin_b: coin_a,
                    }

    def new_order(self, buy, sell, but_price, buy_size, order_type_limit=False):
        market = f'{buy}/{sell}'
        side = 'buy'

        return self._request(
            path='orders',
            params={
                'market': market,
                'side': side,
                'price': but_price,
                'size': buy_size,
                'type': 'limit' if order_type_limit else 'market',
            },
            method='POST',
            login=True
        )

    def get_wallet_balances(self):
        return self._request(
            path='wallet/balances',
            login=True
        )


class MarketManager:

    _market_list = {}

    @classmethod
    def add_market(cls, market):
        cls._market_list[market['name']] = Market(market)

    @classmethod
    def get_market_from_name(cls, market_name):
        if market_name in cls._market_list:
            return cls._market_list[market_name]
        raise 'Market not found'

    @classmethod
    def get_market_list(cls):
        return cls._market_list

    @classmethod
    def get_market_list_from_base_currency_name(cls, currency_name):
        market_list = {}
        for market_name in cls._market_list:
            if cls._market_list[market_name].base_currency == currency_name:
                market_list[market_name] = cls._market_list[market_name]
        return market_list

    @classmethod
    def get_market_list_from_quote_currency_name(cls, currency_name):
        market_list = {}
        for market_name in cls._market_list:
            if cls._market_list[market_name].quote_currency == currency_name:
                market_list[market_name] = cls._market_list[market_name]
        return market_list

    @classmethod
    def buy_currency(cls, buy, sell, buy_size):
        market = cls.get_market_from_name(f'{buy}/{sell}')



        return market
        pass



class Market:

    @property
    def name(self):
        return self._name

    @property
    def base_currency(self):
        return self._base_currency

    @property
    def quote_currency(self):
        return self._quote_currency

    @property
    def price(self):
        return self._price

    @property
    def min_size(self):
        return self._min_size

    def __init__(self, market):
        self._name = market['name']
        self._base_currency = market['baseCurrency']
        self._quote_currency = market['quoteCurrency']
        self._price = market['price']
        self._min_size = market['minProvideSize']

    def get_buy_size(self, buy, size):
        print(f'Buy: {buy} \n'
              f'Size: {size}')
        print(f'{self.price} * {size}')

        if buy == self._base_currency:

            min_size = self._min_size
            result = self.price * size

            if result < min_size:
                print(f'ERROR | {result} < {min_size}')
                return False

        else:

            min_size = self.price * self._min_size
            result = 1 / self.price * size

            if result < min_size:
                print(f'ERROR | {result} < {min_size}')
                return False

        return result
