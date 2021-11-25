# Binance Crypto Trading Bot

**Change constants as required before running, e.g. changing short and long MA periods to suit your strategy**

**coin array in trader.py contains all the symbols that will be monitored, coinpairs must be in 'xxxUSDT' format**

**Run main.py to start trading, trader.py contains the Trader class with attributes and methods required to interact with Binance API, farm.py will collect data to be used for backtesting with simulate.py**

**Create a folder in the directory called logs and a folder called tests to contain output logs and test data respectively**

**You must set up your own API key from the Binance site, create a .env file with your API and secret key for the bot to fetch**

**All dependencies are in requirements.txt however TA-Lib may need manual installation as sometimes there are errors**
```
> pip install -r requirements.txt 
```
