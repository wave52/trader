import requests
import pandas as pd
import time
from datetime import datetime

def get_btc_data():
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1d",
        "limit": 500
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('timestamp')
    df = df[['close', 'volume']].astype(float)
    return df

def calculate_price_sentiment(df):
    price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    if price_change > 0.05:
        return 2  # 非常乐观
    elif price_change > 0.02:
        return 1  # 乐观
    elif price_change < -0.05:
        return -2  # 非常悲观
    elif price_change < -0.02:
        return -1  # 悲观
    else:
        return 0  # 中性

def calculate_volume_sentiment(df):
    avg_volume = df['volume'].mean()
    last_volume = df['volume'].iloc[-1]
    if last_volume > avg_volume * 1.5:
        return 1  # 交易量增加，积极信号
    elif last_volume < avg_volume * 0.5:
        return -1  # 交易量减少，消极信号
    else:
        return 0  # 交易量正常

def calculate_profit_index(df):
    # 这里使用一个简单的方法计算获利指数，您可以根据需要调整
    price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    volume_change = (df['volume'].iloc[-1] - df['volume'].mean()) / df['volume'].mean()
    profit_index = (price_change + volume_change) * 50 + 50  # 将范围调整到0-100%
    return max(0, min(100, profit_index))  # 确保结果在0-100%之间

def calculate_overall_sentiment():
    df = get_btc_data()
    price_sentiment = calculate_price_sentiment(df)
    volume_sentiment = calculate_volume_sentiment(df)
    profit_index = calculate_profit_index(df)

    overall_sentiment = price_sentiment + volume_sentiment
    
    if overall_sentiment > 2:
        sentiment_text = "极度乐观 🤩"
    elif overall_sentiment > 0.5:
        sentiment_text = "乐观 😊"
    elif overall_sentiment < -2:
        sentiment_text = "极度悲观 😰"
    elif overall_sentiment < -0.5:
        sentiment_text = "悲观 😕"
    else:
        sentiment_text = "中性 😐"

    return sentiment_text, profit_index

def main():
    sentiment_text, profit_index = calculate_overall_sentiment()
    print(f"⏰ 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💹 获利指数: {profit_index:.2f}%")
    print(f"🌡️ 市场状态: {sentiment_text}")
    print("------------------------")

if __name__ == "__main__":
    main()