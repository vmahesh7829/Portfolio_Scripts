import datetime
import pandas as pd
import threading
from tiingo import TiingoClient
import yfinance as yf

def yfDfToDict(stockDf):
    out = dict()

    for ind in stockDf.index:

        # create a dict with days info EOD info
        # make sure to match the keys of this to tiingo
        inDict = dict()
        inDict['close'] = stockDf['Close'][ind]
        inDict['divCash'] = stockDf['Dividends'][ind]
        inDict['splitFactor'] = stockDf['Stock Splits'][ind]

        # convert ind from pandasTimestamp to datetime.dateTime
        ind = str(ind.date())
        ind = ind.split('-')
        ind = datetime.datetime( int(ind[0]) , int(ind[1]), int(ind[2]))

        # add that day to the output
        out[ind] = inDict

    return out

# later this should take sDate and eDate
def getPricesOfThreeForeignStocks(sDate,eDate):
    out = dict()
    # yfinance takes dates as an iso string
    sDate = sDate.date().isoformat()
    eDate = eDate.date().isoformat()

    # foreign tickers in Yahoo Finance format
    tickList = ["NLAB.ST","AIR.PA","APT.AX"]
    for ticker in tickList:
        newStock = yf.Ticker(ticker)
        newStock = newStock.history(start=sDate, end=eDate)
        newStock = yfDfToDict(newStock)
        out[ticker] = newStock

    return out



# USAGE:
# stockList is a list of tickers
# sDate and eDate are iso format strings for tiingoMulti
# for tiingoListAllData they are datetime.datetime objects
# this outputs a dictionary with ticker as a key
# value is a dictionary with key date val price

# also have this output a list of trading days
# I want to change so that stockList is a tuplewith (ticker,sDate,eDate)
# 2016-05-16 2020-07-30

def tiingoMulti(stockList,sDate,eDate):

    # thread function spawns a thread that gets data for a stock
    def thread_function(name,client,stock):
        historical_prices = client.get_ticker_price(stock,
                                                fmt='json',
                                                startDate=sDate,
                                                endDate=eDate,
                                                frequency='daily')

        closeDict = {}
        for currDay in historical_prices:

            in_date = currDay['date']

            # set date key to be a date object
            in_date = date(int(in_date[0:4]),int(in_date[5:7]),int(in_date[8:10]))
            closeDict[in_date] = currDay['close']

        nonlocal stockDictOut
        stockDictOut[stock] = closeDict

        print("Call %s: finished", name)

    config = {}

    # To reuse the same HTTP Session across API calls (and have better performance), include a session key.
    config['session'] = True

    # If you don't have your API key as an environment variable,
    # pass it in via a configuration dictionary.
    config['api_key'] = "a6051dc9e9d1140d8322de2b99755165d84f9671"

    # client is the connection to Tiingo
    client = TiingoClient(config)


    threads = list()
    stockDictOut = {}
    dateList = []

    # open a thread that adds apple to the stockdict
    # populate dateList with the apple trading days in order

    # make concurrent calls to Tiingo API to get stock prices
    for index,stock in enumerate(stockList):
        print("Main    : create and start thread %d.", index)
        x = threading.Thread(target=thread_function, args=(index,client,stock,))
        threads.append(x)
        x.start()

    # close up the threads
    for index, thread in enumerate(threads):
        thread.join()

    return stockDictOut

# get all the data tiingo provides
def tiingoListAllData(stockList,sDate,eDate):

    # thread function spawns a thread that gets data for a stock
    def thread_function(name,client,stock):
        historical_prices = client.get_ticker_price(stock,
                                                fmt='json',
                                                startDate=sDate,
                                                endDate=eDate,
                                                frequency='daily')

        closeDict = {}
        for currDay in historical_prices:
            in_date = currDay['date']
            # set date key to be a date object
            in_date = datetime.datetime(int(in_date[0:4]),int(in_date[5:7]),int(in_date[8:10]))
            closeDict[in_date] = currDay

        # add the dictionary for this ticker to the dictionary of tickers
        nonlocal stockDictOut
        stockDictOut[stock] = closeDict
        print("Call %s: finished", name)

    # Create a connection via TiingoClient
    config = {}
    # To reuse the same HTTP Session across API calls (and have better performance), include a session key.
    config['session'] = True
    # If you don't have your API key as an environment variable,
    # pass it in via a configuration dictionary.
    config['api_key'] = "a6051dc9e9d1140d8322de2b99755165d84f9671"
    # client is the connection to Tiingo
    client = TiingoClient(config)
    threads = list()
    stockDictOut = {}
    dateList = []

    # Convert datetime to a date iso String
    sDate = sDate.date().isoformat()
    eDate = eDate.date().isoformat()

    # make concurrent calls to Tiingo API to get stock prices
    for index,stock in enumerate(stockList):
        print("Main    : create and start thread %d.", index)
        x = threading.Thread(target=thread_function, args=(index,client,stock,))
        threads.append(x)
        x.start()

    # close up the threads
    for index, thread in enumerate(threads):
        thread.join()

    return stockDictOut
