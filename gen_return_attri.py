
__author__= 'gianluca'

# importing modules
import pandas
import numpy as np
import matplotlib.pyplot as plt
import pandas_datareader as pdr
from datetime import date

# importing functions from other files
from gen_date_range import * 
from historical_fund_data import *
from api_pulls import *

# columns to add to output 
# contribution to return: weight * return 
# excess return

#FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS

def beta(x, indx):
    # this takes two lists and calculates beta
    covariance= np.cov(x, indx)[0,1] # this always returns a covariance matrix which is why [0,1]
    indx_variance= np.var(indx)
    beta= covariance/indx_variance

    return beta


def alpha(ret, rf, beta, erp):
    # E(r) = alpha + risk free + beta * (equity risk premium)
    alpha= ret - rf - beta*erp
    
    return alpha


def information_ratio(TRx, TRindx, x, indx): 
    # takes in two return lists and calculates information ratio
    excess_ret= TRx - TRindx
    diff_ret= []
    for i in range(len(x)): # can't add subtract lists
        diff_ret+=[x[i]-indx[i]]

    tracking_error= np.std(diff_ret)
    info_ratio= excess_ret/tracking_error

    return info_ratio





def generate_shares_df(portfolio_list):
    # this function takes the portfolio list and generates a dataframe of dates
    # with sharecounts for different holdings + cash value
    # NOTE: both NaN and 0 both imply 0 shares

    counter= 0
    breaker= 1000

    # this iterates through the portfolio list
    for i in portfolio_list: 
        #print(i) 
        #print(i.date)
        #print(i.cash_holdings)

        if counter== 0:
            # this initiates a dataframe for share counts
            shares_df= pandas.DataFrame(columns= ['cash'], index= [i.date])
        
        else:
            # following initiation, we append new portfolios
            # the new row has same columns, NEW date, and values initiate at NaN
            # in next loop, NaN is replaced w/ shares unless stock no longer exists, and stays NaN
            new_row= pandas.DataFrame(columns=shares_df.columns, index= [i.date])
            shares_df.append(new_row)

        # adding cash position: this comes from inital object, now the share attributes
        shares_df.at[i.date, 'cash']= i.cash_holdings
        
        # this iterates through the stock dictionary / attributes
        for key, value in i.stock_dict.items():
            # these are all of the stock item attirbutes
            #print(key, value.ticker, value.num_shares, value.close_price, value.first_purchase_date)

            #if the stock already exists in history, update or maintain the number of shares for date
            if key in shares_df.columns: 
                shares_df.at[i.date,key]= value.num_shares
            #if the stock does has no history, add to the dataframe, then add shares for said daite
            else:
                shares_df[key]= 0
                shares_df.at[i.date,key]= value.num_shares


        counter+=1

        if counter==breaker:
            break
        else:
            pass

    return shares_df


# MAIN: 

if __name__ == "__main__":

    # pulling in TD list data
    transaction_data = parseTDtransactions()

    # generate a list of portfolio holdings for each day from inception to present
    portfolio_list = gen_daily_holdings(transaction_data)
    full_list= get_all_positions(portfolio_list)

    # dataframe of cash/share positions
    shares_df= generate_shares_df(portfolio_list)

    # date range for the portfolio -> used for API pull
    stock_list= shares_df.colunmns[1:] #cash position is not a stock (and is first column)
    stock_list_w_index= ['SPY'] + stock_list #also want to pull SPY for alplha/beta calc etc
    end= date.today()
    start= shares_df.index[0] #oldest date pulled from shares_df

    # pulls stock close data (raw, not adjusted)
    stock_close_df= get_close_yahoo(stock_list, start, end)

    print()
    print()

    print(shares_df)


else:
    print('Imported Functions: gen_return_attri.py')
















"""

if __name__ == "__main__":


    #this will be GUI or selected by user in terminal
    time_horizon= input('Horizaon (YTD, MTD, 1YR, 2YR, 3YR): ')

    #stock list will eventually be taken from portfolio stats
    #stock_list= ['SPY'] + input('Stocks (AAPL, MSFT, ...): ').split(', ') #ask user for stocks
    stock_list= ['SPY', 'AAPL', 'MSFT', 'WM'] # will use this list for now ...
    risk_free= 0.02 # arbitrary risk free rate of return

    # Get the appropriate date range from user
    end= date.today()
    start= start_date(time_horizon) #function imported from another file
    close= get_close_yahoo(stock_list, start, end) # pulls dataframe of selected stocks

    # turning close data into index starting from 0
    index=  close / close.head(1).to_numpy() - 1
    rets= close.pct_change().dropna()
    list_len_init= len(rets.columns)
    equal_weights= np.ones(list_len_init-1)/(list_len_init-1)

    # will have equal weighting from incenption, will add feature to rebalance
    rets['Equal Weight']= (rets[stock_list[1:]]*equal_weights).sum(axis=1) #daily rebalancing

    returns= index.tail(1)
    returns['Equal Weight']= (rets['Equal Weight']+1).product()-1 #need to add equal weight return

    shares_dataframe= pandas.DataFrame(columns=close.columns, index=close.index)
    shares_dataframe.at['date':'date', 'ticker':'ticker']= 10
    
    
    
    # CHECKS CHECKS CHECKS CHECKS CHECKS CHECKS CHECKS
    # print(np.cov(rets['SPY'], rets['AAPL'])[0,1])
    # print(np.cov(rets['SPY'], rets['SPY'], ddof=1))
    # print(np.var(rets['SPY'], ddof=1))

    # formulate betas for stock list
    cols_names= rets.columns
    list_len= len(cols_names)

    betas= np.zeros(list_len)
    counter= 0
    for i in cols_names:
        spyvar= np.var(rets['SPY'], ddof=1)
        betas[counter]= np.cov(rets['SPY'], rets[i], ddof=1)[0,1] / spyvar
        counter+=1

    # formulate alphas for a stock list
    alphas= np.zeros(list_len)
    counter= 0
    for i in cols_names:
        alphas[counter]= returns[i]-risk_free-betas[counter]*(returns['SPY']-risk_free)
        counter+=1

    # excess_returns= returns-returns['SPY'] doesn't work

    output_data= pandas.DataFrame(columns= ['Returns', 'Betas', 'Alphas'], index= cols_names)
    output_data['Returns']= (100*returns.to_numpy()[0]).round(2) 
    output_data['Betas']= betas.round(2)
    output_data['Alphas']= (100*alphas).round(2)

    print()
    print()
    print('YTD Statistics: ')
    print('Note: Equal weighted portfolio assumes daily rebalancing')
    print(output_data)

else:
    print('Imported Functions: gen_return_attri.py')

"""