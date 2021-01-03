
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
import matplotlib.pyplot as plt

# IMPORT FILES
from parseCSV import *
from gen_date_range import *
from api_pulls import *

# NOTE: 
# WHAT'S GOING ON: 
    # 1. many mini functions that compute individual stats
    # 2. assetStats() calls all those mini functions for provided list of returns and outputs {}
    #   o inputted return list is already truncated for user input of YTD/MTD/1YR etc. 
    # 3. multiHorStats() truncates return data, then passes it to assetStats()
    #   o returns {} of {}, since assetStats() returns a dictionary, and they're organized by horizon
    #   o also allows for cumulative statistics that develop one day at a time
    # 4. xxxx
    # 5. xxxx
    # 6. xxxx


###############################################################################################
## FUCNTIONS - PORTFOLIO STATISTICS

def dailyRets(close):
    # calculate an array of returns (assumes given frequency e.g. daily, monthly, etc.)
    rets= close[1:]/close[:-1]-1
    return rets


def compoundRets(rets):
    # compounds an array of returns to get return over period
    ret= np.prod(rets+1)-1
    return round(ret,3)


def beta(x, indx):
    # this takes two lists and calculates beta
    covariance= np.cov(x, indx)[0,1] # this always returns a covariance matrix which is why [0,1]
    indx_variance= np.var(indx)
    betaC= covariance/indx_variance
    return round(betaC, 3)


def alpha(ret, riskFree, beta, equityRP):
    # E(r) = alpha + risk free + beta * (equity risk premium)
    a= ret - riskFree - (beta*equityRP)
    return round(a,3)


def sharpe(portRet, riskFree):
    # excess return / standard deviation
    sr= (compoundRets(portRet)-riskFree) / np.std(portRet) # CHECK NP.STD DOF
    return round(sr,3)


def sortino(portRet, riskFree):
    # sharpe but vol is measured for negative returns only
    adjRet= [sub for sub in portRet if sub<0.0] # CHECK IF THIS EVEN WORKS
    sr= (compoundRets(portRet)-riskFree) / np.std(adjRet) # CHECK NP.STD DOF
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


###############################################################################################
## FUCNTIONS - OTHER

def retTruncate(rets, dtPortDates, sDate, eDate):
    #shortening a long list of returns    
    sIndex= bisect.bisect(dtPortDates, sDate)-1 # "-1" to literally give index position
    eIndex= bisect.bisect(dtPortDates, eDate)-1 # ^^ same as above
    
    #print('TEST')
    #print(bisect.bisect(dtPortDates, date(2010,5,5))-1)

    # creating a smaller list of returns
    truncRets = rets[sIndex:eIndex+1] # need the +1 to be inclusive (always forget this)

    return truncRets


def horizonDates(portDates, argHori):
    # generate dates that corespond w/ YTD, MTD, 1YR, etc
    # NOTE: should creat a way to see variance in estimate vs used
    #       1. if a difference extends beyond (let's say 5 days) it raises a flag

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

    #conditionals allow us to make time periods optional

    horiMoving= argHori['moving']

    if horiMoving: # passing an empty list results in moving part being skipped

        allHori= 'all' in horiMoving # this would make everything TRUE

        # need some rules (EG YTD doesn't work on YYYY/1/1)
        # for YTD, unless we're ~5days into the year, we're not going to allow for it
        test_YTD= date(year, 1,5)
        if today > test_YTD:
            if allHori or 'ytd' in horiMoving:
                ytd= date(year, 1, 1)
                while ytd not in portDates:
                    ytd= ytd+timedelta(1) #running this on new years makes this infinite
                dates['ytd']= (ytd, today)

        if allHori or '1yr' in horiMoving:
            yr1= date(year-1, month, day)
            while yr1 not in portDates:
                yr1= yr1+timedelta(1)
            dates['1yr']= (yr1, today)

        if allHori or '2yr' in horiMoving:
            yr2= date(year-2, month, day)
            while yr2 not in portDates:
                yr2= yr2+timedelta(1)
            dates['2yr']= (yr2, today)

        if allHori or '3yr' in horiMoving:
            yr3= date(year-3, month, day)
            while yr3 not in portDates:
                yr3= yr3+timedelta(1)
            dates['3yr']= (yr3, today)
    
        # Currently unsupported date ranges (sDates)
        mtd= 'NA'
        qtd= 'NA'
        yr5= 'NA'
        yr10= 'NA'
        inception= 'NA'
        custom= 'NA'

    else:
        print('No MOVING horizon (YTD, MTD, etc)')

    
    # This handles pass-through of years
    horiYears= argHori['years']

    if horiYears:
    
        for _ in horiYears:
            a= date(_,1,1)
            b= date(_,12,31)
            while a not in portDates:
                a= a+timedelta(1)
            while b not in portDates:
                b= b-timedelta(1)
            dates[str(_)]= (a, b)
    
    else: 
        print('No standalone years (2019, 2018, etc')


    # This handles pass-through of custom ranges
    horiCust= argHori['custom']

    if horiCust:

        for _ in horiCust:
            a= _[0]
            b= _[1]
            while a not in portDates:
                a= a+timedelta(1)
            while b not in portDates:
                b= b-timedelta(1)
            dates[str(_)]= (a, b)
    
    else:
        print('No custom date ranges')


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
    # NOTE: this entire function is unnecessary
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


