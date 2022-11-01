import sys

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
        self._logger = False

    def commission(self, value):
        return value - (value / 100 * self._commission)

    def _buy(self, buy, sell, pay, commission=True, change=True):

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
        if change is True:
            buy_finish = buy_result - buy_remainder
        else:
            buy_finish = buy_result

        # Здача, возвращаем остаток кратности
        sell_finish = buy_finish * self._ftx.price_list[reverse_transfer]

        # Вычетаем комиссию
        if commission is True:
            buy_finish = self.commission(buy_finish)

        # Принт для понимания че происходит
        if self._logger is True:
            print(f'{sell}({self._wallet[sell]}) -> {buy}({self._wallet[buy]}) = {pay} * {self._ftx.price_list[transfer]} = {buy_finish} [{buy_remainder}]')

        # Совершаем перевод
        self._wallet[buy] += buy_finish
        self._wallet[sell] -= sell_finish

        return True

    def _revers(self, pair_key):
        return self._ftx.pairs_reverse[pair_key]

    def calc(self):
        pairs = self._ftx.pairs
        diff_list = {}
        for pair_key in pairs:

            # Данный for для обратной прокрутки
            for i in range(2):

                # Разворачиваем путь и изменяем название для понимания
                key = pair_key
                pair = pairs[pair_key]
                if i < 1:
                    key = pair_key + '|REVERSE'
                    pair = self._revers(pair_key)

                # Обнуляем кошелек
                for coin in self._wallet:
                    self._wallet[coin] = 0

                # Переводим USD
                self._wallet['USD'] = self._usd

                # Вычисляем итоговую разницу
                diff = self.diff_calc(pair)

                if diff is False: continue
                if diff <= 0: continue

                diff_list[key] = diff

        return dict(sorted(diff_list.items(), key=lambda item: item[1]))

    def diff_calc(self, pair):

        # Закинем деньги на первую монету в пути
        self._logger = True
        result = self._buy(list(pair.keys())[0], 'USD', self._wallet['USD'], False)
        self._logger = False
        if result is False: return False

        # Начинаем прокручивать
        for j in range(self._rounds):
            if j <= 1: self._logger = True
            for key in pair:
                result = self._buy(pair[key], key, self._wallet[key])
                if result is False: return False
            if self._logger is True:
                print('-'*50)
            self._logger = False

        # Обратно покупаем USD чтобы посмотреть результат
        for key in self._wallet:
            if key == 'USD' or self._wallet[key] <= 0: continue
            self._buy('USD', key, self._wallet[key], False)

        # Собираем результаты
        return self._wallet['USD'] - self._usd