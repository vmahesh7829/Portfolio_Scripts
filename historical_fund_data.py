__author__ = 'Viswesh'

#IMPORTS
import pathlib
import math
from datetime import date
from datetime import timedelta
import copy

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


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




# look at sizeof objects
# https://stackoverflow.com/questions/28655004/how-to-calculate-the-number-of-bytes-stored-in-object

# how to use python to find the path
# https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory


class Portfolio():


    class Stock():
        def __init__(self,ticker,num_shares,first_purchase):
            self.ticker = ticker
            self.num_shares = num_shares
            self.close_price = None
            self.first_purchase_date = first_purchase

    closed_positions = ["this is a class variable"]

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

        if (trans.name != "Dividend"): # Ordinary and Qualified dividends
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
            self.amount = row['AMOUNT']
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

    print(full_list)


# MAIN:

# transform TDAMERITRADE csv data into a standardized transaction data format
transaction_data = parseTDtransactions()

#generate a list of portfolio holdings for each day from inception to present
portfolio_list = gen_daily_holdings(transaction_data)

get_all_positions(portfolio_list)
