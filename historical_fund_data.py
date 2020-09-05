__author__ = 'Viswesh'

#IMPORTS
from api_pulls import *
import pandas_datareader as pdr

from collections.abc import Mapping, Container
from sys import getsizeof

import cProfile
import re
import time
import sys
import inspect




import pathlib
import math
from datetime import date
from datetime import timedelta
import copy

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


# Forget a lot of this stuff. Lets just get this working.
# take in a transaction list and a daterange
# from there we can generate a portfolio on a given day. Then generate whatever output
# then write a function that takes in a transaction list,daterange,lambda
# that should do everything

# TODO:

# add EOD price data to portfolio_list

# After:
# Compare to Monthly Statements
# get performance attribution
# save stock data
# link up API's so that we can look at saved values and hit the cheapest first


# Suggested Improvements:

# if csv is iterated backwards, the algo can probably go from 3n -> n
# create transaction by just passing the row
# add self.date
# just pass all the values to the transaction


#RISKY STUFF
# haven't checked return output with broker statements
# don't know the best way to create a pathvariable


def get_size(obj, seen=None):
    """Recursively finds size of objects in bytes"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if hasattr(obj, '__dict__'):
        for cls in obj.__class__.__mro__:
            if '__dict__' in cls.__dict__:
                d = cls.__dict__['__dict__']
                if inspect.isgetsetdescriptor(d) or inspect.ismemberdescriptor(d):
                    size += get_size(obj.__dict__, seen)
                break
    if isinstance(obj, dict):
        size += sum((get_size(v, seen) for v in obj.values()))
        size += sum((get_size(k, seen) for k in obj.keys()))
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum((get_size(i, seen) for i in obj))

    if hasattr(obj, '__slots__'): # can have __slots__ with __dict__
        size += sum(get_size(getattr(obj, s), seen) for s in obj.__slots__ if hasattr(obj, s))

    return size


# look at sizeof objects
# https://stackoverflow.com/questions/28655004/how-to-calculate-the-number-of-bytes-stored-in-object

# how to use python to find the path
# https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory

# this inner function takes the excel date and outputs a python datetime
def excel_date_to_datetime(excel_date: str,curr_year: int)->date:
    out_date = excel_date.split('/')
    out_date[0] = int(out_date[0])
    out_date[1] = int(out_date[1])

    if (curr_year > 1999):
        year_increment = 2000
    else:
        year_increment = 1900

    out_date[2] = int(out_date[2]) + year_increment

    return date(out_date[2], int(out_date[0]), int(out_date[1]) )


class Portfolio():

    closed_positions = []

    class Stock():
        def __init__(self,ticker,num_shares,first_purchase):
            self.ticker = ticker
            self.num_shares = num_shares
            self.close_price = None
            self.first_purchase_date = first_purchase

    def __init__(self,date):
        self.date = date
        self.stock_dict = {}
        self.cash_holdings = 0
    def add_transaction(self,trans):

        self.date = trans.date

        if (trans.name == "Buy"):
            if trans.ticker in self.stock_dict:
                curr_stock = self.stock_dict[trans.ticker]
                curr_stock.num_shares += trans.quantity
            else:
                self.stock_dict[trans.ticker] = self.Stock(trans.ticker,trans.quantity,trans.date)
        elif (trans.name == "Sell"):
            if trans.ticker in self.stock_dict:
                curr_stock = self.stock_dict[trans.ticker]
                curr_stock.num_shares -= trans.quantity
                if (curr_stock.num_shares == 0):
                    popped_stock = self.stock_dict.pop(trans.ticker)
                    Portfolio.closed_positions.append( (trans.ticker,popped_stock.first_purchase_date,trans.date))
                    #print("popping ", trans.ticker)
            else:
                self.stock_dict[trans.ticker] = self.Stock(trans.ticker,trans.quantity,trans.date)


        self.cash_holdings += trans.amount


class Transaction():

    def __init__(self,date):
        self.date = date
        self.name = None
        self.quantity = None #number of shares if any
        self.ticker = None   #stock ticker if a stock was bought or sold
        self.price = None
        self.commission = None
        self.amount = None

    # this takes in a dataframe row from TD Ameritrade
    # it then sets the transaction values appropriately
    # if an unexpected transaction is encountered, the program throws an error
    def addTdTransaction (self,row):

        desc = row['DESCRIPTION']

        if (desc == "ELECTRONIC NEW ACCOUNT FUNDING"):
            self.name = "Deposit"
            self.amount = row['AMOUNT']
        elif (desc[0:6] == "Bought"):
            self.name = "Buy"
            self.quantity = row['QUANTITY']
            self.ticker = row['SYMBOL']
            self.price = row['PRICE']
            self.commission = row['COMMISSION']
            self.amount = row['AMOUNT']
        elif (desc[0:17] == "ORDINARY DIVIDEND"):
            self.name = "Dividend"
            self.ticker = row['SYMBOL']
            self.amount = row['AMOUNT']
        elif (desc[0:18] == "QUALIFIED DIVIDEND"):
            self.name = "Dividend"
            self.ticker = row['SYMBOL']
            self.amount = row['AMOUNT']
        elif (desc[0:4] == "Sold"):
            self.name = "Sell"
            self.quantity = row['QUANTITY']
            self.ticker = row['SYMBOL']
            self.price = row['PRICE']
            self.commission = row['COMMISSION']
            self .amount = row['AMOUNT']
            self.reg_fee = row['REG FEE']
        elif (desc[0:7] == "ADR FEE"):
            self.amount = row['AMOUNT']
        elif (desc == "CLIENT REQUESTED ELECTRONIC FUNDING DISBURSEMENT (FUNDS NOW)"):
            self.name == "Withdrawal"
            self.amount = row['AMOUNT']
        elif (desc == "MISCELLANEOUS JOURNAL ENTRY"):
            self.name = "MISCELLANEOUS JOURNAL ENTRY"
            self.amount = row['AMOUNT']
        else:
            raise Exception("ERROR UNEXPECTED ROW ENCOUNTERED!!!!")

# Read through the transaction excel sheet
def parseTDtransactions ()->list:

    start_year = input('Please enter the year of the first TD Ameritrade CSV file: ')
    end_year = input('Please enter the year of the last TD Ameritrade CSV file: ')
    if (start_year.isdigit() and end_year.isdigit() ):
        start_year = int(start_year)
        end_year = int(end_year)
        if ( (start_year or end_year) < 1975 ):
            raise Exception("The year entered is too low")
        elif ( (start_year or end_year) > date.today().year):
            raise Exception("The year entered is too high")

    else:
        raise TypeError("Enter a valid starting year")

    path_name = "../Portfolio_Scripts/"
    transaction_file_name = "_transactions.csv"
    curr_year = end_year

    transaction_list = []

    while(curr_year >= start_year):
        curr_csv_path = path_name + str(curr_year) + transaction_file_name
        data = pd.read_csv(curr_csv_path)

    # READ TDAMERITRADE transaction csv and store as DATAFRAME
    #brokerage_transaction_data = pd.read_csv(path_name)
        for index, row in data.iterrows():

            if (row['DATE'] != "***END OF FILE***"):
                curr_date = excel_date_to_datetime(row['DATE'],curr_year)

                curr_Transaction = Transaction(curr_date)
                curr_Transaction.addTdTransaction(row)

                transaction_list.append(curr_Transaction)

        curr_year -=1

    transaction_list.reverse()
    return(transaction_list)

# take a transaction dictionary and output a list of the end of day values for:
# all the stocks held
# the cash held
# the total portfolio value

def gen_daily_holdings(transaction_list: list)->list:

    portfolio_list = []

    for trans in transaction_list:
        if (len(portfolio_list)==0):
            new_portfolio = Portfolio(trans.date)
            new_portfolio.add_transaction(trans)
            portfolio_list.append(new_portfolio)
            #print(portfolio_list[-1].date)

        elif(trans.date == portfolio_list[-1].date):
            portfolio_list[-1].add_transaction(trans)
            #print(portfolio_list[-1].date)
        else:
            new_portfolio = copy.deepcopy(portfolio_list[-1])
            new_portfolio.add_transaction(trans)
            portfolio_list.append(new_portfolio)


            #print(portfolio_list[-1].date)
    return portfolio_list

# generates a list of open positions and closed positions
def get_all_positions(port_list: list)->list:
    full_list = port_list[-1].closed_positions

    curr_portfolio = port_list[-1]
    stock_dict = curr_portfolio.stock_dict
    for i in stock_dict:
        full_list.append((i,stock_dict[i].first_purchase_date,date.today()))

    return (full_list)

def gen_hist_stockdf(all_trades):

    # to convert the timestamp to a python datetime:
    # master_df.index = map(lambda x: x.date(), master_df.index)
    first_day = "2016-01-01"
    last_day = "2020-08-25"

    ticker_set = set()

    for ticker in all_trades:
        if ticker[0] not in ticker_set:
            ticker_set.add(ticker[0])

    V_col = get_adj_close_yahoo('V',first_day,last_day)
    master_df = pd.DataFrame(V_col)
    master_df = master_df.rename(columns={"Adj Close": "V"})

    for ticker in ticker_set:
        next_col = get_adj_close_yahoo(ticker,first_day,last_day)
        master_df[ticker] = next_col

    master_df.to_parquet('master_df.parquet.gzip',compression='gzip')


    df_from_memory = pd.read_parquet('master_df.parquet.gzip')

# this function takes the transaction list and returns a list of every
# trading day. The first trading day can be accessed: out[0] last: out[-1]
def get_trade_days(trans_list,master_df):
    start_date = trans_list[0].date
    #print(trans_list[-1].date)


    date_list = master_df.index
    date_list = date_list.tolist()

    return (date_list[date_list.index(start_date):])


def gen_stock_hash(master_df,trade_days):

    master_stock_dict = {}
    ind_list = master_df.index.tolist()

    for (columnName, columnData) in master_df.iteritems():
        master_stock_dict[columnName] = {}
        for day in trade_days:
            master_stock_dict[columnName][day] = master_df[columnName][day]

    return master_stock_dict



    #this is wrong. it is incrementing day too early
def daily_ret_from_portlist(p_list, trade_days,master_stock_dict):
    # get the dates from the master_df (need to verify that these include all holidays)
    output = []
    p_ind = 0

    curr_port = p_list[p_ind]

    for day in trade_days:
        print(day)
        print(curr_port.date)
        if (day >= curr_port.date):
            if (p_ind+1 < len(p_list)):
                p_ind += 1
                curr_port = p_list[p_ind]
                #print(curr_port.date,curr_port.stock_dict,curr_port.cash_holdings)

        curr_port_val = curr_port.cash_holdings
        for ticker in curr_port.stock_dict:
            curr_port_val += ( curr_port.stock_dict[ticker].num_shares * master_stock_dict[ticker][day])
        output.append(curr_port_val)


    return(output)

def time_series_from_portlist(trans_data,trade_days,master_stock_dict):
    port_list = gen_daily_holdings(trans_data)
    daily_ret_from_portlist(port_list,trade_days,master_stock_dict)

    #print( "Portfolio list takes up " ,get_size(port_list), " bytes of memory" )


def create_numpy_stockpricearray():
    trans_list = parseTDtransactions()
    master_df = pd.read_parquet('master_df.parquet.gzip')

    trade_days = get_trade_days(trans_list,master_df)


        #print(trans.date,trans.name, trans.ticker, trans.amount)

    #print(stocks_held)
    trade_days = np.array(trade_days)
    stock_arr = pd.DataFrame(master_df).to_numpy()

    #print(stock_arr)
    #print(master_df)
    numpy_dict = {}
    for i in range (len(master_df.columns)):
        numpy_dict[master_df.columns[i]] = i

    return(trans_list,trade_days,numpy_dict)


# take in a transaction_list,trade_days,
def time_series_from_numpy(trans_list,trade_days,stock_arr,numpy_dict):
    all_stocks = {}
    index = 0

    # go through trade_days, and create a dict of all the tickers
    for trans in trans_list:
        if (trans.ticker not in all_stocks):
            all_stocks[trans.ticker] = index
            index += 1

    a = (len(trade_days), len(all_stocks))

    shares_out = np.zeros(a)

    curr_portfolio = {}



def time_portfolio_list():
    # For CR Performance history, portfolio list takes up 360755 bytes and works
    # in 0.061 seconds (looking for the size of port_list brings this up to about .1 second)

    master_df = pd.read_parquet('master_df.parquet.gzip')
    # transform TDAMERITRADE csv data into a standardized transaction data format
    transaction_data = parseTDtransactions()

    start = time.time()
    trade_days = get_trade_days(transaction_data,master_df)
    end = time.time()
    print( "get_trade_days took: " , end-start, " seconds")

    global master_stock_dict
    master_stock_dict = gen_stock_hash(master_df,trade_days)

    return(transaction_data,trade_days,master_stock_dict)

def time_series_from_trans(trans_data,trade_days,master_stock_dict):

    curr_port = Portfolio(trade_days[0])
    curr_port.add_transaction(trans_data[0])

    next_ind = 1
    output = []

    for day in trade_days:

        # if there was a transaction on the day, update curr_port with all of the days transactions
        while(next_ind<len(trans_data) and day == trans_data[next_ind].date):
            curr_port.add_transaction(trans_data[next_ind])
            next_ind +=1


        #calculate the closing portfolio value
        curr_port_val = curr_port.cash_holdings
        for ticker in curr_port.stock_dict:
            curr_port_val += ( curr_port.stock_dict[ticker].num_shares * master_stock_dict[ticker][day])
        output.append(curr_port_val)
    #print(output)


# MAIN:

#out_tuple = time_portfolio_list()
#cProfile.run('time_series_from_portlist(out_tuple[0],out_tuple[1],out_tuple[2])')

out = time_portfolio_list()
cProfile.run('time_series_from_trans(out[0],out[1],out[2])')
