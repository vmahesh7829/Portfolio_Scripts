__author__ = 'Gianluca'

# Importing modules
import pandas as pd
import numpy as np
import bisect
import copy
from datetime import date, timedelta

# Importing files
from stockDataLib import *

def testActivity():
    # BUNCH OF TESTS
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    print('checking over trades: ')
    test= activityLedger['TSLA']
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
        # borrowInterest
        self.borrowCost = None
        # splitFactor
        self.splitFactor = None
        # ticker
        self.ticker= None
        # date
        self.tranDate= None
        # time
        self.time= None
        # currency
        self.currency= None
        # asset type (stock, forex, etc)
        self.asset= None
        # proceeds (essentially the cash flow)
        self.proceeds= None
        # basis (cost basis)
        self.basis= None

class Holding:

    def __init__(self):
        self.asset= None
        self.ticker= None
        self.units= None
        self.currency= None
        self.basis= None

def getSection(df, index):
    # GETTING SPECIFIC SECTION
    section= df.loc[index] # getting everything that is a trade
    newHeader= section.iloc[0] # assigning first row as headers (which they are in CSV)
    section= section.iloc[1:] # making DF w/o the first row
    section.columns= newHeader # assigning that header to new DF
    dim= section.shape # dimensions (rows,cols) which allows for indexing
    return section, dim

def getDateTime(strDate,symbol):
    date1= strDate.split(symbol)
    yr= int(date1[0])
    mth= int(date1[1])
    dy= int(date1[2])        
    tranDate= date(yr,mth,dy) # turing date into a datetime object
    return tranDate

# ngl, this is pretty retarded
def getDateTime2(strDate,symbol):
    date1= strDate.split(symbol)
    yr= int('20'+date1[2]) # !!!! this totally fucks up if dates are pre 2000 !!!!!
    mth= int(date1[0])
    dy= int(date1[1])        
    tranDate= date(yr,mth,dy) # turing date into a datetime object
    return tranDate

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
            
            tranAsset= row['Asset Category']

            dateTime= row['Date/Time'] # getting the date & time of trade: YYYY-MM-DD, HH:MM:SS (military time)
            date0= dateTime.split(', ')[0] # separating out the date
            time= dateTime.split(', ')[1] # separating out the time
            tranDate= getDateTime(date0, '-') # turing date into a datetime object

            quantity0= row['Quantity'].replace(',','') # want to remove and commas if CSV adds them for thousands
            quantity= float(quantity0) # getting the number of shares traded

            # ATTACH ALL THE NECESSARY DATA TO THE INSTANCE 
            tradeInstance= Transaction('Trade') # INITIALIZING THE INSTANCE
            tradeInstance.tranDate= tranDate
            tradeInstance.time= time

            tranPrice= float(row['T. Price']) # getting the transaction price
            tranBasis= float(row["Basis"])
            tranComm= float(row['Comm/Fee']) # getting the comissions and fees (in T.Price currency)

            # there a many types of trades, e.g. Stocks
            if tranAsset == 'Stocks':
                tranTicker= row['Symbol'] # getting the ticker
                tranShares= quantity
                tranProceeds= float(row['Proceeds'])
                tranAsset2= 'Stock'
                tranCurr= row['Currency'] # getting the currency of the trade
                tranComm= float(row['Comm/Fee']) # getting the comissions and fees (in T.Price currency)
                
            # here we are dealing w/ Forex
            if tranAsset == 'Forex':
                tranTicker= 'CURR.'+row['Currency']
                tranShares= float(row['Proceeds']) # units of new currency
                tranProceeds= quantity # $ sold for Forex
                tranAsset2= 'Currency'
                
                if quantity < 0: # FOREX IS A CLUSTERFUCK, SEE WHAT HAPPENS WHEN YOU BUY BACK USD
                    tranCurr= 'USD'
                if quantity > 0:
                    tranCurr= row['Currency']
                
            tradeInstance.ticker= tranTicker
            tradeInstance.dShares= tranShares
            tradeInstance.proceeds= tranProceeds

            tradeInstance.tPrice= tranPrice
            tradeInstance.basis= tranBasis
            
            tradeInstance.comm= tranComm
            tradeInstance.currency= tranCurr
            tradeInstance.asset= tranAsset2 # making more clear, it's forex trade, but asset is currency

            if tranTicker not in activityLedger:    
                activityLedger[tranTicker]=[]
            activityLedger[tranTicker].append((tranDate, tradeInstance)) 


    # GETTING DIVIDEND DATA
    dividends, dim= getSection(df, 'Dividends') # getting everything that is a trade

    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):
        row=dividends.iloc[i] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        tranDate= row['Date']

        if type(tranDate) != type(0.1): # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            tranDate= getDateTime2(tranDate, '/') # turing date into a datetime object
            ticker0= row['Description'] # getting the description which includes ticker
            ticker= ticker0.split('(')[0] # the ticker has a bunch of stuff in parenthesis e.g. AAPL(US485848584)
            amount= float(row['Amount']) # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment
            
            divInstance= Transaction('Dividend') # initializing the instance for the dividend
            divInstance.ticker= ticker # adding associated ticker
            divInstance.proceeds= amount # dividend amount
            divInstance.currency= curr  # currency 
            divInstance.tranDate= tranDate # date of dividend
            divInstance.dShares= amount

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
            tranDate= getDateTime2(tranDate, '/') # turing date into a datetime object
            amount= float(row['Amount']) # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment
            
            intInstance= Transaction('Interest') # initializing the instance for the dividend
            intInstance.proceeds= amount
            intInstance.currency= curr
            intInstance.tranDate= tranDate
            intInstance.dShares= amount

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
            tranDate= getDateTime2(tranDate, '/') # turing date into a datetime object
            amount= float(row['Amount'])
            curr= row['Currency']

            depInstance= Transaction('Deposit / Withdrawal')
            depInstance.tranDate= tranDate
            depInstance.currency= curr
            depInstance.proceeds= amount 
            depInstance.ticker= curr
            
            if 'Dep/With' not in activityLedger:
                activityLedger['Dep/With'] = []
            
            activityLedger['Dep/With'].append((tranDate, depInstance))

    return activityLedger

