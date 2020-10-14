
__author__= 'gianluca'

# imports
import numpy as np
import requests
import datetime
from datetime import date


import cProfile
import re
from tiingo import TiingoClient


# importing functions from other files
from parseCSV import *
from gen_date_range import *
from api_pulls import *


# columns to add to output
# contribution to return: weight * return
# excess return

#FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS

# NOTE: this is for gen_attri.py
# 1. pull data
# 2. get date range
# 3, get SPY data
# 4. make sure all lists are same dimension etc
# 5. create funtions that produce analysis on data

def BigDict_Tiingo(stockList, sDate, eDate):

    # init the configurations
    config = {}

    # To reuse the same HTTP Session across API calls (and have better performance), include a session key.
    config['session'] = True

    # If you don't have your API key as an environment variable,
    # pass it in via a configuration dictionary.
    config['api_key'] = "a6051dc9e9d1140d8322de2b99755165d84f9671"

    # Initialize
    client = TiingoClient(config)

    #NOTE: 
    # Dictionary (all stocks) of lists (all days per stock) of dictionaries (data per day)
    bigDict= {}

    for stock in stockList:

        # pulling data
        # NOTE: structure:
        # get a list of dictionaries per day with info incl adjClose, volume, etc
        historical_data = client.get_ticker_price(stock,
                                                fmt='json',
                                                startDate=sDate,
                                                endDate=eDate,
                                                frequency='daily')

        # Assigning a stock pull to the big dictionary 
        bigDict[stock]= historical_data

    return bigDict


# turn big dict into dictionaries of data-level lists (e.g. adjusted close, divs)
def extractBigDict(bigDict, item):
    
    # empty dictionary
    selection= {}

    for stock in bigDict:

        # stock in bigDict -> dictionary keys (=stock strings)
        # bigDict[stock] -> list of daily dictionarys (=daily stock stats) for given stock
        # formulas pull chosen statistic (e.g. adjClose), and create a list of chosen stat
        # places list of chosen stat in dictionary of chosen stats attached to stock 

        selection[stock]=  np.array([sub[item] for sub in bigDict[stock]])
        
    return selection


# compounds an array of returns 
def compoundRets(rets):
    ret= np.prod(np.array(rets)+1)-1
    return ret


# calculate an array of returns
def dailyRets(vals):
    rets= vals[1:]/vals[:-1]-1
    return rets


def beta(x, indx):
    # this takes two lists and calculates beta
    covariance= np.cov(x, indx)[0,1] # this always returns a covariance matrix which is why [0,1]
    indx_variance= np.var(indx)
    beta= covariance/indx_variance

    return beta


def alpha(ret, rf, beta, erp):
    # E(r) = alpha + risk free + beta * (equity risk premium)
    alpha= ret - rf - (beta*erp)

    return alpha


def information_ratio(TRx, TRindx, x, indx):
    # takes in two return lists and calculates information ratio
    diff_ret= []
    for i in range(len(x)): # can't add subtract lists
        diff_ret+= [x[i]-indx[i]]

    excess_ret= TRx - TRindx
    tracking_error= np.std(diff_ret)
    info_ratio= excess_ret/tracking_error

    return info_ratio


# main function for generating attribution data
# going to use fucntions defined above to get needed output
def genAttri(stockList, sDate, eDate):

    # calling the function, detting dict of lists of dicts
    bigDict= BigDict_Tiingo(stockList, sDate, eDate)

    # extracing lists data
    adjClose= extractBigDict(bigDict, 'adjClose')
    dates= extractBigDict(bigDict, 'date')


    spyNav= adjClose['SPY']
    spyRet= dailyRets(spyNav) # remember, this will get rid of x[0]
    print(spyRet)



    #print(dates['SPY'])


    #porRet= np.array([0.015,0.022,0.005,-0.02])


    return 1




# MAIN:
if __name__ == "__main__":

    # NOTE: i commented out MAIN in ParseCSV 

    # setting function parameters
    stockList= ['AAPL', 'SPY', 'NVDA', 'TSLA', 'GS']
    sDate = "2019-12-31"
    eDate = "2020-01-05"

    x= genAttri(stockList, sDate, eDate)
    


else:
    print('Import: {}'.format(__file__))