def dateCheck(apiDates, x,y): # completely forgotten what this was originally made for
    if (apiDates[x])[1:] != (apiDates[y])[1:]:
        print('', 'DATES DO NOT MATCH UP !!!!')


###############################################################################################
## FUCNTIONS - MAIN FUNCTIONS


def assetStats(portRet, benchRet, riskFree, equityRP, sDate, eDate, argStats):

    # ####
    # NOTE: THIS IS ESSENTIALLY A FUNCTION OF FUNCTIONS (will make it easier to loop later)
    # ####

    # takes in return streams and generates all data
    # assumes return streams are okay for particular date range
    # consolidates all the different statistics into one call / return

    stats= {}

    # THESE FIRST ITEMS ARE REQUIRED VARIABLES FOR OTHER FUNCTIONS SO DEFINING THEM OUTSIDE DICT
    portTReturn= compoundRets(portRet)
    benchTReturn= compoundRets(benchRet)
    portBeta= beta(portRet, benchRet)
    portEexcessReturn= (portTReturn - benchTReturn)
    
    # These are default statistics for a vector of returns
    stats['assetTReturn']= portTReturn
    stats['benchTReturn']= benchTReturn
    stats['Beta']= portBeta
    stats['ExcessReturn']= round(portEexcessReturn,3)

    # keeping track of dates used for a horizon
    stats['sDate']= sDate
    stats['eDate']= eDate
    

    # (Optional Statistics) ITEMS THAT ARE NOT INPUTS
    allStats= 'all' in argStats # this would make everything TRUE

    if allStats or 'alpha' in argStats:
        stats['Alpha']= alpha(portTReturn, riskFree, portBeta, equityRP)
    
    if allStats or 'inforatio' in argStats:
        stats['InfoRatio']= information_ratio(portEexcessReturn, portRet, benchRet)
    
    if allStats or 'sharpe' in argStats:
        stats['Sharpe']= sharpe(portRet, riskFree)
    
    if allStats or 'treynor' in argStats:
        stats['Treynor']= treynor(portRet, portBeta, riskFree)
    
    if allStats or 'sortino' in argStats:
        # IFFY WAY OF CALCULATING VOL SUB 0 IN THIS RATIO - PLEASE CHECK
        stats['Sortino']= sortino(portRet, riskFree)

    if allStats or 'capture' in argStats:
        # HAVE NOT YET CREATED FORMULAS FOR THESE
        stats['Capture']= capture()
    
    
    return stats


# if we want, we can take date range outside of this formula rather than passing through a list
def multiHorStats(dtPortDates, portRet, benchRet, argStats, argHori):

    # really want this to be sDate, eDate, argStats
    # argHori will no longer be list, just 'cuml' or 'static'
    # different date ranges will be generated outside of the function
    # want to make this more of a black box

    # THINGS TO CHECK/CONFIRM
    print()
    print("FOLLOWING ITEMS NEED TO BE CHECKED: ")
    print()
    print('Confirm downside VOL methodology in sortino() (single line if/for)')
    print()
    print('Get the date-check thing to work')
    print()
    print('HorizonDates() needs to be checked, or return an adjustment variance') 

    # genAttri will have portfolio + assets + dates to create mhStats
    # whole process / loop required for mhStats will be done in here instead

    # create a dictionary of dictionaries
    # headline dictionary is orginzed by horizon 
    # selected horizon has a dicitonary of various statistics
    
    mhStats= {} # multi-horizon stat

    # this generates sDates for various horizons
    # REQUIRES DATETIME FORMAT
    horDates= horizonDates(dtPortDates, argHori)

    # need to truncate based on various sDates from dates
    for sub in horDates:
        # start date for horizon
        adjSDate= horDates[sub][0]
        adjEDate= horDates[sub][1]

        # Shortening return streams to match horizon
        truncPortRet=   retTruncate(portRet, dtPortDates, adjSDate, adjEDate)    
        truncBenchRet= retTruncate(benchRet, dtPortDates, adjSDate, adjEDate) 

        # can actually use exact same funciton to truncate dtPortDates
        truncDtPortDates= retTruncate(dtPortDates, dtPortDates, adjSDate, adjEDate) 
        print(truncDtPortDates[0:10])
        print()
        print()

        # Other rando assumptions needed
        riskFree= 0.010 # this needs to be calculated somehow
        equityRP= 0.045 # this needs to be calculated somehow

        # generates horizon of statistics (it's a dictionary) within the stats dictionary
        mhStats[sub]= assetStats(truncPortRet, truncBenchRet, riskFree, equityRP, adjSDate , adjEDate,  argStats)


    return mhStats


# MAIN:
if __name__ == "__main__":

    print('NOTHING TO SHOW HERE!')

else:
    print('Import: {}'.format(__file__))









