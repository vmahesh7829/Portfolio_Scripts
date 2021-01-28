__author__ = 'Gianluca'

import pandas as pd
import numpy as np

import os
import heapq
import datetime



# UNIVERSAL INSTANCE ACROSS ALL TYPES OF SIGNIFICANT EVENTS
class Transaction:

    def __init__(self, transType):

        # transtype
        self.transType = transType
        # change in shares
        self.dShares = None
        # transaction price
        self.tPrice = None
        # commission
        self.comm = None
        # dividend
        self.divValue = None
        # borrowInterest
        self.borrowCost = None
        # splitFactor
        self.splitFactor = None
        # endShares
        self.endShares = None
        # ticker
        self.ticker= None
        # date
        self.date= None
        # time
        self.time= None
        # currency
        self.currency= None
        # asset type (stock, forex, etc)
        self.asset= None
        # store the key as well for future searchability
        self.ledgerKey = None
        # every transaction should change the amount of cash in the portfolio
        self.dCash = None

    def __eq__(self, other):
        return self.date == other.date

    def __lt__(self, other):
        return self.date < other.date

def getSection(df, index):
    # GETTING SPECIFIC SECTION

    

    section= df.loc[index] # getting everything that is a trade
    newHeader= section.iloc[0] # assigning first row as headers (which they are in CSV)
    section= section.iloc[1:] # making DF w/o the first row
    section.columns= newHeader # assigning that header to new DF
    dim= section.shape # dimensions (rows,cols) which allows for indexing
    return section, dim


def parseIBKR(activityLedger, csvPath):

    # header=None makes no header, just 0-N
    # index_col=0 makes the first column the index values (e.g. Trades, ...)
    df= pd.read_csv(csvPath, header=None, index_col=0)

    # GETTING TRADE DATA
    trades, dim= getSection(df, 'Trades') # getting everything that is a trade

    # LOOP THROUGH ALL TRADES TO GET THE DATA
    for i in range(dim[0]):

        row= trades.iloc[i] # isolating a row for analysis
        order= row['DataDiscriminator'] # !!! WHEN YOU ILOC A ROW, HEADER OF DATAGRAME BECOMES INDEX !!!!!

        if order == 'Order': # if it's an order we'll continue

            ticker= row['Symbol'] # getting the ticker
            quantity0= row['Quantity'].replace(',','') # want to remove and commas if CSV adds them for thousands
            quantity= float(quantity0) # getting the number of shares traded
            dateTime= row['Date/Time'] # getting the date & time of trade: YYYY-MM-DD, HH:MM:SS (military time)

            date= dateTime.split(', ')[0] # separating out the date
            time= dateTime.split(', ')[1] # separating out the time

            # Turning date into a datetime object for comparator
            date = date.split('-')
            date = datetime.datetime( int(date[0]) , int(date[1]), int(date[2]))

            # ATTACH ALL THE NECESSARY DATA TO THE INSTANCE
            tradeInstance= Transaction('Trade') # INITIALIZING THE INSTANCE

            tradeInstance.ticker= ticker
            # store the key where instance is held in dict
            tradeInstance.ledgerKey = ticker
            tradeInstance.dShares= quantity
            tradeInstance.date= date
            tradeInstance.time= time
            tradeInstance.comm= row['Comm/Fee'] # getting the comissions and fees
            tradeInstance.tPrice= row['T. Price'] # getting the transaction price
            tradeInstance.currency= row['Currency'] # getting the currency of the trade
            tradeInstance.asset= row['Asset Category'] # grabbing the asset cateogy (stock, ...)
            tradeInstance.dCash = row['Basis'] # storing net cash movement of each transaction

            if ticker in activityLedger:

                prevTotal= activityLedger[ticker][-1][1].endShares #previous transaction endShares
                newTotal= prevTotal + quantity # adding traded shares (+/-) to old total to get new total
                tradeInstance.endShares= newTotal # adding the new total to the instance

                activityLedger[ticker].append((date, tradeInstance)) # adding tuple (date,inst) to list

            else: # if first time seeing stock need to initialize list first
                activityLedger[ticker]=[] # initiallizing a list for a stock (will hold trades)
                tradeInstance.endShares= quantity # since it's first order, the amount
                activityLedger[ticker].append((date, tradeInstance)) # adding tuple (date,inst) to list



    # GETTING DIVIDEND DATA
    dividends, dim= getSection(df, 'Dividends') # getting everything that is a trade

    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):

        row=dividends.iloc[i] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        date= row['Date']

        if type(date) == str: # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            ticker0= row['Description'] # getting the description which includes ticker
            ticker= ticker0.split('(')[0] # the ticker has a bunch of stuff in parenthesis e.g. AAPL(US485848584)
            amount= float(row['Amount']) # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment

            divInstance= Transaction('Dividend') # initializing the instance for the dividend
            date = date.split('/')
            date = datetime.datetime( int(date[2])+yearInc , int(date[0]), int(date[1]))

            divInstance.ticker= ticker # adding associated ticker
            divInstance.ledgerKey = 'Dividends'
            divInstance.dCash= amount # dividend amount
            divInstance.currency= curr  # currency
            divInstance.date= date # date of dividend

            if 'Dividends' not in activityLedger:
                activityLedger['Dividends']=[]

            activityLedger['Dividends'].append((date, divInstance)) # creating a dividend list if it does not exist


    # GETTING INTEREST DATA
    interest, dim= getSection(df, 'Interest') # getting everything that is a trade

    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):

        row=interest.iloc[i] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        date= row['Date']



        if type(date) == str: # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            amount= float(row['Amount']) # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment

            intInstance= Transaction('Interest') # initializing the instance for the dividend

            date = date.split('/')
            date = datetime.datetime( int(date[2])+yearInc , int(date[0]), int(date[1]))

            intInstance.dCash= amount
            intInstance.ledgerKey = 'Interest'
            intInstance.currency= curr
            intInstance.date= date

            if 'Interest' not in activityLedger:
                activityLedger['Interest']=[]

            activityLedger['Interest'].append((date, intInstance))


    # GETTING DEPOSIT DATA
    deposits, dim= getSection(df, 'Deposits & Withdrawals')

    # LOOP THROUGH ALL DEPS/WITHS TO GET THE DATA
    for i in range(dim[0]):

        row= deposits.iloc[i]
        date= row['Settle Date']


        if type(date) == str:
            amount= float(row['Amount'])
            curr= row['Currency']

            depInstance= Transaction('Deposit / Withdrawal')

            date = date.split('/')
            date = datetime.datetime( int(date[2])+yearInc , int(date[0]), int(date[1]))

            depInstance.date= date
            depInstance.ledgerKey = 'Dep/With'
            depInstance.currency= curr
            depInstance.dCash = amount

            if 'Dep/With' not in activityLedger:
                activityLedger['Dep/With'] = []

            activityLedger['Dep/With'].append((date, depInstance))

    return activityLedger


