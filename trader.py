import json, numpy, talib, websocket, logging, math
from dotenv import dotenv_values
from binance import Client
from binance.enums import *

#technical indicators to determine entry/exit points
#RSI
periodRSI = 14
overbought = 66
oversold = 34

#EMA
periodShortMA = 20
periodLongMA = 50

#trade parameters
coins = ["ethusdt", "btcusdt", "adausdt"]

#globals
numPositions = 0

#Trader class contains all values needed to interact with binance api
class Trader:

    def __init__(self, ticker, api, secret):
        self._ticker = ticker
        self._socket = f"wss://stream.binance.com:9443/ws/{ticker.lower()}@kline_1m"
        self._client = Client(api_key=api, api_secret=secret)
        self._closes = []
        self._buyPrice = 0
        self._change = 0
        self._position = False

    #websocket functions
    def socketOpen(self, ws):
        logging.info(f"{self._ticker[:3].upper()} Connection opened")

    def socketClose(self, ws, *_):
        logging.info(f"{self._ticker[:3].upper()} Connection closed")
    
    def socketError(self, ws, error):
        logging.error(error)

    def socketMessage(self, ws, message):
        global numPositions
        cjson = json.loads(message)
        candle = cjson["k"]
        candleClosed = candle["x"]
        closePrice = candle["c"]

        if candleClosed:
            self._closes.append(float(closePrice))

            if len(self._closes) > periodLongMA:
                numpyCloses = numpy.array(self._closes)
                longMA = talib.EMA(numpyCloses, timeperiod=periodLongMA)
                shortMA = talib.EMA(numpyCloses, timeperiod=periodShortMA)
                rsi = talib.RSI(numpyCloses, periodRSI)
                latestRSI = rsi[-1]

                signal = shortMA[-1] - longMA[-1]

                if self._buyPrice != 0:
                    self._change = ((float(closePrice) - self._buyPrice) / self._buyPrice) + 1

                if (signal > 0 and latestRSI < oversold) and not self._position:
                    maxBuy = self.all_in(float(closePrice))
                    order = self.tryOrder(SIDE_BUY, maxBuy)

                    if order:
                        self._buyPrice = float(closePrice)
                        numPositions += 1
                        self._position = True

                elif ((signal > 0 and latestRSI > overbought) or (self._change < 0.9892 and (signal < 0 or latestRSI > overbought))) and self._position:
                    balance = self.getBalances()
                    order = self.tryOrder(SIDE_SELL, balance)

                    if order:
                        numPositions -= 1
                        self._position = False

    #stream websocket data
    def listen(self):
        while True:
            ws = websocket.WebSocketApp(self._socket, 
                                    on_open=self.socketOpen, 
                                    on_close=self.socketClose, 
                                    on_message=self.socketMessage, 
                                    on_error=self.socketError)
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
            if b["asset"] == self._ticker[:3].upper() and self._position:
                logging.info(b["asset"] + ": " + b["free"])
                return float(b["free"])
            elif b["asset"] == self._ticker[-4:].upper() and not self._position:
                logging.info(b["asset"] + ": " + b["free"])
                return float(b["free"])
            
    #calculate maximum purchase amount
    def all_in(self, price):
        balance = self.getBalances()
        buy = math.floor(balance) / math.ceil(price)
        assert(numPositions < len(coins))
        return round((1 / (len(coins) - numPositions)) * buy, 8)
                
#get sensitive data from environment file       
def getEnv():
    env = dotenv_values(".env")
    api = env["API_KEY"]
    secret = env["SECRET_KEY"]

    return api, secret
