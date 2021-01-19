__author__ = 'gianluca and vishy'

from datetime import date
from api_pulls import *
import time

def GetStockHash(t_data,all_stocks):
    start_date = t_data[0].date
    end_date = t_data[-1].date

    if (end_date.year == date.today().year):
        end_date = date.today()

    stockDict = getStockDict(all_stocks,start_date,end_date)

    return stockDict


def GetStockHashMulti(all_stocks,sDate,eDate):

    if (eDate.year == date.today().year):
        eDate = date.today()

    sDate = sDate.isoformat()
    eDate = eDate.isoformat()

    return tiingoMulti(all_stocks,sDate,eDate)

def tiingoListAllData(all_stocks,sDate,eDate):

    if (eDate.year == date.today().year):
        eDate = date.today()

    sDate = sDate.isoformat()
    eDate = eDate.isoformat()

    return tiingoListAllData(all_stocks,sDate,eDate)



# MAIN:

if __name__ == "__main__":
    print()
else:
    print('Import: {}'.format(__file__))
