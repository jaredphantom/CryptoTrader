import numpy, talib, trader, csv
import matplotlib.pyplot as plt

#Configure as you wish
startCapital = 10000

#DO NOT TOUCH
prices = []
allPrices = []
highs = []
lows = []
volumes = []
equityCurve = [startCapital]
buyHold = [startCapital]
position = False
tempCapital = startCapital
buyPrice = 0
wins = 0
totalTrades = 0
change = 1
interval = 0
returnsPercent = []
riskAversion = 0
consecutiveLosses = 0
consecutiveLossesArray = []
feeMultiplier = 0.99925

#util functions
def percentChange(initial, final):
    num = ((final - initial) / initial) * 100
    return clean(num)

def clean(num):
    rounded = round(num, 2)
    if rounded == int(num):
        return int(num)
    return rounded

def strictly_increasing(L):
    return all(x < y for x, y in zip(L, L[1:]))

def strictly_decreasing(L):
    return all(x > y for x, y in zip(L, L[1:]))

#strategy function
def strategy(prices, adx, ema, rsi, risk, change):
    #bearish
    if strictly_decreasing(prices[-3:]) and rsi >= 70:
        return -1 #sell
        
    #bullish
    elif strictly_increasing(prices[-3:]) and rsi <= 30:
        return 1 #buy
    
    return 0 #hold

#read file line by line
#with open("tests/Binance_ETHUSDT_Minute.csv", "r") as f:
#with open("tests/Bitstamp_BTCUSD_2021_minute.csv", "r") as f:
with open("tests/ethdata.csv", "r") as f:
    reader = csv.DictReader(f)
    for data in reader:
        interval += 1

        #determine what interval to get prices from
        #file contains 1m candle data, so 'interval != 5' would emulate 5m candle data etc.
        #leave as 'interval != 1' for exact price data from file
        if interval != 1:
            continue

        interval = 0

        price = data["close"]
        high = data["high"]
        low = data["low"]

        try:
            volume = data["Volume USDT"]
        except KeyError:
            volume = data["Volume USD"]

        try:
            float(price)
            float(high)
            float(low)
            float(volume)
        except ValueError:
            break

        prices.append(float(price))
        highs.append(float(high))
        lows.append(float(low))
        volumes.append(float(volume))
        allPrices.append(float(price))
        buyHold.append(startCapital * (((float(price) - allPrices[0]) / allPrices[0]) + 1))

        #starts to simulate trades after adequate quantity of price data obtained, uses sliding window for efficiency by deleting oldest data
        if len(prices) > 300:
            del prices[0]
            del highs[0]
            del lows[0]
            del volumes[0] 

            numpyCloses = numpy.array(prices)
            numpyHighs = numpy.array(highs)
            numpyLows = numpy.array(lows)
            numpyVolumes = numpy.array(volumes)

            longMA = talib.DEMA(numpyCloses, timeperiod=trader.periodLongMA)
            shortMA = talib.DEMA(numpyCloses, timeperiod=trader.periodShortMA)

            rsi = talib.RSI(numpyCloses, trader.periodRSI)
            latestRSI = rsi[-1]
            mfi = talib.MFI(numpyHighs, numpyLows, numpyCloses, numpyVolumes, timeperiod=14)
            latestMFI = mfi[-1]
            adx = talib.ADX(numpyHighs, numpyLows, numpyCloses, timeperiod=14)
            latestADX = adx[-1]

            ema = shortMA[-1] - longMA[-1]

            if buyPrice != 0:
                change = ((float(price) - buyPrice) / buyPrice) + 1

            if riskAversion < 0:
                riskAversion = 0
            
            if riskAversion > 2:
                riskAversion = 2

            if (latestADX > 25 and strategy(prices, adx, ema, latestRSI, riskAversion, change) == 1 and consecutiveLosses < 4) and not position:
                buyPrice = float(price)
                position = True

            elif ((change > 1.1 or change < 0.9)) and position:
                returnsPercent.append(percentChange(tempCapital, tempCapital * change * feeMultiplier))
                tempCapital = tempCapital * change * feeMultiplier
                print(tempCapital)
                equityCurve.append(tempCapital)
                if change > 1 + (1 - feeMultiplier):
                    wins += 1
                    consecutiveLosses = 0
                    riskAversion -= 1
                else:
                    consecutiveLosses += 1
                    riskAversion += 1
                
                consecutiveLossesArray.append(consecutiveLosses)
                totalTrades += 1
                position = False

    firstPrice = allPrices[0]
    finalPrice = prices[-1]

    #output test results for easy viewing and comparison
    print("----------------------------------------------------------------")
    print(f"Starting Capital: ${startCapital}")
    print(f"Final Capital: ${clean(tempCapital)}")
    print(f"\nPercentage P/L: {percentChange(startCapital, tempCapital)}%")
    print(f"Price Change: {percentChange(firstPrice, finalPrice)}%")
    print(f"\nTotal Trades: {totalTrades}")
    if totalTrades > 0:
        print(f"Best Trade: {max(returnsPercent)}%")
        print(f"Worst Trade: {min(returnsPercent)}%")
        print(f"Most Consecutive Losses: {max(consecutiveLossesArray)}")
        print(f"Win Rate: {clean((wins / totalTrades) * 100)}%")
        #print(f"All Trade Returns: {returnsPercent}")
    if position:
        print(f"Currently Open Position: {percentChange(buyPrice, finalPrice)}%")
    print("----------------------------------------------------------------")

    #plot graphs for equity curves with trading strategy (blue) vs buy and hold strategy (red)
    ypoints = numpy.array(equityCurve)
    ypointsControl = numpy.array(buyHold)
    plt.subplot(2, 1, 1)
    plt.plot(ypoints)
    plt.subplot(2, 1, 2)
    plt.plot(ypointsControl, color="r")
    plt.show()