def getSingleList(activityLedger):
    singleList= []
    for key in activityLedger:
        singleList+=activityLedger[key]
    return singleList

def getStockList(singleList):
    # this is how we can get a stock list
    stockList= []
    for i in singleList:
        #print(i)
        transi= i[1]
        asseti= transi.asset
        tickeri= transi.ticker
        if asseti == 'Stock':
            if tickeri not in stockList:
                stockList.append(tickeri)
    return stockList

def holdingDeepCopy(prevDayDict):
    newDict= {}
    # creating a deep copy
    for ticker in prevDayDict:
        copyInst= Holding()
        copyInst.asset= prevDayDict[ticker].asset
        copyInst.ticker= prevDayDict[ticker].ticker
        copyInst.units= prevDayDict[ticker].units
        copyInst.currency= prevDayDict[ticker].currency
        copyInst.basis= prevDayDict[ticker].basis
        newDict[ticker]=copyInst
    return newDict


def dailyHoldings(singleList, stockData, baseCurr, stockList):
    # neet full date list, and a list of transaction dates to match changes
    fullDateList= list(stockData['SPY'].keys())
    tranDateList= [item[0] for item in singleList]

    # initializing the holdings dictionary
    initDate= sDate-timedelta(1)
    baseCurr= 'CURR.'+baseCurr # want to make it obvoius that this is a currency

    # creating base currency instance
    initInst= Holding() # instance of $0
    initInst.asset= 'Currency'
    initInst.ticker= baseCurr # for stocks this will obv be a ticker
    initInst.units= 0
    initInst.currency= baseCurr 
    initInst.basis= 0 # this will never be used since currencies don't have capital gains (i think?)

    # initializing our portfolio (day before deposit)
    holdings= {initDate: {baseCurr: initInst}}
    navList=[]
    depList=[0]*len(fullDateList)  

    # total number of transactions (integer)
    tranLen= len(tranDateList)
    
    idxTracker= -1 # creating a index tracker to make things easier
    for i in fullDateList: # looping through entire date range 
        idxTracker+=1 # moving to next trading day, so gotta add one (starts at -1)

        if idxTracker == 0:
            prevDate= initDate # if first index, prevoius day is initDate
        else:
            prevDate= fullDateList[idxTracker-1] # getting the previous day in full date list

        # initially holdings will be equivalent to prevoius day
        holdings[i]= holdingDeepCopy(holdings[prevDate]) # USE DEEP COPY

        # if splitfactor is a yes, gonna create a random transaction rn 
        splitTracker= checkSplit(stockData, stockList, day=i)
        
        # if any splits on this day, we need to create 0 proceed transactions
        if len(splitTracker) != 0:
            for split in splitTracker:
                stock= split[0]
                factor= split[1]

                splitTransaction= Transaction('Split')
                splitTransaction.ticker= stock
                splitTransaction.dShares= float(factor)
                splitTransaction.comm= 0
                splitTransaction.proceeds= 0
                splitTransaction.currency= 'USD'

                # need to insert these things into singleList and tranDateList
                splitIdx= bisect.bisect_left(tranDateList, i)
                tranDateList.insert(splitIdx, i)
                singleList.insert(splitIdx, (i, splitTransaction))


        if i in tranDateList: # if that date corresponds with a transaction date we need to modify
            tranIdx= bisect.bisect_left(tranDateList,i) # getting placement in the transaction list
            
            while tranDateList[tranIdx] == i:
                tranInst= singleList[tranIdx][1] # getting the transaction instance
                # getting transaction characteristics
                tranType= tranInst.transType
                tranTicker= tranInst.ticker
                tranCurr= tranInst.currency
                newShares= tranInst.dShares
                tranComm= tranInst.comm
                tranProceeds= tranInst.proceeds
                tranAsset= tranInst.asset

                # always deal w/ Proceeds first
                currTick= 'CURR.'+tranCurr
                holdings[i][currTick].units += tranProceeds

                if tranType == 'Deposit / Withdrawal':
                    depList[idxTracker]+= tranProceeds

                if tranType == 'Trade' or tranType =='Split':
                    holdings[i][currTick].units += tranComm

                    if tranTicker in holdings[i]: 
                        # trades get handled normally
                        if tranType == 'Trade':
                            holdings[i][tranTicker].units += newShares # or the issue is here
                            holdings[i][tranTicker].basis= 'fuckyou'
                        
                        # if it's a split same thing but it's multiplication
                        if tranType == 'Split':
                            holdings[i][tranTicker].units *= newShares # or the issue is here
                            holdings[i][tranTicker].basis= 'fuckyou'
                        
                    else:
                        holdings[i][tranTicker]= Holding()
                        holdings[i][tranTicker].asset= tranAsset
                        holdings[i][tranTicker].ticker= tranTicker
                        holdings[i][tranTicker].units= newShares
                        holdings[i][tranTicker].basis= 'fuckyou'
                        holdings[i][tranTicker].currency= tranCurr
            
                tranIdx += 1
                if tranIdx > (tranLen-1):
                    break # if adding +1 makes longer than actual list, we're done


        #itializing day's NAV
        nav=0
        for item in holdings[i]:
            itemShares= holdings[i][item].units
            if item[:5] != 'CURR.' and item != 'NLAB':
                itemClose= stockData[item][i]['close']
                nav+= itemClose * itemShares

            if item == 'CURR.USD':
                nav+= 1 * itemShares

            if item == 'CURR.SEK':
                nav+= 0.12 * itemShares

            if item == 'NLAB':
                nav+= 0.12 * 44 * itemShares
        
        navList.append(nav)


    return holdings, navList, depList

