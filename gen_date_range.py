
# goal is to return correct starting dates 
from pandas.tseries.offsets import BMonthEnd #this allows for end of month
from datetime import date


def start_date(option):
    # this is needed for month to date
    offset = BMonthEnd()

    today= date.today()
    year= today.year
    month= today.month
    day= today.day

    #Month to date is a little more complicated
    init= offset.rollback(today)

    # the start dates
    Month_TD= date(init.year, init.month, init.day)
    Year_TD= date(year-1, 12, 31)
    One_YR= date(year-1, month, day)
    Two_YR= date(year-2, month, day)
    Three_YR= date(year-3, month, day)
    sol= {'YTD':Year_TD, 'MTD': Month_TD, '1YR': One_YR, '2YR': Two_YR, '3YR':Three_YR}

    return sol[option]