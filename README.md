## Crypto Exchange Balance Script

A simple script that provides you an overview where your cryptocurrencys are located.

Supported Exchanges:
- Coinbase
- Bitstamp
- Kraken
- Bitfinex
- Bittrex
- Binance

### Usage
Install the following dependecies:
```
pip install btfxwss
pip install krakenex
pip install BitstampClient
pip install git+https://github.com/ericsomdahl/python-bittrex.git
pip install python-binance
pip install coinbase
```
Insert your API-Keys formatted as csv (see the keys.example) into a keys file in the folder of your script.
The api keys need read access to the account/balances for the script to function.

Then just run it with:
```
python ex_balance.py
```


### Development
Tested on Python 3.5.1 and PyCharm 2017.3


### Tips
```
Error while querying <__main__.BinanceService object at 0x0000000004278D68>: APIError(code=-1021): Timestamp for this request is outside of the recvWindow.
```
If you get this error you should try to sync your local computer time or wider the recvWindow on the binance api settings.


