import json, websocket, logging

#farm parameters
coins = ["ethusdt"]

#websocket functions
def socketOpen(ws):
    logging.info("Connection opened")

def socketClose(ws, *_):
    logging.info("Connection closed")
    
def socketError(ws, error):
    logging.error(error)

def socketMessage(ws, message):
    cjson = json.loads(message)
    candle = cjson["k"]
    candleClosed = candle["x"]
    closePrice = candle["c"]
    highPrice = candle["h"]
    lowPrice = candle["l"]
    volume = candle["v"]

    if candleClosed:
        with open("tests/ethdata.txt", "a") as f:
            f.write(f"{closePrice},{highPrice},{lowPrice},{volume}\n")

#Farmer class contains all values needed to interact with binance api
class Farmer:

    def __init__(self, ticker):
        self._socket = f"wss://stream.binance.com:9443/ws/{ticker.lower()}@kline_1m"

    #stream websocket data
    def listen(self):
        while True:
            ws = websocket.WebSocketApp(self._socket, 
                                    on_open=socketOpen, 
                                    on_close=socketClose, 
                                    on_message=socketMessage, 
                                    on_error=socketError)
            ws.run_forever()

#connect to binance websocket and start farming
if __name__ == "__main__":
    logging.basicConfig(filename="logs/farmer.log", 
                        filemode="w", 
                        format="%(asctime)s | %(levelname)s - %(message)s", 
                        datefmt="%d %b %H:%M:%S", 
                        level=logging.INFO)

    farmer = Farmer(coins[0])
    farmer.listen()