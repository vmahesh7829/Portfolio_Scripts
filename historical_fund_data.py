__author__ = 'Viswesh'

#IMPORTS
from api_pulls import *
import pandas_datareader as pdr

from collections.abc import Mapping, Container

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


# this function takes the transaction list and returns a list of every
# trading day. The first trading day can be accessed: out[0] last: out[-1]
def get_trade_days(trans_list,master_df):
    start_date = trans_list[0].date
    #print(trans_list[-1].date)


    date_list = master_df.index
    date_list = date_list.tolist()

    return (date_list[date_list.index(start_date):])

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



# Not used anymore. This shows how to loop through transactions to generates
# portfolio statististics such as EOD value.

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

    for ticker in curr_port.stock_dict:
        print(ticker,curr_port.stock_dict[ticker].num_shares)
    return output


# MAIN:


# to output in type numpy array takes this to 0.01 seconds

out = time_portfolio_list()
returns = time_series_from_trans(out[0],out[1],out[2])
print(returns)


# This creates a matrix of positions and a matrix of stock prices
# this takes 0.017 seconds

#out = create_numpy_stockpricearray()
#output = gen_nump_matrices(out[0],out[1],out[2],out[3],out[4])
#cProfile.run('gen_nump_matrices(out[0],out[1],out[2],out[3],out[4])')



# not sure if the price data is accurate.
# jpm has the same price on 2 days
#master_df = pd.read_parquet('master_df.parquet.gzip')
#print(output[3])
#print(output[0][0])
#print(output[0][1])
#print(master_df['JPM'][92]) (92 was the index of 5/16/2016)
#print(master_df['JPM'][93])
#print((both_matrices[1][0]),both_matrices[1][1])
