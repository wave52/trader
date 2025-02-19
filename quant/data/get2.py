import akshare as ak
import pandas as pd 

def get_stock_data(symbol="600126", start_date=None, end_date=None):
    """
    获取A股股票数据
    :param symbol: 股票代码，如'603915'（国茂股份）
    :param start_date: 开始日期，格式：YYYYMMDD
    :param end_date: 结束日期，格式：YYYYMMDD
    :return: DataFrame
    """
    try:
        # 确保股票代码格式正确
        if not symbol.startswith(('0', '3', '6')):
            print(f"错误：无效的股票代码 {symbol}")
            return None
            
        # 使用正确的函数获取A股历史数据
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date="20240101" if start_date is None else start_date,
            end_date="20250218" if end_date is None else end_date,
            adjust="qfq"  # 前复权数据
        )
        
        # 检查是否成功获取数据
        if df.empty:
            print(f"错误：未能获取到股票 {symbol} 的数据")
            return None
            
        print("原始数据列名:", df.columns.tolist())
        print("\n原始数据前几行:")
        print(df.head())
        
        # 根据实际列名进行重命名
        column_mapping = {
            '日期': 'datetime',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'openinterest'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 转换日期格式
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 设置日期为索引
        df.set_index('datetime', inplace=True)
        
        return df
        
    except Exception as e:
        print(f"获取数据时发生错误: {str(e)}")
        print("请检查网络连接和股票代码是否正确")
        return None

if __name__ == "__main__":
    # 获取数据
    symbol = "603915"  # 国茂股份
    print(f"正在获取股票 {symbol} 的数据...")
    
    data = get_stock_data(symbol)
    
    if data is not None:
        print("\n处理后的数据前几行:")
        print(data.head())
        print("\n处理后的数据列名:", data.columns.tolist())
        print("\n数据形状:", data.shape)
        # 保存数据到CSV
        data.to_csv(f"{symbol}.csv")
        print(f"\n数据已保存到 {symbol}.csv")
    else:
        print("获取数据失败")