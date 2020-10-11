import requests
import datetime
from datetime import date
import pymongo

# the api has a column field that lowers the amount of response data


# Takes one ticker and a daterange and calls the Tiingo API
# Returns a dictionary with date as the key and adjusted close
# as the value for the inputted daterange

def genTiingoDict(ticker: str, sDate, eDate):

    token = *****


    reqBody = "https://api.tiingo.com/tiingo/daily/"+ticker+'/prices?startDate='
    reqBody = reqBody +sDate+ '&endDate=' + eDate+token+"&columns=adjClose,close"

    headers = {
        'Content-Type': 'application/json'
    }
    requestResponse = requests.get(reqBody, headers=headers)

    pData = requestResponse.json()

    stock_Dict = {}
    closeDict = {}

    for currDay in pData:

        in_date = currDay['date']
        in_date = date(int(in_date[0:4]),int(in_date[5:7]),int(in_date[8:10]))
        stock_Dict[in_date] = currDay['adjClose']

        closeDict[currDay['date'][0:10]]= currDay['close']

        # also save close price to database


    return (stock_Dict,closeDict)

def getStockDict(stockSet: set,sDate,eDate):
    client = pymongo.MongoClient("mongodb+srv://DyAQ0qSyAdi1Udg9:DyAQ0qSyAdi1Udg9@apidatabank.drr3k.mongodb.net/historicalStockPrices?retryWrites=true&w=majority")
    db = client.historicalStockPrices
    posts = db.tiingoClose

    sDate = sDate.isoformat()
    eDate = eDate.isoformat()

    stock_dict = {}
    dbDict = {}

    for stock in stockSet:
        out = genTiingoDict(stock,sDate,eDate)
        stock_dict[stock] = out[0]
        dbDict[stock] = out[1]

    post_id = posts.insert_one(dbDict).inserted_id
    print(dbDict)
    return stock_dict
