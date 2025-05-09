import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import json
import os

class StockDataCollector:
    """股票数据收集器"""
    def __init__(self):
        self.stock_info = None
        
    def get_all_stock_data(self, max_retries=3):
        """获取所有股票的基本面数据"""
        for retry in range(max_retries):
            try:
                # 获取所有A股实时行情数据
                stock_df = ak.stock_zh_a_spot_em()
                
                # 打印列名，用于调试
                print("原始数据列名:", stock_df.columns.tolist())
                
                # 重命名列以匹配我们需要的格式
                stock_df = stock_df.rename(columns={
                    '市盈率-动态': '市盈率',
                    '60日涨跌幅': 'ROE',  # 暂时用60日涨跌幅替代ROE
                    '最新价': '当前价格'  # 确保价格列名一致
                })
                
                # 确保必要的列存在
                required_columns = ['代码', '名称', 'ROE', '市盈率', '市净率', '总市值', '当前价格']
                if not all(col in stock_df.columns for col in required_columns):
                    print("缺少必要的数据列，实际列名:", stock_df.columns.tolist())
                    return False
                
                # 将空值和异常值替换为 NaN
                stock_df['ROE'] = pd.to_numeric(stock_df['ROE'], errors='coerce')
                stock_df['市盈率'] = pd.to_numeric(stock_df['市盈率'], errors='coerce')
                stock_df['市净率'] = pd.to_numeric(stock_df['市净率'], errors='coerce')
                stock_df['总市值'] = pd.to_numeric(stock_df['总市值'], errors='coerce')
                stock_df['当前价格'] = pd.to_numeric(stock_df['当前价格'], errors='coerce')
                
                # 将总市值从元转换为亿元
                stock_df['总市值'] = stock_df['总市值'] / 100000000
                
                # 过滤条件：
                # 1. 只保留主板股票（以60或00开头的股票代码）
                #stock_df = stock_df[stock_df['代码'].str.match('^(60|00)')]
                
                # 2. 股价小于20元
                #stock_df = stock_df[stock_df['当前价格'] < 20]
                
                # 3. 剔除ST股票
                #stock_df = stock_df[~stock_df['名称'].str.contains('ST|退')]
                
                # 4. 剔除数据不完整的股票
                #stock_df = stock_df.dropna(subset=['ROE', '市盈率', '市净率', '总市值', '当前价格'])
                
                print(f"\n过滤后剩余股票数量: {len(stock_df)}")
                
                self.stock_info = stock_df
                return True
            except Exception as e:
                print(f"获取股票数据时出错 (尝试 {retry+1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
        return False

    def get_stock_history(self, stock_code, max_retries=3):
        """获取单个股票的历史数据"""
        for retry in range(max_retries):
            try:
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"),
                    end_date=datetime.now().strftime("%Y%m%d"),
                    adjust="qfq"
                )
                time.sleep(random.uniform(0.5, 2))
                return df
            except Exception as e:
                print(f"获取股票 {stock_code} 历史数据时出错 (尝试 {retry+1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
        return None

    def calculate_momentum(self, df):
        """计算动量因子"""
        try:
            if len(df) < 60:  # 至少需要60个交易日的数据
                return None
            return (df['收盘'].iloc[-1] / df['收盘'].iloc[0] - 1) * 100
        except Exception as e:
            print(f"计算动量因子时出错: {str(e)}")
            return None

    def collect_and_save_data(self, output_file='stock_data.json'):
        """收集数据并保存到JSON文件"""
        if not self.get_all_stock_data():
            print("获取股票数据失败")
            return False

        factor_data = []
        print("\n开始收集股票数据...")
        
        for _, stock in self.stock_info.iterrows():
            stock_code = stock['代码']
            print(f"\n处理股票 {stock_code}")
            
            try:
                # 获取历史数据计算动量
                price_data = self.get_stock_history(stock_code)
                if price_data is None:
                    continue
                
                momentum = self.calculate_momentum(price_data)
                
                # 获取其他因子
                roe = float(stock['ROE'])
                pe = float(stock['市盈率'])
                pb = float(stock['市净率'])
                total_mv = float(stock['总市值'])
                
                # 数据合理性检查
                if any([
                    momentum is None,
                    np.isnan(roe) or abs(roe) > 100,
                    np.isnan(pe) or pe <= 0 or pe > 1000,
                    np.isnan(pb) or pb <= 0 or pb > 50,
                    np.isnan(total_mv) or total_mv <= 0
                ]):
                    continue
                
                factor_data.append({
                    'stock_code': stock_code,
                    'name': stock['名称'],
                    'momentum': momentum,
                    'roe': roe,
                    'pe': pe,
                    'pb': pb,
                    'total_mv': total_mv,
                    'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f"股票 {stock_code} 数据收集完成")
                
            except Exception as e:
                print(f"处理股票 {stock_code} 时出错: {str(e)}")
                continue

        # 保存数据到JSON文件
        if factor_data:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(factor_data, f, ensure_ascii=False, indent=2)
            print(f"\n数据已保存到 {output_file}")
            return True
        return False

class StockSelector:
    """股票选择器"""
    def __init__(self, stock_pool=None):
        self.stock_pool = stock_pool
        self.factor_data = pd.DataFrame()
        self.selected_stocks = []
        
    def normalize_factor(self, series):
        """对因子进行标准化"""
        try:
            if len(series) <= 1:
                return series
            return (series - series.mean()) / series.std()
        except Exception as e:
            print(f"标准化因子时出错: {str(e)}")
            return series

    def select_stocks(self, data_file='stock_data.json', top_n=10):
        """从JSON文件读取数据并选股"""
        try:
            # 读取JSON数据
            if not os.path.exists(data_file):
                print(f"数据文件 {data_file} 不存在")
                return []
                
            with open(data_file, 'r', encoding='utf-8') as f:
                factor_data = json.load(f)
            
            self.factor_data = pd.DataFrame(factor_data)
            
            # 如果指定了股票池，进行过滤
            if self.stock_pool is not None:
                self.factor_data = self.factor_data[self.factor_data['stock_code'].isin(self.stock_pool)]
            
            if len(self.factor_data) == 0:
                print("没有获取到有效数据")
                return []

            # 标准化因子
            self.factor_data['momentum_norm'] = self.normalize_factor(self.factor_data['momentum'])
            # self.factor_data['roe_norm'] = self.normalize_factor(self.factor_data['roe'])
            self.factor_data['pe_norm'] = self.normalize_factor(1 / self.factor_data['pe'])
            self.factor_data['pb_norm'] = self.normalize_factor(1 / self.factor_data['pb'])

            # 计算综合得分（重新分配权重），暂时不计算ROE
            # self.factor_data['total_score'] = (
            #     self.factor_data['momentum_norm'] * 0.3 +
            #     self.factor_data['roe_norm'] * 0.4 +
            #     self.factor_data['pe_norm'] * 0.15 +
            #     self.factor_data['pb_norm'] * 0.15
            # )
            self.factor_data['total_score'] = (
                self.factor_data['momentum_norm'] * 0.4 +
                self.factor_data['pe_norm'] * 0.3 +
                self.factor_data['pb_norm'] * 0.3
            )

            # 选择得分最高的股票
            self.selected_stocks = self.factor_data.nlargest(top_n, 'total_score')
            return self.selected_stocks
            
        except Exception as e:
            print(f"选股过程中出错: {str(e)}")
            return []

    def print_results(self):
        """打印选股结果"""
        print("\n====== 选股结果 ======")
        print(f"共筛选出 {len(self.selected_stocks)} 只股票")
        
        for _, stock in self.selected_stocks.iterrows():
            print(f"\n股票代码: {stock['stock_code']}")
            print(f"股票名称: {stock['name']}")
            print(f"综合得分: {stock['total_score']:.2f}")
            print(f"动量因子: {stock['momentum']:.2f}%")
            print(f"ROE: {stock['roe']:.2f}%")
            print(f"市盈率: {stock['pe']:.2f}")
            print(f"市净率: {stock['pb']:.2f}")
            print(f"总市值: {stock['total_mv']:.2f}亿")

def collect_data():
    """收集数据的主函数"""
    collector = StockDataCollector()
    collector.collect_and_save_data()

def select_stocks():
    """选股的主函数"""
    # 测试用的股票池（以优质蓝筹股为例）
    test_stocks = [
        '600519',  # 贵州茅台
        '000858',  # 五粮液
        '600036',  # 招商银行
        '601318',  # 中国平安
        '600276',  # 恒瑞医药
    ]
    
    # 创建选股器实例
    selector = StockSelector()  # 不传入stock_pool则选择全市场股票
    
    # 执行选股
    selected = selector.select_stocks(top_n=10)
    
    # 打印结果
    selector.print_results()

if __name__ == "__main__":
    # 可以根据需要选择执行数据收集还是选股
    # collect_data()  # 收集数据
    select_stocks()  # 执行选股