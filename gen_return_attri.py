
__author__= 'gianluca'

import pandas
import numpy as np
import matplotlib.pyplot as plt
import pandas_datareader as pdr
from datetime import date
from gen_date_range import * #this is file w/ date range functions


# columns to add to output 
# contribution to return: weight * return 
# excess return

#FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS FUCNTIONS

def get_adj_close(stock_list, start, end):
    df= pdr.get_data_yahoo(stock_list, end=end, start=start) #grab data from yahoo
    adjclose= df['Adj Close'] #isolate the adj close figures
    # print(close) #pringting close data to the console
    return adjclose





# MAIN: 

#this will be GUI or selected by user in terminal
time_horizon= input('Horizaon (YTD, MTD, 1YR, 2YR, 3YR): ')

#stock list will eventually be taken from portfolio stats
#stock_list= ['SPY'] + input('Stocks (AAPL, MSFT, ...): ').split(', ') #ask user for stocks
stock_list= ['SPY', 'AAPL', 'MSFT', 'WM'] # will use this list for now ...
risk_free= 0.02 # arbitrary risk free rate of return

# Get the appropriate date range from user
end= date.today()
start= start_date(time_horizon) #function imported from another file
adj_close= get_adj_close(stock_list, start, end) # pulls dataframe of selected stocks



# turning close data into index starting from 0
index=  adj_close / adj_close.head(1).to_numpy() - 1
rets= adj_close.pct_change().dropna()
list_len_init= len(rets.columns)
equal_weights= np.ones(list_len_init-1)/(list_len_init-1)

# will have equal weighting from incenption, will add feature to rebalance
rets['Equal Weight']= (rets[stock_list[1:]]*equal_weights).sum(axis=1) #daily rebalancing

returns= index.tail(1)
returns['Equal Weight']= (rets['Equal Weight']+1).product()-1 #need to add equal weight return

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

