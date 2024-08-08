import json

import pandas

BASE_PATH = '../../data/stocks/'


class StockData:
    def __init__(self, init_ticker="DEA"):
        """
        StockData loads stock data from files created by YahooStock

        :param init_ticker: the ticker symbol of a publicly traded stock
        """
        self.ticker = init_ticker
        try:
            text_file = open(BASE_PATH + self.ticker + '.json', 'r')
            self.text_string = text_file.read()
            text_file.close()
            self.text_string = self.text_string.replace('\n', '')
            self.json_data = json.loads(self.text_string)
            prices_a = self.json_data[self.ticker]['prices']
            these_prices = []
            for price in prices_a:
                these_prices.append(price)
            self.price_frame = pandas.DataFrame(these_prices)
            self.data_frame = self.price_frame.to_numpy()
        except FileNotFoundError:
            print('Stock data file not found: ' + BASE_PATH + self.ticker + '.json')


def test_init():
    stock_data = StockData('CVS')
    print('test_init done!')


if __name__ == '__main__':
    test_init()
