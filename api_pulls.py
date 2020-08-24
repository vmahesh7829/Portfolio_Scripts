
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


    