
__author__ = 'gianluca and vishy'

from datetime import date
import pandas_datareader as pdr
from api_pulls import *

<<<<<<< HEAD
def GetStockHash(t_data,all_stocks):
=======

def getStockHash(t_data,all_stocks):
>>>>>>> a9a2990b2a2aa3070ef021ed674037378f71ea91
    start_date = t_data[0].date
    end_date = t_data[-1].date

    if (end_date.year == date.today().year):
        end_date = date.today()


    stockDict = getStockDict(all_stocks,start_date,end_date)
    return stockDict

<<<<<<< HEAD
    # call tiingo api. (send ticker-list start date and end date)
    # hash the json response and get a list of all the trading days
    # return the trade day list and the stock price dictionary
=======
>>>>>>> a9a2990b2a2aa3070ef021ed674037378f71ea91

# MAIN:

if __name__ == "__main__":
    print()
else:
    print('Import: {}'.format(__file__))
