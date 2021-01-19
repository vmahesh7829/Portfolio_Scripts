__author__ = 'Gianluca'

import pandas as pd
import numpy as np

from datetime import date, timedelta

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
        self.tranDate= None
        # time
        self.time= None
        # currency
        self.currency= None
        # interest
        self.interest= None
        # deposit
        self.deposit= None
        # withdrawal
        self.withdrawal= None
        # asset type (stock, forex, etc)
        self.asset= None

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

            date0= dateTime.split(', ')[0] # separating out the date
            time= dateTime.split(', ')[1] # separating out the time
            
            date1= date0.split('-')
            yr= int(date1[0])
            mth= int(date1[1])
            dy= int(date1[2])
            
            tranDate= date(yr,mth,dy) # turing date into a datetime object

            # ATTACH ALL THE NECESSARY DATA TO THE INSTANCE 
            tradeInstance= Transaction('Trade') # INITIALIZING THE INSTANCE

            tradeInstance.ticker= ticker
            tradeInstance.dShares= quantity
            tradeInstance.tranDate= tranDate
            tradeInstance.time= time
            tradeInstance.comm= row['Comm/Fee'] # getting the comissions and fees
            tradeInstance.tPrice= row['T. Price'] # getting the transaction price
            tradeInstance.currency= row['Currency'] # getting the currency of the trade
            tradeInstance.asset= row['Asset Category'] # grabbing the asset cateogy (stock, ...)

            if ticker in activityLedger:

                prevTotal= activityLedger[ticker][-1][1].endShares #previous transaction endShares
                newTotal= prevTotal + quantity # adding traded shares (+/-) to old total to get new total
                tradeInstance.endShares= newTotal # adding the new total to the instance

                activityLedger[ticker].append((tranDate, tradeInstance)) # adding tuple (date,inst) to list
            
            else: # if first time seeing stock need to initialize list first
                activityLedger[ticker]=[] # initiallizing a list for a stock (will hold trades)
                tradeInstance.endShares= quantity # since it's first order, the amount 
                activityLedger[ticker].append((tranDate, tradeInstance)) # adding tuple (date,inst) to list


    # GETTING DIVIDEND DATA
    dividends, dim= getSection(df, 'Dividends') # getting everything that is a trade

    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):
        
        row=dividends.iloc[i] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        tranDate= row['Date']

        if type(tranDate) != type(0.1): # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            ticker0= row['Description'] # getting the description which includes ticker
            ticker= ticker0.split('(')[0] # the ticker has a bunch of stuff in parenthesis e.g. AAPL(US485848584)
            amount= float(row['Amount']) # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment
            
            divInstance= Transaction('Dividend') # initializing the instance for the dividend
            
            divInstance.ticker= ticker # adding associated ticker
            divInstance.divValue= amount # dividend amount
            divInstance.currency= curr  # currency 
            divInstance.tranDate= tranDate # date of dividend

            if 'Dividends' not in activityLedger:    
                activityLedger['Dividends']=[]

            activityLedger['Dividends'].append((tranDate, divInstance)) # creating a dividend list if it does not exist


    # GETTING INTEREST DATA
    interest, dim= getSection(df, 'Interest') # getting everything that is a trade

    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):
        
        row=interest.iloc[i] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        tranDate= row['Date']

        if type(tranDate) != type(0.1): # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            amount= float(row['Amount']) # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment
            
            intInstance= Transaction('Interest') # initializing the instance for the dividend
            
            intInstance.interest= amount
            intInstance.currency= curr
            intInstance.tranDate= tranDate

            if 'Interest' not in activityLedger:
                activityLedger['Interest']=[]
                
            activityLedger['Interest'].append((tranDate, intInstance))


    # GETTING DEPOSIT DATA
    deposits, dim= getSection(df, 'Deposits & Withdrawals')   

    # LOOP THROUGH ALL DEPS/WITHS TO GET THE DATA
    for i in range(dim[0]):

        row= deposits.iloc[i]
        tranDate= row['Settle Date']

        if type(tranDate) != type(0.1):
            amount= float(row['Amount'])
            curr= row['Currency']

            depInstance= Transaction('Deposit / Withdrawal')

            depInstance.tranDate= tranDate
            depInstance.currency= curr

            if amount>0:
                depInstance.deposit= amount
            else:
                depInstance.withdrawal= amount
            
            if 'Dep/With' not in activityLedger:
                activityLedger['Dep/With'] = []
            
            activityLedger['Dep/With'].append((tranDate, depInstance))

    return activityLedger

def getStockList(activityLedger):
    # this is how we can get a stock list
    stockList=[]
    for key in activityLedger: # go through every key
        sub= activityLedger[key] # get the list of the key
        subTicker= sub[0][1].asset # get the asset attribute contained in the list
        if subTicker == 'Stocks': # if the asset attribute is a stock, we keep the key for stock list
            stockList.append(key) # appending the key of current iteration to the list (since instance reps a "Stocks")
    sDate= activityLedger['Dep/With'][0][0] # Date in tuple of first deposit in account
    return stockList, sDate

if __name__ == "__main__":

    gcPath2019= '/Users/gianluca/Desktop/ibkrCsv/2019activity.csv'
    gcPath2020= '/Users/gianluca/Desktop/ibkrCsv/2020activity.csv'

    # initializing the stock ledger
    activityLedger= {}  # will ultimately be a dictionary of lists of tuples

    # updating the stock ledger
    activityLedger= parseIBKR(activityLedger, gcPath2019)
    activityLedger= parseIBKR(activityLedger, gcPath2020)

    # getting a stock list and a start date
    # Note:
    #   o need to make all dates datetime instances
    #   o let's have getStockList also provide eDate to save a line within "main" 
    stockList, sDate= getStockList(activityLedger)





    print(stockList)
    print(sDate)

    # Now we need





    # BUNCH OF TESTS
    print()
    print()
    print('checking over trades: ')
    test= activityLedger['CARR']
    for i in test:
        #print(i)
        print(i[0], i[1].tranDate, i[1].time, i[1].ticker, i[1].dShares, i[1].endShares)


    print()
    print()
    print('checking over dividends: ')
    test= activityLedger['Dividends']
    for i in test:
        #print(i)
        print(i[0],i[1].tranDate, i[1].ticker, i[1].divValue)

    print()
    print()
    print('checking over interest: ')
    test= activityLedger['Interest']
    for i in test:
        #print(i)
        print(i[0],i[1].tranDate, i[1].interest, i[1].currency)


    print()
    print()
    print('checking over deposits: ')
    test= activityLedger['Dep/With']
    for i in test:
        #print(i)
        print(i[0],i[1].tranDate, i[1].deposit, i[1].withdrawal)


else:
    print('Import: {}'.format(__file__))