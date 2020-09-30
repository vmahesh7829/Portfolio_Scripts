import requests
import datetime
from datetime import date

# the api has a column field that lowers the amount of response data


# Takes one ticker and a daterange and calls the Tiingo API
# Returns a dictionary with date as the key and adjusted close
# as the value for the inputted daterange

def genTiingoDict(ticker: str, sDate, eDate):

    token = *****


    reqBody = "https://api.tiingo.com/tiingo/daily/"+ticker+'/prices?startDate='
    reqBody = reqBody +sDate+ '&endDate=' + eDate+token+"&columns=adjClose"

    headers = {
        'Content-Type': 'application/json'
    }
    requestResponse = requests.get(reqBody, headers=headers)

    pData = requestResponse.json()

    stock_Dict = {}

    for currDay in pData:

        in_date = currDay['date']
        in_date = date(int(in_date[0:4]),int(in_date[5:7]),int(in_date[8:10]))

        stock_Dict[in_date] = currDay['adjClose']


    return stock_Dict

def getStockDict(stockSet: set,sDate,eDate):

    sDate = sDate.isoformat()
    eDate = eDate.isoformat()

    stock_dict = {}

    for stock in stockSet:
        stock_dict[stock] = genTiingoDict(stock,sDate,eDate)

    return stock_dict
