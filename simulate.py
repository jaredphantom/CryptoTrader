import numpy, talib, trader, csv

#Configure as you wish
startCapital = 10000

#DO NOT TOUCH
prices = []
position = False
tempCapital = startCapital
buyPrice = 0
wins = 0
totalTrades = 0
change = 1
interval = 0
returnsPercent = []
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

#read file line by line
with open("tests/Binance_ETHUSDT_minute.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)
    next(reader)
    for data in reader:
        interval += 1

        #determine what interval to get prices from
        #file contains 1m candle data, so 'interval != 5' would emulate 5m candle data etc.
        #leave as 'interval != 1' for exact price data from file
        if interval != 1:
            continue

        interval = 0

        price = data[6]
        prices.append(float(price))

        if len(prices) > trader.periodLongMA:
            numpyCloses = numpy.array(prices)
            longMA = talib.EMA(numpyCloses, timeperiod=trader.periodLongMA)
            shortMA = talib.EMA(numpyCloses, timeperiod=trader.periodShortMA)
            rsi = talib.RSI(numpyCloses, trader.periodRSI)
            latestRSI = rsi[-1]

            #signal equation determines trading strategy, experiment with the values
            signal = shortMA[-1] - longMA[-1]

            if buyPrice != 0:
                change = ((float(price) - buyPrice) / buyPrice) + 1

            #again, experiment with the conditional statement values (within the brackets)
            if (signal > 0 and latestRSI < trader.oversold) and not position:
                buyPrice = float(price)
                position = True

            elif ((signal > 0 and latestRSI > trader.overbought) or (change < 0.9892 and (signal < 0 or latestRSI > trader.overbought))) and position:
                returnsPercent.append(percentChange(tempCapital, tempCapital * change * feeMultiplier))
                tempCapital = tempCapital * change * feeMultiplier
                if change > 1 + (1 - feeMultiplier):
                    wins += 1
                    consecutiveLosses = 0
                else:
                    consecutiveLosses += 1
                
                consecutiveLossesArray.append(consecutiveLosses)
                totalTrades += 1
                position = False

    firstPrice = prices[0]
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
        print(f"All Trade Returns: {returnsPercent}")
    if position:
        print(f"Currently Open Position: {percentChange(buyPrice, finalPrice)}%")
    print("----------------------------------------------------------------")
