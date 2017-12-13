#planned apis:
#Bitstamp, Kraken, Bitfinex, Bittrex, Binance
import abc
import logging

import sys

import time
import traceback

from btfxwss import BtfxWss
from bittrex import Bittrex
import krakenex
import fileinput
import bitstamp.client
from binance.client import Client


currency_replacelist = dict({"XXBT" : "BTC", "XXRP" : "XRP", "XETH" : "ETH"," ZEUR" : "EUR", "XZEC" : "ZEC", "XXMR" : "XMR"})

class QueryInterface(object, metaclass=abc.ABCMeta):
    def __init__(self, key, secret, extradata=''):
        self.key = key
        self.secret = secret
        self.extra = extradata

    @abc.abstractmethod
    def getBalances(self):
        """Abstract method to return a list of balances on the currect exchange

        Returns a dict of currency-value tuples (("BTC", 1.1), ("ETH", 9.6))
        """
        raise NotImplementedError('getBalances not implemented')


class DummyService(QueryInterface):
    def getBalances(self):
        return (("BTC", 1.1), ("ETH", 9.6))

class KrakenService(QueryInterface):
    def getBalances(self):
        k = krakenex.API(key=self.key, secret=self.secret)
        resp = k.query_private("Balance")

        logging.debug(resp['result'])
        return resp['result']



class BitstampService(QueryInterface):
    def getBalances(self):
        balance = dict()
        trading_client = bitstamp.client.Trading(username = self.extra, key = self.key, secret = self.secret)

        resp = trading_client.account_balance(quote="EUR")
        self.parseResponse(resp, balance)
        logging.debug(balance)

        resp = trading_client.account_balance(quote="USD")
        self.parseResponse(resp, balance)
        logging.debug(balance)


        return balance

    def parseResponse(self, resp, balance):
        for key in resp.keys():
            key = str(key)

            if key.endswith("balance"):
                cur = key.split("_")[0]
                value = resp[key]

                if cur not in balance:
                    balance[cur] = value

class BitfinexService(QueryInterface):
    def getBalances(self):
        bf = BtfxWss(key=self.key, secret=self.secret)
        bf.start()

        while not bf.conn.connected.is_set():
            time.sleep(1)

        bf.authenticate()
        time.sleep(1)

        resp = bf.wallets
        timeout = time.time() + 10
        while resp.qsize == 0 or time.time() <= timeout:
            time.sleep(1)

        bf.stop()


        l = list()
        while resp.qsize() > 0:
            l.append(resp.get())

        logging.debug(l)
        #logging.info(l[0][0][1])

        balance = dict()
        if len(l) == 0:
            return balance

        for entry in l[0][0][1]:
            #[['funding', 'IOT', 0.00471435, 0, None], ['exchange', 'ETH', 0, 0, None], ['exchange', 'IOT', 408.54209381, 0, None], ['exchange', 'BTC', 0, 0, None]]
            cur = entry[1]
            value = entry[2]

            if cur not in balance:
                balance[cur] = 0.0
            balance[cur] += value


        return balance

class BittrexService(QueryInterface):
    def getBalances(self):
        bittrex = Bittrex(api_key=self.key, api_secret=self.secret)
        resp = bittrex.get_balances()

        balance = dict()
        for entry in resp['result']:
            cur = entry['Currency']
            value = entry['Balance']

            if cur not in balance:
                balance[cur] = 0.0
            balance[cur] += value

        logging.debug(resp)

        return balance

class BinanceService(QueryInterface):
    def getBalances(self):
        client = Client(api_key=self.key, api_secret=self.secret)
        resp = client.get_account()['balances']
        logging.debug(resp)

        balance = dict()
        for entry in resp:
            cur = entry['asset']
            value = entry['free']

            #filter
            if float(value) > 0:
                balance[cur] = value

        return balance


class CoinbaseService(QueryInterface):
    def getBalances(self):
        #TODO: ADD COINBASE
        pass


def parseKeys(file):
    creds = list()
    for line in fileinput.input(file):
        line = line.strip()

        if line.startswith("#") or line == "":
            continue

        split = line.split(";")
        logging.debug(split)
        creds.append(split)

    return creds

def parseCreds(creds):
    exchangeServices = list()

    for cred in creds:
        assert len(cred) >= 3
        # Still missing switch case in python
        ex_name = cred[0]


        # Bitstamp, Kraken, Bitfinex, Bittrex, Binance, Bitpanda?
        if ex_name == "bitstamp":
            exchangeServices.append((BitstampService(cred[1], cred[2], cred[3]), ex_name))

        elif ex_name == "kraken":
            exchangeServices.append((KrakenService(cred[1], cred[2]), ex_name))

        elif ex_name == "bitfinex":
            exchangeServices.append((BitfinexService(cred[1], cred[2]), ex_name))

        elif ex_name == "bittrex":
            exchangeServices.append((BittrexService(cred[1], cred[2]), ex_name))

        elif ex_name == "binance":
            exchangeServices.append((BinanceService(cred[1], cred[2]), ex_name))

        elif ex_name == "coinbase":
            exchangeServices.append((CoinbaseService(cred[1], cred[2]), ex_name))

    return exchangeServices

def printInfo():
    pass

def normalizeCurrencys(balances):
    final_balances = dict()

    for bal_list in balances:
        for key in bal_list:
            value = float(bal_list[key])

            #key normalizing
            key = key.upper()

            if key in currency_replacelist:
                key = currency_replacelist[key]

            if key not in final_balances:
                final_balances[key] = 0.0

            final_balances[key] += value

    return final_balances

def main():
    logging.basicConfig(filename='balances.log', level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    logging.info("Crypto Balance Script by GoneUp")
    
    creds = parseKeys("keys")
    logging.info("Loaded {} key entrys".format(len(creds)))

    services = parseCreds(creds)
    logging.info("Parsed {} valid key entrys".format(len(services)))

    logging.info("Querying...")
    balances = list()

    for service in services:
        s = service[0]

        try:
            bal = s.getBalances()
            balances.append(bal)
            logging.info("Balance of {}: {}".format(service[1], bal))

        except Exception as err:
            logging.error("Error while querying {}: {}".format(s, err))
            traceback.print_tb(err.__traceback__)

    logging.info("Normalizing..")
    norm_balances = normalizeCurrencys(balances)
    logging.info("Total:")
    for bal in norm_balances:
        logging.info("Currency: {}, Value: {:0.4f}".format(bal, norm_balances[bal]))

if __name__ == '__main__':
    main()



