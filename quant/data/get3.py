import yfinance as yf
import pandas as pd

def get_stock_data(symbol="AAPL", start_date=None, end_date=None):
    """
    获取股票数据
    :param symbol: 股票代码，如'AAPL'（苹果公司）
    :param start_date: 开始日期，格式：YYYY-MM-DD
    :param end_date: 结束日期，格式：YYYY-MM-DD
    :return: DataFrame
    """
    try:
        # 获取股票数据
        stock = yf.Ticker(symbol)
        df = stock.history(
            start=start_date if start_date else "2023-01-01",
            end=end_date if end_date else "2024-02-18",
            interval="1d"
        )
        
        # 检查是否成功获取数据
        if df.empty:
            print(f"错误：未能获取到股票 {symbol} 的数据")
            return None
            
        # 重命名列以匹配之前的格式
        df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # 确保索引名称为datetime
        df.index.name = 'datetime'
        
        return df
        
    except Exception as e:
        print(f"获取数据时发生错误: {str(e)}")
        print("请检查网络连接和股票代码是否正确")
        return None

if __name__ == "__main__":
    # 获取苹果股票数据
    symbol = "AAPL"
    print(f"正在获取股票 {symbol} 的数据...")
    
    data = get_stock_data(symbol)
    
    if data is not None:
        print("\n数据前几行:")
        print(data.head())
        print("\n数据列名:", data.columns.tolist())
        print("\n数据形状:", data.shape)
        # 保存数据到CSV
        data.to_csv(f"{symbol}.csv")
        print(f"\n数据已保存到 {symbol}.csv")
    else:
        print("获取数据失败")