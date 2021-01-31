__author__ = 'gianluca and vish'

# TODO:

# check tiingo call (probably have to use eDate.date() in api_pulls)
# match foreign keys to tiingo keys

from api_pulls import *
from parseIBKR import printActivityLedger
from yfinancetest import *
import time

def GetStockHashMulti(all_stocks,sDate,eDate):

    if (eDate.year == date.today().year):
        eDate = date.today()

    sDate = sDate.isoformat()
    eDate = eDate.isoformat()

    return tiingoMulti(all_stocks,sDate,eDate)

# also this should generate a dateList
def stockListAllData(actLedger,sDate,eDate):

    usa = []
    stockList=[]
    # split tickers into USA and foreign
    for key in actLedger: # go through every key
        sub= actLedger[key] # get the list of the key
        # get the first transaction object of each ticker
        subTicker= sub[0][1]
        # if the asset attribute is a stock, we keep the key for stock list
        if subTicker.asset == 'Stocks':
            if subTicker.currency == 'USD':
                usa.append(key)

    # get aapl ticker because the price history extends back decades
    # Eventually, we should cache a list of trading days that we verify
    if 'AAPL' not in usa:
        usa.append('AAPL')
    # get US prices from tiingo
    usaDict = tiingoListAllData(usa,sDate,eDate)
    # get foreign prices from yahoo finance
    foreign = getPricesOfThreeForeignStocks(sDate,eDate)
    # get tradeDays
    tradeDays = usaDict['AAPL'].keys()

    return(usaDict,foreign,tradeDays)



# MAIN:

if __name__ == "__main__":
    print()
else:
    print('Import: {}'.format(__file__))
