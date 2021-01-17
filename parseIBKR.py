__author__ = 'Gianluca'

import pandas as pd
import numpy as np

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
        # currency
        self.currency= None


if __name__ == "__main__":

    gcPath2019= '/Users/gianluca/Desktop/ibkrCsv/2019activity.csv'
    gcPath2020= '/Users/gianluca/Desktop/ibkrCsv/2020activity.csv'

    # initializing the stock ledger
    activityLedger= {}  # will ultimately be a dictionary of lists of tuples

    # for 2019
    # header=None makes no header, just 0-N
    # index_col=0 makes the first column the index values (e.g. Trades, ...)
    df= pd.read_csv(gcPath2019, header=None, index_col=0)
    
    
    # GETTING TRADE DATA
    trades= df.loc['Trades'] # getting everything that is a trade
    newHeader= trades.iloc[0] # assigning first row as headers (which they are in CSV)
    trades= trades.iloc[1:] # making DF w/o the first row
    trades.columns= newHeader # assigning that header to new DF
    dim= trades.shape # dimensions (rows,cols) which allows for indexing

    # LOOP THROUGH ALL TRADES TO GET THE DATA
    for i in range(dim[0]):

        row= trades.iloc[i] # isolating a row for analysis
        order= row['DataDiscriminator'] # !!! WHEN YOU ILOC A ROW, HEADER BECOMES INDEX !!!!!

        if order == 'Order': # if it's an order we'll continue

            ticker= row['Symbol'] # getting the ticker
            quantity= row['Quantity'] # getting the number of shares traded
            date= row['Date/Time'] # getting the date & time of trade

            # ATTACH ALL THE NECESSARY DATA TO THE INSTANCE 
            tradeInstance= Transaction('Trade') # INITIALIZING THE INSTANCE

            tradeInstance.ticker= ticker
            tradeInstance.dShares= quantity
            tradeInstance.date= date
            tradeInstance.comm= row['Comm/Fee'] # getting the comissions and fees
            tradeInstance.tPrice= row['T. Price'] # getting the transaction price
            tradeInstance.currency= row['Currency'] # getting the currency of the trade

            # EXTRA DATA POINTS FOR POSSIBLE FUTURE USE
            asset= row['Asset Category'] # grabbing the asset cateogy (stock, ...)


            if ticker in activityLedger:

                prevTotal= activityLedger[ticker][-1][1].endShares #previous transaction endShares
                newTotal= prevTotal + quantity # adding traded shares (+/-) to old total to get new total
                tradeInstance.endShares= newTotal # adding the new total to the instance

                activityLedger[ticker].append((date, tradeInstance)) # adding tuple (date,inst) to list
            
            else: # if first time seeing stock need to initialize list first
                activityLedger[ticker]=[] # initiallizing a list for a stock (will hold trades)
                tradeInstance.endShares= quantity # since it's first order, the amount 
                activityLedger[ticker].append((date, tradeInstance)) # adding tuple (date,inst) to list

    print('Activity ledger with trades')
    print(activityLedger)
    
    # GETTING DIVIDEND DATA
    dividends= df.loc['Dividends'] # getting everything that is a dividend
    print(dividends)
    newHeader= dividends.iloc[0] # assigning first row as headers (which they are in CSV)
    dividends= dividends.iloc[1:] # making DF w/o the first row
    dividends.columns= newHeader # assigning that header to new DF
    dim= dividends.shape # dimensions (rows,cols) which allows for indexing

    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):
        
        row=dividends.iloc[0] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        date= row['Date']

        if date != 'NaN': # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            ticker0= row['Description'] # getting the description which includes ticker
            ticker= ticker0.split('(')[0] # the ticker has a bunch of stuff in parenthesis e.g. AAPL(US485848584)
            amount= row['Amount'] # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment
            
            divInstance= Transaction('Dividend') # initializing the instance for the dividend
            
            divInstance.ticker= ticker
            divInstance.divValue= amount
            divInstance.currency= curr
            divInstance.date= date

            if 'Dividends' in activityLedger:
                
                activityLedger['Dividends'].append((date, divInstance))
            
            else: 
                activityLedger['Dividends']=[]
                activityLedger['Dividends'].append((date, divInstance))


    print('Activity ledger with dividends too')
    print(activityLedger)




else:
    print('Import: {}'.format(__file__))