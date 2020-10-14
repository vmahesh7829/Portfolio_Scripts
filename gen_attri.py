
__author__= 'gianluca'

# IMPORT MODULES
import numpy as np
import requests
import datetime
from datetime import date
import cProfile
import re
from tiingo import TiingoClient


# IMPORT FILES
from parseCSV import *
from gen_date_range import *
from api_pulls import *

# NOTE: 
# SOME STEPS TO FOLLOW / REFER TO
#   1. pull data
#   2. get date range
#   3, get SPY data
#   4. make sure all lists are same dimension etc
#   5. create funtions that produce analysis on data

# STILL REQUIRED:
#   1. function that truncates return list from parseCSV to match diff date ranges

###############################################################################################
## FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS ##
###############################################################################################

def BigDict_Tiingo(stockList, sDate, eDate):
    # pulls list (per stock) of daily dictionaries (includes open/close/etc.)

    # init the configurations
    config = {}

    # To reuse the same HTTP Session across API calls (and have better performance), include a session key.
    config['session'] = True

    # If you don't have your API key as an environment variable,
    # pass it in via a configuration dictionary.
    config['api_key'] = "a6051dc9e9d1140d8322de2b99755165d84f9671"

    # Initialize
    client = TiingoClient(config)

    # NOTE: 
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


def extractBigDict(bigDict, item):
    # turn big dict into dictionaries of data-level lists (e.g. adjusted close, divs)
    
    # empty dictionary
    selection= {}

    for stock in bigDict:

        # stock in bigDict -> dictionary keys (=stock strings)
        # bigDict[stock] -> list of daily dictionarys (=daily stock stats) for given stock
        # formulas pull chosen statistic (e.g. adjClose), and create a list of chosen stat
        # places list of chosen stat in dictionary of chosen stats attached to stock 

        selection[stock]=  np.array([sub[item] for sub in bigDict[stock]])
        
    return selection


def compoundRets(rets):
    # compounds an array of returns to get return over period
    ret= np.prod(np.array(rets)+1)-1
    return ret


def dailyRets(vals):
    # calculate an array of returns (assumes given frequency e.g. daily, monthly, etc.)
    rets= vals[1:]/vals[:-1]-1
    return rets


def beta(x, indx):
    # this takes two lists and calculates beta
    covariance= np.cov(x, indx)[0,1] # this always returns a covariance matrix which is why [0,1]
    indx_variance= np.var(indx)
    beta= covariance/indx_variance

    return beta


def alpha(ret, riskFree, beta, equityRP):
    # E(r) = alpha + risk free + beta * (equity risk premium)
    alpha= ret - riskFree - (beta*equityRP)

    return alpha

def sortino():
    return 'NA'

def treynor():
    return 'NA'


def information_ratio(portExcessReturn, x, indx):
    # takes in two return lists and calculates information ratio
    diffRet= x-indx
    trackingError= np.std(diffRet)
    infoRatio= portExcessReturn/trackingError

    return infoRatio


def retTrunctate(portRet, dates, sDate, eDate):
    # takes portfolio return, and turns it into the right size

    return 'NA'


def portStats(portRet, benchRet, riskFree, equityRP):

    # ####
    # NOTE: THIS IS ESSENTIALLY A FUNCTION OF FUNCTIONS (will make it easier to loop later)
    # ####

    # takes in return streams and generates all data
    # assumes return streams are okay for particular date range
    # consolidates all the different statistics into one call / return

    stats= {}

    # THESE FIRST ITEMS ARE REQUIRED VARIABLES FOR OTHER FUNCTIONS SO DEFINING THEM OUTSIDE DICT
    portTReturn= compoundRets(portRet)
    stats['portTReturn']= portTReturn

    benchTReturn= compoundRets(benchRet) # should probably use [-1]/[0]-1 # would be more accurate
    stats['benchTReturn']= benchTReturn
    
    portBeta= beta(portRet, benchRet)
    stats['portBeta']= portBeta

    portEexcessReturn= (portTReturn - benchTReturn)
    stats['portEexcessReturn']= portEexcessReturn

    # ITEMS THAT ARE NOT INPUTS TO OTHER STATISTICS
    stats['portAlpha']= alpha(portTReturn, riskFree, portBeta, equityRP)
    stats['infoRatio']= information_ratio(portEexcessReturn, portRet, benchRet)
    
    # HAVE NOT YET CREATED FORMULAS FOR THESE
    stats['capture']= "NA"
    stats['sortino']= "NA"
    stats['treynor']= "NA"

    return stats


def genAttri():
    # this function does everything from start to finish
    #   1. pulls parseCSV (temporarily just uses API data sets)
    #   2. ...
    #   3. for multiple periods -> portStats

    # takes in return streams and generates all data
    # assumes return streams are okay for particular date range

    # NOTE: assume YTD, MTD, QTD, 1YR, 2YR, 3YR, 5YR, 10YR, Inception, + custom date range
    # Is this too many? GUI would probably show first 4, then drop down arrow for additional? 
    # Going to assume the AAPL is our portfolio and benchmark is SPY


    ######################################################################
    ### TEMPORARY CODE
    ######################################################################
    stockList= ['AAPL', 'SPY']
    sDate = "2019-12-31"
    eDate = "2020-12-31"

    # calling the function, detting dict of lists of dicts
    bigDict= BigDict_Tiingo(stockList, sDate, eDate)

    # extracing lists data
    adjClose= extractBigDict(bigDict, 'adjClose')
    dates= extractBigDict(bigDict, 'date')

    benchNav= adjClose['SPY']
    portNav= adjClose['AAPL']

    ##################################################################
    ### TEMPORARY CODE ENDS
    ##################################################################


    benchRet= dailyRets(benchNav) # remember, this will get rid of x[0]
    portRet= dailyRets(portNav)

    # NOTE: NEED TO BE ABLE TO MODIFY ^^^ BASED ON DATES

    riskFree= 0.01 # this needs to change
    equityRP= 0.045 # this needs to change

    stats= portStats(portRet, benchRet, riskFree, equityRP)

    for sub in stats:
        print(sub, stats[sub])


    return stats












# MAIN:
if __name__ == "__main__":

   
    # running the function
    stats= genAttri()
    

else:
    print('Import: {}'.format(__file__))









