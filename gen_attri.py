
__author__= 'gianluca'

# IMPORT MODULES
import numpy as np
import requests
import datetime
from datetime import date, timedelta
import cProfile
import re
from tiingo import TiingoClient
import bisect

# IMPORT FILES
from parseCSV import *
from gen_date_range import *
from api_pulls import *

# NOTE: 
# SOME STEPS TO FOLLOW / REFER TO:
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
    return round(ret,3)


def dailyRets(vals):
    # calculate an array of returns (assumes given frequency e.g. daily, monthly, etc.)
    rets= vals[1:]/vals[:-1]-1
    return rets


def beta(x, indx):
    # this takes two lists and calculates beta
    covariance= np.cov(x, indx)[0,1] # this always returns a covariance matrix which is why [0,1]
    indx_variance= np.var(indx)
    beta= covariance/indx_variance

    return round(beta, 3)


def alpha(ret, riskFree, beta, equityRP):
    # E(r) = alpha + risk free + beta * (equity risk premium)
    alpha= ret - riskFree - (beta*equityRP)

    return round(alpha,3)


def sortino():
    return 'NA'


def sharpe(portRet, riskFree):
    # excess return / standard deviation
    sr= (compoundRets(portRet)-riskFree) / np.std(portRet) # CHECK NP.STD DOF
    return round(sr,3)


def treynor(portRet, beta, riskFree):
    # sharpe ratio but with beta in denominator
    tr= (compoundRets(portRet)-riskFree) / beta # CHECK NP.STD DOF
    return round(tr,3)

def capture():
    return 'NA'


def information_ratio(portExcessReturn, x, indx):
    # takes in two return lists and calculates information ratio
    diffRet= x-indx
    trackingError= np.std(diffRet)
    infoRatio= portExcessReturn/trackingError

    return round(infoRatio,3)


def retTruncate(rets, dtPortDates, sDate, eDate):

    #shortening a long list of returns    
    sIndex= bisect.bisect(dtPortDates, sDate)
    eIndex= bisect.bisect(dtPortDates, eDate)+1 # adding 1 so that it is inclusive

    # creating a smaller list of returns
    truncRets = rets[sIndex:eIndex]

    return truncRets


def horizonDates(portDates):
    # generate dates that corespond w/ YTD, MTD, 1YR, etc
    dates= {}

    # today's features
    today= date.today()
    year= today.year
    month= today.month
    day= today.day

    # CURRENT METHOD OF MAKING DATES WORK SEEMS VERY RISKAYY ... IDK
    # NOTE: needs a beak - in some cases the horizon is out of the range ...
    # NOTE: these dates truncate lists of return data which means we don't need (-1) date b/c we're not calculating !!!
    # NOTE: QUESTION: SHOULD IT BE: (DAY or DAY+1) ????????? 

    ytd= date(year-1, 1, 1)
    while ytd not in portDates:
        ytd= ytd+timedelta(1)
    dates['ytd']= ytd

    yr1= date(year-1, month, day)
    while yr1 not in portDates:
        yr1= yr1+timedelta(1)
    dates['1yr']= yr1

    yr2= date(year-2, month, day)
    while yr2 not in portDates:
        yr2= yr2+timedelta(1)
    dates['2yr']= yr2

    yr3= date(year-3, month, day)
    while yr3 not in portDates:
        yr3= yr3+timedelta(1)
    dates['3yr']= yr3

    # Currently unsupported date ranges (sDates)
    mtd= 'NA'
    qtd= 'NA'
    yr5= 'NA'
    yr10= 'NA'
    inception= 'NA'
    custom= 'NA'

    # Additional options that should ultimately be included
    fy2020= 'NA'
    fy2019= 'NA'
    fy2018= 'NA'

    return dates    

def isoToDatetime(isoDates):
    # turning a list of iso dates into a list of datetime dates
    dtDates=  [ date(  int(sub[:4]), int(sub[5:7]), int(sub[8:10])  ) for sub in isoDates ]

    # warning in event that something goes wrong
    if len(isoDates) != len(dtDates):
        print("WARNING: isoToDatetime FUNCTION OUTPUT LEN DOES NOT MATCH")

    return dtDates


