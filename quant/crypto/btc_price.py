import requests
import pandas as pd
import ta
import time
import numpy as np
from datetime import datetime, timedelta

def get_current_price(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    return float(data['price'])

def get_historical_data(symbol="BTCUSDT", interval="1h", limit=1000):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    
    return df

def calculate_support_resistance_levels(symbol="BTCUSDT"):
    timeframes = {'15m': 1000, '1h': 1000, '4h': 1000, '1d': 1000}
    levels = {}
    
    for timeframe, limit in timeframes.items():
        df = get_historical_data(symbol, timeframe, limit)
        
        window = {'15m': 14, '1h': 24, '4h': 50, '1d': 200}[timeframe]
        
        indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=window, window_dev=2)
        df['bb_high'] = indicator_bb.bollinger_hband()
        df['bb_low'] = indicator_bb.bollinger_lband()
        
        df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=window).rsi()

        df['trend'] = np.where(df['close'] > df['close'].shift(window), 1, -1)
        
        resistance_levels = df[(df['rsi'] > 70) & (df['close'] > df['bb_high'])  | (df['trend'] == -1)]['close'].dropna()
        support_levels = df[(df['rsi'] < 30) & (df['close'] < df['bb_low']) | (df['trend'] == 1)]['close'].dropna()
        
        levels[timeframe] = {
            'R': [{"type": "R", "price": price, "timeframe": timeframe, "strength": count} 
                  for price, count in resistance_levels.value_counts().items()],
            'S': [{"type": "S", "price": price, "timeframe": timeframe, "strength": count} 
                  for price, count in support_levels.value_counts().items()]
        }
        
        levels[timeframe]['R'] = sorted(levels[timeframe]['R'], key=lambda x: x['strength'], reverse=True)
        levels[timeframe]['S'] = sorted(levels[timeframe]['S'], key=lambda x: x['strength'], reverse=True)
    
    return levels

def analyze_levels_with_current_price(levels, current_price):
    resistance_levels = []
    support_levels = []
    
    for timeframe in levels:
        for level in levels[timeframe]['R'] + levels[timeframe]['S']:
            level['percentage'] = ((level['price'] - current_price) / current_price) * 100
        
        resistance_levels.extend([level for level in levels[timeframe]['R'] if level['price'] > current_price])
        support_levels.extend([level for level in levels[timeframe]['S'] if level['price'] < current_price])
    
    return resistance_levels, support_levels

def generate_support_resistance_map(current_price, resistance_levels, support_levels):
    print("🗺BTCUSDT 价格地形图")
    print("====================================")
    print("支撑阻力分布 (S=支撑, R=阻力):")
    
    min_price, max_price = 49000, 71000
    levels_per_timeframe = 2  # 每个时间级别显示的支撑/阻力位数量
    
    timeframes = ['15m', '1h', '4h', '1d']
    filtered_levels = []
    
    for timeframe in timeframes:
        r_levels = [level for level in resistance_levels if level['timeframe'] == timeframe and min_price <= level['price'] <= max_price]
        s_levels = [level for level in support_levels if level['timeframe'] == timeframe and min_price <= level['price'] <= max_price]
        
        filtered_levels.extend(r_levels[:levels_per_timeframe])
        filtered_levels.extend(s_levels[:levels_per_timeframe])
    
    filtered_levels = sorted(filtered_levels + [{"type": None, "price": current_price, "timeframe": None, "percentage": 0}], key=lambda x: x["price"], reverse=True)
    
    for level in filtered_levels:
        if level['price'] == current_price:
            print(f">>> {level['price']:.0f} (当前价格⛳️)")
        else:
            print(f"{level['type']} {level['price']:.0f} ({level['timeframe']}) {level['percentage']:+.2f}%")
    
    print("------------------------------------")
    print("支撑阻力统计（涨跌难度):")
    ranges = [1, 3, 5, 10]
    for r in ranges:
        support_count = sum(1 for level in support_levels if abs(level['percentage']) <= r)
        resistance_count = sum(1 for level in resistance_levels if abs(level['percentage']) <= r)
        print(f"{r}% 范围: 支撑 {support_count} | 阻力 {resistance_count}")

current_price = get_current_price()
support_resistance_levels = calculate_support_resistance_levels()
resistance_levels, support_levels = analyze_levels_with_current_price(support_resistance_levels, current_price)


print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
generate_support_resistance_map(current_price, resistance_levels, support_levels)