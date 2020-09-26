
__author__ = 'gianluca'


# TODO:

# at some point need to add API functoins for IEX cloud


import pandas_datareader as pdr

# pulls closing price data from yahoo fianance
def get_close_yahoo(stock_list, start, end):
    df= pdr.get_data_yahoo(stock_list, end=end, start=start) #grab data from yahoo
    close= df['Close'] #isolate the close figures
    # print(close) #pringting close data to the console
    return close

# pulls adjusted closing price data from yahoo finance
def get_adj_close_yahoo(stock_list, start, end):
    df= pdr.get_data_yahoo(stock_list, end=end, start=start) #grab data from yahoo
    adjclose= df['Adj Close'] #isolate the close figures
    # print(close) #pringting close data to the console
    return adjclose

def gen_hist_stockdf(all_trades):

    # to convert the timestamp to a python datetime:
    # master_df.index = map(lambda x: x.date(), master_df.index)
    first_day = "2016-01-01"
    last_day = "2020-08-25"

    ticker_set = set()

    for ticker in all_trades:
        if ticker[0] not in ticker_set:
            ticker_set.add(ticker[0])

    V_col = get_adj_close_yahoo('V',first_day,last_day)
    master_df = pd.DataFrame(V_col)
    master_df = master_df.rename(columns={"Adj Close": "V"})

    for ticker in ticker_set:
        next_col = get_adj_close_yahoo(ticker,first_day,last_day)
        master_df[ticker] = next_col

    master_df.to_parquet('master_df.parquet.gzip',compression='gzip')


    df_from_memory = pd.read_parquet('master_df.parquet.gzip')



# find all the stock data that's in the database and load it to the dict.
# make API calls for the rest
def gen_stock_hash(master_df,trade_days):

    master_stock_dict = {}
    ind_list = master_df.index.tolist()

    for (columnName, columnData) in master_df.iteritems():
        master_stock_dict[columnName] = {}
        for day in trade_days:
            master_stock_dict[columnName][day] = master_df[columnName][day]

    return master_stock_dict



def create_numpy_stockpricearray():
    trans_list = parseTDtransactions()
    master_df = pd.read_parquet('master_df.parquet.gzip')

    trade_days = get_trade_days(trans_list,master_df)


        #print(trans.date,trans.name, trans.ticker, trans.amount)
    #print(stocks_held)
    trade_days = np.array(trade_days)

    stock_arr = pd.DataFrame(master_df).to_numpy()
    stock_arr = stock_arr.transpose()

    index_arr = master_df.index

    first_ind = binary_search(index_arr,trade_days[0])
    last_ind = binary_search(index_arr,trade_days[-1])
    nump_inds = (first_ind,last_ind)


    #print(master_df)
    #print(stock_arr)
    #print(master_df)
    numpy_dict = {}
    for i in range (len(master_df.columns)):
        numpy_dict[master_df.columns[i]] = i

    return(trans_list,trade_days,stock_arr,numpy_dict,nump_inds)

# MAIN:

if __name__ == "__main__":
    print()
else:
    print('Import: {}'.format(__file__))
