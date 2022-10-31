import asyncio
from pprint import pprint

from ftx import FtxClient


class Tester:

    def __init__(self, ftx: FtxClient, usd, rounds, maker=True):
        self._ftx = ftx
        self._commission = self._ftx.commission_maker if maker is True else self._ftx.commission_taker
        self._wallet = ftx.wallet
        self._diff_stat = {}
        self._calc_count = 0
        self._usd = usd
        self._rounds = rounds

    def commission(self, value):
        return value - (value / 100 * self._commission)

    def _buy(self, buy, sell, pay, commission=True):

        # Нельзя торговать покупать "доллар за доллар"
        # На кошельке должны быть средства
        if buy == sell or self._wallet[sell] < pay: return False

        # Получаем торговые пары
        transfer = f'{sell}/{buy}'
        reverse_transfer = f'{buy}/{sell}'

        # На FTX сумма покупаемых монет должна быть кратна числу
        # Получаем количество монет, которое можем купить
        buy_result = pay * self._ftx.price_list[transfer]

        # Если количество монет меньше кратности, то выходим
        if buy_result < self._ftx.min_provide_size[transfer]: return False

        # Получаем остаток кратности монеты, например: 3 % 2 = 1
        # Пример для SHIB: 1403289 % 100000 = 3289
        buy_remainder = buy_result % self._ftx.min_provide_size[transfer]

        # Сколько купим по итогу монет
        buy_finish = buy_result - buy_remainder
        # buy_finish = buy_result

        # Здача, возвращаем остаток кратности
        sell_finish = buy_finish * self._ftx.price_list[reverse_transfer]

        # Вычетаем комиссию
        if commission is True:
            buy_finish = self.commission(buy_finish)

        # Совершаем перевод
        self._wallet[buy] += buy_finish
        self._wallet[sell] -= sell_finish

    def _revers(self, pair_key):
        return self._ftx.pairs_reverse[pair_key]

    async def calc(self):
        while True:
            print(self._ftx.price_list)
            pairs = self._ftx.pairs
            diff_list = {}
            for pair_key in pairs:

                # Данный for для обратной прокрутки
                for i in range(2):

                    # Обнуляем кошелек
                    for coin in self._wallet:
                        self._wallet[coin] = 0

                    # Переводим USD
                    self._wallet['USD'] = self._usd

                    # Закинем деньги на первую монету в пути
                    self._buy(list(pairs[pair_key].keys())[0], 'USD', self._wallet['USD'], False)

                    # Начинаем прокручивать
                    for j in range(self._rounds):
                        for key in pairs[pair_key]:
                            self._buy(pairs[pair_key][key], key, self._wallet[key])

                    # Обратно покупаем USD чтобы посмотреть результат
                    for key in self._wallet:
                        if key == 'USD' or self._wallet[key] <= 0: continue
                        self._buy('USD', key, self._wallet[key], False)

                    # Собираем результаты
                    diff = self._wallet['USD'] - self._usd
                    if diff <= 0: continue
                    key = pair_key if i < 1 else pair_key + '|REVERSE'
                    diff_list[key] = diff

                    # Разворачиваем путь и изменяем название для понимания
                    pairs[pair_key] = self._revers(pair_key)

            diff_list = dict(sorted(diff_list.items(), key=lambda item: item[1]))

            pprint(diff_list)

            await asyncio.sleep(self._ftx.update_time)

