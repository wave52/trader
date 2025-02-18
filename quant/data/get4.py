import akshare as ak
import pandas as pd

def get_stock_data(symbol="588000", start_date=None, end_date=None):
    """
    获取中证2000ETF的历史数据
    
    参数:
    - symbol: ETF代码，默认为中证2000ETF（588000）
    - start_date: 开始日期，格式：YYYY-MM-DD
    - end_date: 结束日期，格式：YYYY-MM-DD
    """
    try:
        # 使用akshare获取ETF数据
        df = ak.fund_etf_category_sina(symbol=symbol)
        
        # 打印原始列名，帮助调试
        print("原始数据列名:", df.columns.tolist())
        
        # 检查数据是否为空
        if df.empty:
            print(f"未能获取到ETF {symbol} 的数据")
            return None
            
        # 确保日期列存在
        date_column = None
        for col in ['date', '日期', 'Date']:
            if col in df.columns:
                date_column = col
                break
                
        if date_column is None:
            print("错误：未找到日期列")
            print("可用的列名:", df.columns.tolist())
            return None
            
        # 重命名列以匹配backtrader要求
        column_mapping = {
            date_column: 'datetime',
            'open': 'open',
            '开盘': 'open',
            'high': 'high',
            '最高': 'high',
            'low': 'low',
            '最低': 'low',
            'close': 'close',
            '收盘': 'close',
            'volume': 'volume',
            '成交量': 'volume',
            'amount': 'openinterest',
            '成交额': 'openinterest'
        }
        
        # 只重命名存在的列
        rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        
        # 将日期列转换为datetime类型
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 如果指定了日期范围，进行过滤
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['datetime'] >= start_date]
        else:
            df = df[df['datetime'] >= pd.to_datetime('20230101')]
            
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['datetime'] <= end_date]
            
        # 按日期排序
        df = df.sort_values('datetime')
        
        # 设置日期为索引
        df.set_index('datetime', inplace=True)
        
        # 确保所有必需的列都存在
        required_columns = ['open', 'high', 'low', 'close', 'volume', 'openinterest']
        for col in required_columns:
            if col not in df.columns:
                print(f"警告：缺少必需的列 {col}")
                if col == 'openinterest':  # 如果缺少openinterest列，使用volume代替
                    df['openinterest'] = df['volume']
                else:
                    return None
        
        # 确保所有数值列都是float类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'openinterest']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # 检查是否有缺失值
        if df.isnull().any().any():
            print("警告：数据中存在缺失值")
            df = df.fillna(method='ffill')  # 使用前值填充缺失值
            
        print(f"获取到 {len(df)} 条交易数据")
        print("\n数据预览:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"获取数据时发生错误: {str(e)}")
        print("请检查网络连接和代码是否正确")
        return None

if __name__ == "__main__":
    # 测试函数
    df = get_stock_data()
    if df is not None:
        print("\n数据类型检查:")
        print(df.dtypes)
        print("\n数据完整性检查:")
        print("是否有缺失值:", df.isnull().any().any()) 