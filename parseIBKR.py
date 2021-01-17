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


if __name__ == "__main__":

    gcPath2019= '/Users/gianluca/Desktop/ibkrCsv/2019activity.csv'
    gcPath2020= '/Users/gianluca/Desktop/ibkrCsv/2020activity.csv'

    # for 2019
    # header=None makes no header, just 0-N
    # index_col=0 makes the first column the index values (e.g. Trades, ...)
    df= pd.read_csv(gcPath2019, header=None, index_col=0)
    
    # GETTING TRADE DATA
    trades= df.loc['Trades'] # getting everything that is a trade
    newHeader= trades.iloc[0] # assigning first row as headers (which they are in CSV)
    trades=trades.iloc[1:] # making DF w/o the first row
    trades.columns= newHeader # assigning that header to new DF
    dim= trades.shape # dimensions (rows,cols) which allows for indexing

    # initializing the stock ledger
    stockLedger= {}  # will ultimately be a dictionary of lists of tuples

    # LOOP THROUGH ALL TRADES TO GET THE DATA
    for i in range(dim[0]):

        row= trades.iloc[i] # isolating a row for analysis
        order= row['DataDiscriminator'] # !!! WHEN YOU ILOC A ROW, HEADER BECOMES INDEX !!!!!

        if order == 'Order': # if it's an order we'll continue

            ticker= row['Symbol'] # getting the ticker
            
            # ATTACH ALL THE NECESSARY DATA TO THE INSTANCE 
            tradeInstance= Transaction('Trade') # INITIALIZING THE INSTANCE
            tradeInstance.ticker= ticker
            tradeInstance.dShares= row['Quantity'] # getting the number of shares traded
            tradeInstance.comm= row['Comm/Fee'] # getting the comissions and fees
            tradeInstance.tPrice= row['T. Price'] # getting the transaction price     

            # EXTRA DATA POINTS FOR POSSIBLE FUTURE USE
            asset= row['Asset Category'] # grabbing the asset cateogy
            currency= row['Currency'] # getting the currency of the trade
            date= row['Date/Time'] # getting the date & time of trade
            tPrice= row['T. Price'] # getting the transaction price
            
            if ticker in stockLedger:
                stockLedger[ticker].append((date, tradeInstance))
            
            else: # if first time seeing stock need to initialize list first
                stockLedger[ticker]=[]
                stockLedger[ticker].append((date, tradeInstance))

            
    print(stockLedger)


else:
    print('Import: {}'.format(__file__))