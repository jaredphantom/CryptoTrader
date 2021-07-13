# Binance Crypto Trading Bot

**Change parameters as required before running, e.g. changing short and long MA periods to suit your strategy**

**crossMA and openPosition must be configured manually before running, if short MA is above long MA then crossMA must be changed to True, and if you currently have an open position on your desired coin pair then openPosition must be changed to True**

**Calculated RSI values will be slightly inaccurate for the first hour or so of running due to a lack of price data**

**You must set up your own API key from the Binance site, create a .env file with your API and secret key for the bot to fetch**

**All dependencies are in requirements.txt**
```
> pip install -r requirements.txt 
```
