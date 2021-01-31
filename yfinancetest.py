import yfinance as yf
import pandas as pd
import datetime

# turn the yFinance dataFrame into the same format as tiingoListAllData output
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
