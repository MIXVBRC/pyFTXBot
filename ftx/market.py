
class Market:

    @property
    def name(self):
        return self._name

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

        result = self.price * size
        if buy == self._quote_currency:
            result = self.price * (1 / size)

        if result < self._min_size:
            return False

        return result