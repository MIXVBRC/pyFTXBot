import config
import json
import hmac
import time
from pprint import pprint
from requests import Request, Session
from typing import Optional, Dict, Any


class FtxClient:

    def __init__(self):
        self._session = Session()
        self._account = self._account_info()
        self._coins = list()
        self._purse = {}
        self._market_list = {}
        self._standard_list = list()
        self._min_provide_size = {}
        self._price_list = {}
        self._pairs = {}

        self._account['makerFee'] *= 100
        self._account['takerFee'] *= 100

        self._actual_price()
        self._generate_pairs()

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

        for market in response:

            if market['volumeUsd24h'] < 100000 \
                    or market['baseCurrency'] is None \
                    or market['quoteCurrency'] is None \
                    or market['isEtfMarket'] is None: continue

            base_currency = market['baseCurrency']
            quote_currency = market['quoteCurrency']
            min_provide_size = market['minProvideSize']
            price = market['price']

            if base_currency not in self._market_list:
                self._market_list[base_currency] = [quote_currency]
            else:
                self._market_list[base_currency].append(quote_currency)

            self._coins.append(base_currency)
            self._purse[base_currency] = 0

            self._standard_list.append(f'{base_currency}/{quote_currency}')

            self._min_provide_size[f'{base_currency}/{quote_currency}'] = min_provide_size
            self._min_provide_size[f'{quote_currency}/{base_currency}'] = min_provide_size

            self._price_list[f'{quote_currency}/{base_currency}'] = price
            self._price_list[f'{base_currency}/{quote_currency}'] = 1 / price

    def _generate_pairs(self):

        for coin_a in self._coins:
            for coin_b in self._coins:
                for coin_c in self._coins:

                    if coin_a == coin_b or coin_a == coin_c or coin_b == coin_c: continue
                    if f'{coin_a}/{coin_b}' not in self._price_list: continue
                    if f'{coin_a}/{coin_c}' not in self._price_list: continue
                    if f'{coin_b}/{coin_c}' not in self._price_list: continue
                    if f'{coin_b}{coin_c}{coin_a}' in self._pairs: continue
                    if f'{coin_c}{coin_a}{coin_b}' in self._pairs: continue

                    self._pairs[f'{coin_a}{coin_b}{coin_c}'] = {
                        coin_a: coin_b,
                        coin_b: coin_c,
                        coin_c: coin_a,
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