def dtToISO(dtDates):
    # turning a list of datetime dates to iso dates
    # unclear whether this function will be needed (likely for storing into cloud)
    isoDates=[]
    for sub in dtDates:
        #getting string equivalents
        year= str(sub.year)
        month= str(sub.month)
        day= str(sub.day)

        #issue is that for January, datetime returns "1", not "01"
        # if everything is 2, keep as is
        if len(month)==2 and len(day)==2:
            isoDates += ["{}-{}-{}".format(year,month,day)]       

        # if month is 1 and day is 2, add 0 before month
        if len(month)==1 and len(day)==2:
            isoDates += ["{}-{}-{}".format(year,'0'+month,day)]       
        
        # if month is 2 and day is 1, add 0 before day
        if len(month)==2 and len(day)==1:
            isoDates += ["{}-{}-{}".format(year,month,'0'+day)]       
        
        # if month is 1 and day is 1, add 0 before both
        if len(month)==1 and len(day)==1:
            isoDates += ["{}-{}-{}".format(year,'0'+month,'0'+day)]       

    # warning in event that something goes wrong
    if len(isoDates) != len(dtDates):
        print("WARNING: dtToISO FUNCTION OUTPUT LEN DOES NOT MATCH")

    return isoDates


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
    stats['portEexcessReturn']= round(portEexcessReturn,3)

    # ITEMS THAT ARE NOT INPUTS TO OTHER STATISTICS
    stats['portAlpha']= alpha(portTReturn, riskFree, portBeta, equityRP)
    stats['portInfoRatio']= information_ratio(portEexcessReturn, portRet, benchRet)
    stats['portSharpe']= sharpe(portRet, riskFree)
    stats['portTreynor']= treynor(portRet, portBeta, riskFree)


    # HAVE NOT YET CREATED FORMULAS FOR THESE
    stats['capture']= capture()
    stats['sortino']= sortino()
    

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
    
    # ASSUMING AAPL TO BE OUR PORTFOLIO
    # ALL OF THE DATA IN THIS SECTION WILL ULTIMATELY BE PROVIDED BY PARSE CSV
    
    stockList= ['BRK-A', 'SPY']

    sDate = date(2015,12,31) # in reality, sDate will be oldest date in date list provided by parseCSV
    eDate = date.today()-timedelta(1)

    # calling the function, detting dict of lists of dicts
    bigDict= BigDict_Tiingo(stockList, sDate, eDate)

    # extracing lists data
    adjClose= extractBigDict(bigDict, 'adjClose')
    apiDates= extractBigDict(bigDict, 'date')

    # getting lists specific to a stock
    benchNav= adjClose['SPY']
    portNav= adjClose['BRK-A']

    TiingoPortDates= (apiDates['BRK-A'])[1:] # first date goes away b/c it is % change
    dtPortDates=  isoToDatetime(TiingoPortDates)

    ##################################################################
    ### TEMPORARY CODE ENDS
    ##################################################################

    # going to create a dictionary of dictionaries
    # headline dictionary is orginzed by horizon 
    # selected horizon has a dicitonary of various statistics
    mhStats= {} # multi-horizon stat

    # these items will come from parseCSV
    benchRet= dailyRets(benchNav) # remember, this will get rid of x[0]
    portRet= dailyRets(portNav)

    # this generates sDates for various horizons
    # REQUIRES DATETIME FORMAT
    horDates= horizonDates(dtPortDates)

    # need to truncate based on various sDates from dates
    for sub in horDates:
        # retTruncate works w/ dateTime date format
        truncPortRet= retTruncate(portRet, dtPortDates, horDates[sub], eDate)    
        truncBenchRet= retTruncate(benchRet, dtPortDates, horDates[sub], eDate) 

        # Other rando assumptions needed
        riskFree= 0.010 # this needs to be calculated somehow
        equityRP= 0.045 # this needs to be calculated somehow

        # saves this horizon of statistics (it's a dictionary) within the stats dictionary
        mhStats[sub]= portStats(truncPortRet, truncBenchRet, riskFree, equityRP)

    return mhStats



# MAIN:
if __name__ == "__main__":

    # Running genAttri
    # Should we pass on a benchmark? 
    # Maybe we can determine appropriate benchmark based on asset exposure
    mhStats= genAttri()

    for sub in mhStats:
        print()
        print(sub, ':')
        print(mhStats[sub])
        print()
        print()



else:
    print('Import: {}'.format(__file__))









