__author__ = 'Viswesh'

#IMPORTS
from stockDataLib import *

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

# output the numpy arrays we need to generate some stats
# clean this up so StockDataLib can be called for stock prices get rid of the
# stock dict passing

# just tell the library which stocks are needed, then ask for them.
# let the library handle the details


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
    # Deposits/Sales are positive
    # Withdrawals/Purchases are negative

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
            self.name = "Withdrawal"
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


def time_portfolio_list():


    # transform TDAMERITRADE csv data into a standardized transaction data format
    transaction_data = parseTDtransactions()

    #get all the tickers in transaction_data
    all_stocks = set()

    # go through trade_days, and create a set of all the tickers
    # create a portfolio list and make sure to deepcopy the stocks
    # in each stock, store the cost basis as well
    # also make allStocks a dict and store the first and last trading day
    for trans in transaction_data:
        if (trans.ticker!= None and trans.ticker not in all_stocks):
            all_stocks.add(trans.ticker)


    start_date = transaction_data[0].date
    end_date = transaction_data[-1].date

    stock_dict = GetStockHashMulti(all_stocks,start_date,end_date)

    # for all_stocks
    #first day is day of first transaction
    #last day is the day of the last transaction

    # This gets a list of trading days by assuming that the first stock it grabs
    # has data for the entire daterange

    first_stock = next(iter(stock_dict))

    trade_days = []
    for currDay in stock_dict[first_stock]:
        trade_days.append(currDay)


    return(transaction_data,trade_days,stock_dict)





def time_series_from_trans(trans_data,trade_days,master_stock_dict):

    curr_port = Portfolio(trade_days[0])
    next_ind = 0
    portNav = []
    dailyPortRet = []
    netFlows = 0

    print(trans_data[0].name)

    for day in trade_days:

        # if there was a transaction on the day, update curr_port with all of the days transactions
        while(next_ind<len(trans_data) and day == trans_data[next_ind].date):
            curr_port.add_transaction(trans_data[next_ind])


            # store all the withdrawals and deposits for the day
            if ( (trans_data[next_ind].name == "Withdrawal") or (trans_data[next_ind].name == "Deposit") ):
                netFlows += trans_data[next_ind].amount
            next_ind +=1



        #calculate the closing portfolio value
        curr_port_val = curr_port.cash_holdings
        for ticker in curr_port.stock_dict:
            curr_port_val += ( curr_port.stock_dict[ticker].num_shares * master_stock_dict[ticker][day])

        portNav.append(curr_port_val)

        # on first day, return is endNav/net deposits
        # this will break if the user transfers stocks from another account
        if (len(dailyPortRet)==0 ):

            if (netFlows == 0):
                print(trans_data[0].name,trans_data[0].amount)
                raise Exception("netFlows should not be 0")

            dailyPortRet.append(portNav[-1]/netFlows -1)

        elif(netFlows !=0):
            curr_port_val -= netFlows
            dailyPortRet.append(curr_port_val/portNav[-2] -1)
        else:
            dailyPortRet.append(curr_port_val/portNav[-2] -1)

        netFlows = 0


    return (portNav,dailyPortRet,trade_days)


if __name__ == "__main__":
    out = time_portfolio_list()
    output = time_series_from_trans(out[0],out[1],out[2])
    portNav = output[0]
    dailyPortRet = output[1]
    tradeDays = output[2]

    start = 10000
    for ret in dailyPortRet:
        start = start *(ret+1)
    print(start)

else:
    print('Import: {}'.format(__file__))
