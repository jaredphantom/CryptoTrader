import trader as t
import logging, threading

#connect to binance websocket and start trading
if __name__ == "__main__":
    logging.basicConfig(filename="logs/trader.log",
                        filemode="w",
                        format="%(asctime)s | %(levelname)s - %(message)s",
                        datefmt="%d %b %H:%M:%S",
                        level=logging.INFO)

    for coin in t.coins:
        print(coin)
        stream = t.Trader(coin, *t.getEnv())
        wst = threading.Thread(target=stream.listen)
        wst.start()
    
    print("")
