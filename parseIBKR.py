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
        # time
        self.time= None
        # currency
        self.currency= None
        # interest
        self.interest= None


if __name__ == "__main__":

    gcPath2019= '/Users/gianluca/Desktop/ibkrCsv/2019activity.csv'
    gcPath2020= '/Users/gianluca/Desktop/ibkrCsv/2020activity.csv'

    # initializing the stock ledger
    activityLedger= {}  # will ultimately be a dictionary of lists of tuples

    # for 2019
    # header=None makes no header, just 0-N
    # index_col=0 makes the first column the index values (e.g. Trades, ...)
    df= pd.read_csv(gcPath2020, header=None, index_col=0)
    
    
    # GETTING TRADE DATA
    trades= df.loc['Trades'] # getting everything that is a trade
    newHeader= trades.iloc[0] # assigning first row as headers (which they are in CSV)
    trades= trades.iloc[1:] # making DF w/o the first row
    trades.columns= newHeader # assigning that header to new DF
    dim= trades.shape # dimensions (rows,cols) which allows for indexing

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

            # ATTACH ALL THE NECESSARY DATA TO THE INSTANCE 
            tradeInstance= Transaction('Trade') # INITIALIZING THE INSTANCE

            tradeInstance.ticker= ticker
            tradeInstance.dShares= quantity
            tradeInstance.date= date
            tradeInstance.time= time
            tradeInstance.comm= row['Comm/Fee'] # getting the comissions and fees
            tradeInstance.tPrice= row['T. Price'] # getting the transaction price
            tradeInstance.currency= row['Currency'] # getting the currency of the trade

            # EXTRA DATA POINTS FOR POSSIBLE FUTURE USE
            asset= row['Asset Category'] # grabbing the asset cateogy (stock, ...)

            if ticker in activityLedger:

                prevTotal= activityLedger[ticker][-1][2].endShares #previous transaction endShares
                newTotal= prevTotal + quantity # adding traded shares (+/-) to old total to get new total
                tradeInstance.endShares= newTotal # adding the new total to the instance

                activityLedger[ticker].append((date, asset, tradeInstance)) # adding tuple (date,inst) to list
            
            else: # if first time seeing stock need to initialize list first
                activityLedger[ticker]=[] # initiallizing a list for a stock (will hold trades)
                tradeInstance.endShares= quantity # since it's first order, the amount 
                activityLedger[ticker].append((date, asset, tradeInstance)) # adding tuple (date,inst) to list


    # GETTING DIVIDEND DATA
    dividends= df.loc['Dividends'] # getting everything that is a dividend
    #print(dividends)
    newHeader= dividends.iloc[0] # assigning first row as headers (which they are in CSV)
    dividends= dividends.iloc[1:] # making DF w/o the first row
    dividends.columns= newHeader # assigning that header to new DF
    dim= dividends.shape # dimensions (rows,cols) which allows for indexing

    
    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):
        
        row=dividends.iloc[i] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        date= row['Date']

        if type(date) != type(0.1): # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            ticker0= row['Description'] # getting the description which includes ticker
            ticker= ticker0.split('(')[0] # the ticker has a bunch of stuff in parenthesis e.g. AAPL(US485848584)
            amount= float(row['Amount']) # the amount of money deposited
            curr= row['Currency'] # the currentcy of dividend payment
            
            divInstance= Transaction('Dividend') # initializing the instance for the dividend
            
            divInstance.ticker= ticker
            divInstance.divValue= amount
            divInstance.currency= curr
            divInstance.date= date

            if 'Dividends' in activityLedger:
                
                activityLedger['Dividends'].append((date, ticker, divInstance))
            
            else: 
                activityLedger['Dividends']=[]
                activityLedger['Dividends'].append((date, ticker, divInstance))

    #print('Activity ledger with dividends too')
    #print(activityLedger)

    # GETTING INTEREST DATA
    interest= df.loc['Interest'] # getting everything that is interest
    #print(interest)
    newHeader= interest.iloc[0] # assigning first row as headers (which they are in CSV)
    interest= interest.iloc[1:] # making DF w/o the first row
    interest.columns= newHeader # assigning that header to new DF
    dim= interest.shape # dimensions (rows,cols) which allows for indexing

    # LOOP THROUGH ALL DIVIDENDS TO GET THE DATA
    for i in range(dim[0]):
        
        row=interest.iloc[i] # isolating a row for analysis (remember, this is now a series w/ header as Index)
        date= row['Date']

        if type(date) != type(0.1): # if there is no date, it is not a dividend (I think this is okay but may BREAK)
            amount= float(row['Amount']) # the amount of money deposited
            print(amount)
            curr= row['Currency'] # the currentcy of dividend payment
            
            intInstance= Transaction('Interest') # initializing the instance for the dividend
            
            intInstance.interest= amount
            intInstance.currency= curr
            intInstance.date= date

            if 'Interest' in activityLedger:
                
                activityLedger['Interest'].append((date, intInstance))
            
            else: 
                activityLedger['Interest']=[]
                activityLedger['Interest'].append((date, intInstance))


    #print('Activity ledger with interest too')
    #print(activityLedger)


    print()
    print()
    print('checking over trades: ')
    test= activityLedger['USD.SEK']
    for i in test:
        #print(i)
        print(i[0], i[2].date, i[2].time, i[2].ticker, i[2].dShares, i[2].endShares)



    print()
    print()
    print('checking over dividends: ')
    test= activityLedger['Dividends']
    for i in test:
        #print(i)
        print(i[0],i[2].date, i[2].ticker, i[2].divValue)



    print()
    print()
    print('checking over interest: ')
    test= activityLedger['Interest']
    for i in test:
        #print(i)
        print(i[0],i[1].date, i[1].interest, i[1].currency)



else:
    print('Import: {}'.format(__file__))