def checkSplit(stockData, stockList, day):
    splitTracker= []
    for stock in stockList:
        tickerData= stockData[stock]
        try:
            splitF= tickerData[day]['splitFactor']
            if splitF != 1.0:
                print()
                print('SPLIT ALERT!!!!  ', stock, day, splitF)
                splitTracker.append([stock, splitF])
        except:
            print(stock, ': FAILED checkSplit()')
            pass

    return splitTracker



if __name__ == "__main__":

    gcPath2019= '/Users/gianluca/Desktop/ibkrCsv/2019activity.csv'
    gcPath2020= '/Users/gianluca/Desktop/ibkrCsv/2020activity.csv'

    # initializing the stock ledger
    activityLedger= {}  # will ultimately be a dictionary of lists of tuples

    # updating the stock ledger
    activityLedger= parseIBKR(activityLedger, gcPath2019)
    activityLedger= parseIBKR(activityLedger, gcPath2020)

    # putting all the ledgers into a single list
    singleList= getSingleList(activityLedger)

    # sorting the list of tuples
    singleList.sort(key= lambda x: x[0]) 

    # getting stock list 
    stockList= getStockList(singleList) # this no longer works

    # start date = the first deposit
    sDate= singleList[0][1].tranDate
    eDate= date.today()

    # tiingo API pull has to include benchmark
    benchmark= 'SPY'
    tiingoList= stockList + [benchmark]
    #tiingoList= ['SPY','TSLA']

    # Now we need to do the API thing
    stockData = tiingoListAllData(tiingoList, sDate, eDate)

    # get dictionary of daily holdings, TWR, NPV (in basCurr)
    holdings, navList, depList= dailyHoldings(singleList, stockData, 'USD', stockList)


    # DOING SOME TESTS

    # Time to debug this ...    
    monday= date(2021,1,25)
    mondayHoldings= holdings[monday]
    for _ in mondayHoldings:
        pos= mondayHoldings[_]
        print(pos.ticker,': ',pos.units)


    rets=[]
    for i in range(1,len(navList)):
        ret= 100*(((navList[i]-depList[i])/navList[i-1])-1)
        rets.append(round(ret,2))

    logRet=[0]*len(rets)
    logRet[0]= rets[0]
    for i in range(1,len(rets)):
        logRet[i]=rets[i]+logRet[i-1] 

    import matplotlib.pyplot as plt
    plt.plot(logRet)
    plt.show()



else:
    print('Import: {}'.format(__file__))

