import akshare as ak
import pandas as pd 

# 获取沪深300历史数据（示例）
def get_stock_data(symbol="sh000300", period="daily"):
    df = ak.stock_zh_index_daily(symbol=symbol)
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
data.to_csv("sh000300.csv")