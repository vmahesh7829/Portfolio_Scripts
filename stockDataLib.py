__author__ = 'gianluca and vish'

# TODO:


from api_pulls import *

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
            else:
                pass
                # here, we could find the foreign tickers and map them to
                # International tickers that we provide

    # instead for now, its hardcoded
    nonUsTick = {'APT':'APT.AX','NLAB':'NLAB.ST',"AIRd":"AIR.PA"}

    # get aapl ticker because the price history extends back decades
    # Eventually, we should cache a list of trading days that we verify
    if 'AAPL' not in usa:
        usa.append('AAPL')
    # get US prices from tiingo
    usaDict = tiingoListAllData(usa,sDate,eDate)
    # get foreign prices from yahoo finance
    foreign = getPricesOfThreeForeignStocks(sDate,eDate,nonUsTick)
    # get tradeDays
    tradeDays = usaDict['AAPL'].keys()

    return(usaDict,foreign,nonUsTick,tradeDays)



# MAIN:

if __name__ == "__main__":
    print()
else:
    print('Import: {}'.format(__file__))
