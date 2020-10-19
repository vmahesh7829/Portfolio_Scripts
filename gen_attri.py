
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


from gen_portStats import *
from stockDataLib import *



def gen_attri():

    # SOME THOUGHTS
    #   o maybe this should be gen_default()
    #   o and then userData {} is passed into it, and then returns userData {} w/ more info in it
    #   o ........

    # typically would just get SPY for benchmark
    #   o until parseCSV is complete, will be using BRK-A as our portfolio
    all_stocks= ['BRK-A', 'SPY']

    # setting paramaters and getting datta
    sDate= date(2015,1,1)
    eDate= date.today()
    data = GetStockHashMulti(all_stocks,sDate,eDate)

    # extracting info on benchmark
    spyData= data['SPY']
    spyAdj= np.array(list(spyData.values()))
    spyDates= np.array(list(spyData.keys()))
    benchRet= dailyRets(spyAdj) 

    # extracting info on our portfolio
    # again, THIS IS TEMPORARY (=later will be using parseCV)
    portData= data['BRK-A'] 
    brkAdj= np.array(list(portData.values()))
    brkDates= np.array(list(portData.keys())) 
    portRet= dailyRets(brkAdj)

    # removing first index of dates since everything is % return now
    dtPortDates= spyDates[1:]

    # initializing {} for all user data
    userData= {}

    # setting default data on loading data
    argHori= ['ytd', 'cuml'] # chosen horizons
    argStats= ['alpha'] # chosen statistics


    userData['portfolio']= multiHorStats(dtPortDates, portRet, benchRet, eDate, argStats, argHori)

    return userData



if __name__ == "__main__":
    
    userData= gen_attri()
    print(userData)





    ###########################################################################################
    ###########################################################################################
    ############### TESTING THE CUML STUFF, THIS WILL GO INTO FIGS FILE AT SOME POINT


    # testing cumulative alpha
    x=[]
    y=[]
    for sub in userData['portfolio']['ytd_cuml']:
        x+= [userData['portfolio']['ytd_cuml'][sub]['ExcessReturn']]
        y+= [userData['portfolio']['ytd_cuml'][sub]['eDate']]
    
    data= [x,y]

    #graph the index
    fig, ax1= plt.subplots(figsize=(10,5))
    ax1.plot(x)
    ax1.set_title('YTD cuml alpha (BRK)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('alpha')
    ax1.yaxis.tick_right()
    plt.show()


else:
    print('Import: {}'.format(__file__))

