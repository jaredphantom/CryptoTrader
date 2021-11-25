import json, numpy, talib, websocket, logging, requests
from discord import Webhook, RequestsWebhookAdapter
from dotenv import dotenv_values
from binance import Client
from binance.enums import *

#technical indicators to determine entry/exit points
#RSI
periodRSI = 14
overbought = 70
oversold = 30

#EMA
periodShortMA = 9
periodLongMA = 21

#trade parameters
coins = ["dydxusdt", "enjusdt"]
slippage = 0.99

#globals
numPositions = len(coins)
losses = 0
webhook = Webhook.from_url(
    "https://discordapp.com/api/webhooks/904783821604524053/7YJpzN9ZH1jUSjk-O5Gb7Bia4Xs3Qx-TzIO2pBO9r0iVL0_Ic_usbb9NxEE4peUqJFvH", 
    adapter=RequestsWebhookAdapter())

#util functions
def strictly_increasing(L):
    return all(x < y for x, y in zip(L, L[1:]))

def truncate(num, n):
    integer = int(num * (10**n))/(10**n)
    return float(integer)

def stepSize(str):
    return str.find("1") - str.find(".")

def checkBigger(a, b, msg):
    try:
        assert(a > b)
        return True
    except AssertionError:
        logging.error(msg)
    return False

#Trader class contains all values needed to interact with binance api
class Trader:

    def __init__(self, ticker, api, secret):
        self._ticker = ticker
        self._socket = f"wss://stream.binance.com:9443/ws/{ticker.lower()}@kline_5m"
        self._client = Client(api_key=api, api_secret=secret)
        self._closes = []
        self._buyPrice = 0
        self._change = 0
        self._position = True
        self._stepSize = 0

    #websocket functions
    def socketOpen(self, ws):
        global numPositions
        self._stepSize = stepSize(self._client.get_symbol_info(self._ticker.upper())['filters'][2]['stepSize'])
        if checkBigger(self.getMinQty(), self.getBalances(), f"Position already open for {self._ticker.upper()}"):
            numPositions -= 1
            self._position = False
        logging.info(f"{self._ticker[:-4].upper()} Connection opened")

    def socketClose(self, ws, *_):
        logging.info(f"{self._ticker[:-4].upper()} Connection closed")
    
    def socketError(self, ws, error):
        logging.error(error)

    def socketMessage(self, ws, message):
        global numPositions, losses
        cjson = json.loads(message)
        candle = cjson["k"]
        candleClosed = candle["x"]
        closePrice = candle["c"]

        if candleClosed:
            print(f"{self._ticker[:-4].upper()}: {closePrice}\n")
            self._closes.append(float(closePrice))

            if len(self._closes) > periodLongMA:
                numpyCloses = numpy.array(self._closes)
                rsi = talib.RSI(numpyCloses, periodRSI)
                latestRSI = rsi[-1]
                longMA = talib.EMA(numpyCloses, timeperiod=periodLongMA)
                shortMA = talib.EMA(numpyCloses, timeperiod=periodShortMA)

                def MAcross(long, short):
                    if long[-1] > short[-1] and long[-2] < short[-2]:
                        return -1 #short MA cross below long MA (sell signal)
                    elif long[-1] < short[-1] and long[-2] > short[-2]:
                        return 1 #short MA cross over long MA (buy signal)
                    return 0

                if self._buyPrice != 0:
                    self._change = ((float(closePrice) - self._buyPrice) / self._buyPrice) + 1

                if (MAcross(longMA, shortMA) == 1 and latestRSI > (overbought + oversold) / 2 and losses < 4) and not self._position:
                    maxBuy = self.all_in(float(closePrice))
                    logging.info(f"Attempt to buy {self._ticker[:-4].upper()}: {maxBuy}")
                    if checkBigger(maxBuy, self.getMinQty(), "Maximum purchase amount below minimum quantity"):
                        order = self.tryOrder(SIDE_BUY, maxBuy)

                        if order:
                            webhook.send(f"Buy {self._ticker[:-4].upper()} @ ${closePrice}")
                            self._buyPrice = float(closePrice)
                            numPositions += 1
                            self._position = True

                elif (MAcross(longMA, shortMA) == -1) and self._position:
                    balance = truncate(self.getBalances(), self._stepSize)
                    logging.info(f"Attempt to sell {self._ticker[:-4].upper()}: {balance}")
                    order = self.tryOrder(SIDE_SELL, balance)

                    if order:
                        webhook.send(f"Sell {self._ticker[:-4].upper()} @ ${closePrice}: {(self._change - 1) * 100}% P/L")
                        self._buyPrice = 0
                        numPositions -= 1
                        self._position = False
                        if self._change <= 1:
                            losses += 1
                        else:
                            losses = 0

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

    #get minimum trade quantity for ticker
    def getMinQty(self):
        info = self._client.get_symbol_info(self._ticker.upper())
        return float(info['filters'][2]['minQty'])

    #get wallet balances for relevant tickers
    def getBalances(self):
        account = self._client.get_account()
        balances = account["balances"]

        for b in balances:
            if b["asset"] == self._ticker[:-4].upper() and self._position:
                return float(b["free"])
            elif b["asset"] == self._ticker[-4:].upper() and not self._position:
                return float(b["free"])
            
    #calculate maximum purchase amount
    def all_in(self, price):
        balance = self.getBalances()
        buy = balance / price
        if checkBigger(len(coins), numPositions, "Maximum open positions already reached"):
            return truncate((1 / (len(coins) - numPositions)) * buy * slippage, 1)
        return 0
                
#get sensitive data from environment file       
def getEnv():
    env = dotenv_values(".env")
    api = env["API_KEY"]
    secret = env["SECRET_KEY"]

    return api, secret
