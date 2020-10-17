import requests
import datetime
from datetime import date
import pymongo

import logging
import threading
import time

from tiingo import TiingoClient

import cProfile
import re


# IQfeed could be a good source for 100 dollar per month
# marketstack is 10 dollars per month and 10k request per month (sourced from tiingo)
# https://eodhistoricaldata.com/ 20 permonth. Can basically get 10k from API as well
# online people say its sourced from yahoo finance

# make sure to check for old tickers first

# the api has a column field that lowers the amount of response data


# Takes one ticker and a daterange and calls the Tiingo API
# Returns a dictionary with date as the key and adjusted close
# as the value for the inputted daterange

def genTiingoDict(ticker: str, sDate, eDate):

    token = "&token=a6051dc9e9d1140d8322de2b99755165d84f9671"


    reqBody = "https://api.tiingo.com/tiingo/daily/"+ticker+'/prices?startDate='
    reqBody = reqBody +sDate+ '&endDate=' + eDate+token+"&columns=close"

    headers = {
        'Content-Type': 'application/json'
    }
    requestResponse = requests.get(reqBody, headers=headers)

    pData = requestResponse.json()

    stock_Dict = {}
    closeDict = {}

    for currDay in pData:

        in_date = currDay['date']

        # set date key to be a date object
        in_date = date(int(in_date[0:4]),int(in_date[5:7]),int(in_date[8:10]))
        stock_Dict[in_date] = currDay['close']

        # push to db with key as a date string
        closeDict[currDay['date'][0:10]]= currDay['close']

        # also save close price to database


    return (stock_Dict,closeDict)

# sDate and eDate are of type Datetime
def getStockDict(stockSet: set,sDate,eDate):

    sDate = sDate.isoformat()
    eDate = eDate.isoformat()

    stock_dict = {}
    dbDict = {}

    counter = 1
    for stock in stockSet:
        out = genTiingoDict(stock,sDate,eDate)
        stock_dict[stock] = out[0]
        dbDict[stock] = out[1]
        print(f"Tiingo Call {counter} completed.")
        counter +=1


    return stock_dict


# using the library is waay faster. Probably because only 1 auth is needed
# bad part of the library is that it sends everything and we may just want close
def tiingoMulti(stockList,sDate,eDate):

    # needs a list of tickers, a startdate, and an end date
    # that list should be a dictionary
    # that holds the first buy and last sell date

    #sDate and eDate should be converted into iso here

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

    # Initialize
    client = TiingoClient(config)


    threads = list()
    stockDictOut = {}

    for index,stock in enumerate(stockList):
        print("Main    : create and start thread %d.", index)
        x = threading.Thread(target=thread_function, args=(index,client,stock,))
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        thread.join()

    return stockDictOut