def getStockList(activityLedger):
    # this is how we can get a stock list
    stockList=[]
    for key in activityLedger: # go through every key
        sub= activityLedger[key] # get the list of the key
        subTicker= sub[0][1].asset # get the asset attribute contained in the list
        if subTicker == 'Stocks': # if the asset attribute is a stock, we keep the key for stock list
            stockList.append(key) # appending the key of current iteration to the list (since instance reps a "Stocks")
    return stockList

# this prints out the activity ledger
def printActivityLedger(activityLedger):
    for key in activityLedger:
        for entry in activityLedger[key]:
            trade = entry[1]
            print(trade.date,trade.transType,trade.ticker,trade.dShares,
            trade.tPrice,trade.endShares)

        print()

# takes in a list of sorted lists and returns a merged list will all elements
def mergeKSortedLists(lists: list, actLedger: dict):

  h = []
  sortedList = []

  # push 1 val for every item in list
  for transType in lists:
    heapq.heappush(h, (transType[0][0],transType[0][1],0) )

  while (len(h) > 0):
    date,instance,i = heapq.heappop(h)
    # append next item to output
    sortedList.append((date,instance))
    print(instance.date,instance.transType,instance.ticker,instance.dShares,
    instance.tPrice,instance.endShares)

    # push next object from list that was popped(unless list is over)
    # increment i to the next element in the list that holds instance
    i +=1
    instList = actLedger[instance.ledgerKey]
    if (i < len(instList)):
      heapq.heappush(h, (instList[i][0],instList[i][1],i) )

  return sortedList



if __name__ == "__main__":

    # later this should potentially be stored as an environment variable
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path += "/IBKR2020.csv"
    # if a file before 2000 is entered, this has to be changed to 1900
    # if this is not done y2k bug will happen
    yearInc = 2000

    # initializing the stock ledger
    activityLedger= {}  # will ultimately be a dictionary of lists of tuples
    activityLedger= parseIBKR(activityLedger, dir_path)

    stockList= getStockList(activityLedger)

    # this is a list of all the lists in activityLedger
    kLists = activityLedger.values()

    # merge them
    sortedTransList = mergeKSortedLists(kLists,activityLedger)


    # push notes:

    # be careful if we every put a 1999 file in here

    # df.iLoc is throwing errors when a certain section isn't in the csv
    # solution is to search the csv, then only run if the section is present

    # made a print activity ledger function to print it out

    # added a comparator function to Transaction instance
    # (do not use its for the heapq function)

    # added a field ledgerKey to find a particular instance inside activity ledger
    # or rather the list inside it

    # merged the lists in activity ledger into one sorted list

    #Todo:
        # add try catch to this file
        # start NAV calculation in new branch
        # call the tiingo API (check for splits)
        # calculate NAV (and update for splits)

    #TODO Later:
        # change API to only ask for dates that are used (perhaps write library)
        # add time of trade to datetimeobj (should be in tradeInstance.time)





else:
    print('Import: {}'.format(__file__))
