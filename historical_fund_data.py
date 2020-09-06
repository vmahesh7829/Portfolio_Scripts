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

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# TODO:

# After:
# get performance attribution
# save stock data
# link up API's so that we can look at saved values and hit the cheapest first




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

# generates a list of open positions and closed positions
def get_all_positions(port_list: list)->list:
    full_list = port_list[-1].closed_positions

    curr_portfolio = port_list[-1]
    stock_dict = curr_portfolio.stock_dict
    for i in stock_dict:
        full_list.append((i,stock_dict[i].first_purchase_date,date.today()))

    return (full_list)

def binary_search(d_list,val):
    def search_func(d_list,val,first,last):
        mid_ind = (first+last)//2
        mid = d_list[mid_ind]

        if (val < mid):
            return search_func(d_list,val,first,mid_ind-1)
        elif (val > mid):
            return search_func(d_list,val,mid_ind+1,last)
        else:
            return mid_ind
    return search_func(d_list,val,0,len(d_list)-1)

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



def create_numpy_stockpricearray():
    trans_list = parseTDtransactions()
    master_df = pd.read_parquet('master_df.parquet.gzip')

    trade_days = get_trade_days(trans_list,master_df)


        #print(trans.date,trans.name, trans.ticker, trans.amount)
    #print(stocks_held)
    trade_days = np.array(trade_days)

    stock_arr = pd.DataFrame(master_df).to_numpy()
    stock_arr = stock_arr.transpose()

    index_arr = master_df.index

    first_ind = binary_search(index_arr,trade_days[0])
    last_ind = binary_search(index_arr,trade_days[-1])
    nump_inds = (first_ind,last_ind)


    #print(master_df)
    #print(stock_arr)
    #print(master_df)
    numpy_dict = {}
    for i in range (len(master_df.columns)):
        numpy_dict[master_df.columns[i]] = i

    return(trans_list,trade_days,stock_arr,numpy_dict,nump_inds)


def gen_numpy_pos_list(curr_port,args):
    all_stocks = args[0]
    numpy_dict = args[1]

    nump_arr = np.zeros((1, len(all_stocks)+1))
    nump_arr = nump_arr[0]

    nump_arr[0] = curr_port.cash_holdings

    for stock in all_stocks:
        s_ind = numpy_dict[stock]
        if (stock in curr_port.stock_dict):
            nump_arr[s_ind+1] = curr_port.stock_dict[stock].num_shares

    return nump_arr


# take in a transaction_list,trade_days,
def time_series_from_numpy(trans_list,trade_days,stock_arr,numpy_dict,nump_inds):
    all_stocks = {}
    index = 0

    first_day = trade_days[0]
    last_day = trade_days[-1]

    # go through trade_days, and create a dict of all the tickers
    for trans in trans_list:
        if (trans.ticker != None and trans.ticker not in all_stocks):
            all_stocks[trans.ticker] = index
            index += 1

    #Todo: make eod_prices into a numpy array


    a = (len(all_stocks)+1, len(trade_days))
    eod_prices = np.zeros(a)

    i = 1
    for stock in all_stocks:
        curr_ind = numpy_dict[stock]
        position_arr = stock_arr[curr_ind]
        position_arr = position_arr[nump_inds[0]:nump_inds[1]+1]
        eod_prices[i] = position_arr
        i +=1
    eod_prices = eod_prices.transpose()


    args = (all_stocks,numpy_dict)
    num_shares = iter_port(trans_list,trade_days,gen_numpy_pos_list,args)

    #turns days_holdings from a python list to a numpy array
    # iter_port should probably just return a numpy array
    return (eod_prices,num_shares)




# args = master_stock_dict
def get_eod_port_val(curr_port,args):
    day = curr_port.date
    master_stock_dict = args
    curr_port_val = curr_port.cash_holdings
    for ticker in curr_port.stock_dict:
        curr_port_val += ( curr_port.stock_dict[ticker].num_shares * master_stock_dict[ticker][day])
    return curr_port_val


def iter_port(trans_data,trade_days,lam,args):
    curr_port = Portfolio(trade_days[0])
    curr_port.add_transaction(trans_data[0])
    output = []

    next_ind = 1

    for day in trade_days:

        # if there was a transaction on the day, update curr_port with all of the days transactions
        while(next_ind<len(trans_data) and day == trans_data[next_ind].date):
            curr_port.add_transaction(trans_data[next_ind])
            next_ind +=1
        curr_port.date = day
        output.append(lam(curr_port,args))


    output = np.stack(output)
    return output

def time_portfolio_list():
    # For CR Performance history, portfolio list takes up 360755 bytes and works
    # in 0.061 seconds (looking for the size of port_list brings this up to about .1 second)

    # by not using portfolio_list time takes 0.006 seconds a 10x speedup

    master_df = pd.read_parquet('master_df.parquet.gzip')
    # transform TDAMERITRADE csv data into a standardized transaction data format
    transaction_data = parseTDtransactions()


    trade_days = get_trade_days(transaction_data,master_df)

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


# MAIN:
#cProfile.run('time_series_from_trans(out[0],out[1],out[2])')

# this loops through all transactions in 0.007 seconds
# to output in type numpy array takes this to 0.01 seconds

out = time_portfolio_list()
returns = iter_port(out[0],out[1],get_eod_port_val,out[2])
print(returns)
#cProfile.run('iter_port(out[0],out[1],get_eod_port_val,out[2])')


# this takes 0.017 seconds
#out = create_numpy_stockpricearray()
#both_matrices = time_series_from_numpy(out[0],out[1],out[2],out[3],out[4])
#cProfile.run('time_series_from_numpy(out[0],out[1],out[2],out[3],out[4])')

#print((both_matrices[1][0]),both_matrices[1][1])
