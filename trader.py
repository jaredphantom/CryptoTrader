import json, numpy, talib, websocket, logging, math
from dotenv import dotenv_values
from binance import Client
from binance.enums import *

#technical indicators to determine entry/exit points
#RSI
periodRSI = 14
overbought = 70
oversold = 30

#SMA
periodShortMA = 20
periodLongMA = 50
crossMA = False

#trade parameters
coins = ["ethusdt", "bnbusdt", "btcusdt"]

#globals
closePrices = []
openPosition = False

#websocket functions
def socketOpen(ws):
    logging.info("Connection opened")
    trader.getBalances()

def socketClose(ws):
    logging.info("Connection closed")
    
def socketError(ws, error):
    logging.error(error)

def socketMessage(ws, message):
    global openPosition, closePrices, crossMA
    cjson = json.loads(message)
    candle = cjson["k"]
    candleClosed = candle["x"]
    closePrice = candle["c"]

    if candleClosed:
        closePrices.append(float(closePrice))
        
        if len(closePrices) > periodLongMA:
            numpyCloses = numpy.array(closePrices)
            longMA = talib.SMA(numpyCloses, timeperiod=periodLongMA)
            shortMA = talib.SMA(numpyCloses, timeperiod=periodShortMA)
            logging.info(str(periodLongMA) + "MA: " + str(longMA[-1]))
            logging.info(str(periodShortMA) + "MA: " + str(shortMA[-1]))

            if shortMA[-1] > longMA[-1]:
                if not crossMA:
                    crossMA = True
                    logging.info("Short-term MA crossed over the long-term MA")

                    if not openPosition:
                        maxBuy = trader.all_in(float(closePrice))
                        order = trader.tryOrder(SIDE_BUY, maxBuy)

                        if order:
                            openPosition = True
            
            if shortMA[-1] < longMA[-1]:
                if crossMA:
                    crossMA = False
                    logging.info("Short-term MA crossed below the long-term MA")

                    if openPosition:
                        balance = trader.getBalances()
                        order = trader.tryOrder(SIDE_SELL, balance)

                        if order:
                            openPosition = False
        
        if len(closePrices) > periodRSI:
            numpyCloses = numpy.array(closePrices)
            rsi = talib.RSI(numpyCloses, periodRSI)
            latestRSI = rsi[-1]
            logging.info("RSI: " + str(latestRSI))

            if latestRSI > overbought:
                logging.info("Asset is overbought")

                if openPosition:
                    balance = trader.getBalances()
                    order = trader.tryOrder(SIDE_SELL, balance)

                    if order:
                        openPosition = False

            if latestRSI < oversold:
                logging.info("Asset is oversold")

                if not openPosition:
                    maxBuy = trader.all_in(float(closePrice))
                    order = trader.tryOrder(SIDE_BUY, maxBuy)

                    if order:
                        openPosition = True

#Trader class contains all values needed to interact with binance api
class Trader:

    def __init__(self, ticker, api, secret):
        self._ticker = ticker
        self._api = api
        self._secret = secret
        self._socket = f"wss://stream.binance.com:9443/ws/{ticker.lower()}@kline_1m"
        self._client = Client(api_key=api, api_secret=secret)

    #stream websocket data
    def listen(self):
        ws = websocket.WebSocketApp(self._socket, 
                                    on_open=socketOpen, 
                                    on_close=socketClose, 
                                    on_message=socketMessage, 
                                    on_error=socketError)
        ws.run_forever()

    #attempts to do a buy/sell order
    def tryOrder(self, side, amount, order_type=ORDER_TYPE_MARKET):
        try:
            order = self._client.create_order(symbol=self._ticker.upper(), side=side, type=order_type, quantity=amount)
            logging.info(order)
        except Exception as e:
            logging.error(e)
            return False

        return True

    #get wallet balances for relevant tickers
    def getBalances(self):
        account = self._client.get_account()
        balances = account["balances"]

        for b in balances:
            if b["asset"] == self._ticker[:3].upper() and openPosition:
                logging.info(b["asset"] + ": " + b["free"])
                return float(b["free"])
            elif b["asset"] == self._ticker[-4:].upper() and not openPosition:
                logging.info(b["asset"] + ": " + b["free"])
                return float(b["free"])
            
    #calculate maximum purchase amount
    def all_in(self, price):
        balance = self.getBalances()
        return round(math.floor(balance) / math.ceil(price), 8)
                
#get sensitive data from environment file       
def getEnv():
    env = dotenv_values(".env")
    api = env["API_KEY"]
    secret = env["SECRET_KEY"]

    return api, secret

#connect to binance websocket and start trading
if __name__ == "__main__":
    logging.basicConfig(filename="data.log", 
                        filemode="w", 
                        format="%(asctime)s | %(levelname)s - %(message)s", 
                        datefmt="%d %b %H:%M:%S", 
                        level=logging.INFO)

    trader = Trader(coins[0], *getEnv())
    trader.listen()