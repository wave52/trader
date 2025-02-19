import akshare as ak
import pandas as pd

def get_stock_data(symbol="sh513380"):
    df = ak.fund_etf_hist_sina(symbol=symbol)
    df.rename(columns={
        'date': 'datetime',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume'
    }, inplace=True)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    return df

# 保存数据到CSV
data = get_stock_data()
data.to_csv("sh563300.csv")