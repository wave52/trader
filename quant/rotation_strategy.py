import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RotationStrategy:
    def __init__(self, 
                 initial_capital=1000000,  # 初始资金
                 position_limit=5,         # 最大持仓数量
                 oversold_threshold=-10,   # 超跌阈值（百分比）
                 holding_period=5,         # 持有期（天）
                 stop_loss=-5):           # 止损线（百分比）
        
        self.capital = initial_capital
        self.position_limit = position_limit
        self.oversold_threshold = oversold_threshold
        self.holding_period = holding_period
        self.stop_loss = stop_loss
        self.positions = {}  # 当前持仓 {股票代码: (买入价格, 买入时间)}
        self.cash = initial_capital
        
    def get_market_data(self, stock_code, days=30):
        """获取股票行情数据"""
        try:
            # 使用akshare获取股票数据
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                  start_date=(datetime.now() - timedelta(days=days)).strftime("%Y%m%d"),
                                  end_date=datetime.now().strftime("%Y%m%d"))
            return df
        except Exception as e:
            logging.error(f"获取股票{stock_code}数据失败: {str(e)}")
            return None

    def find_oversold_stocks(self, stock_pool):
        """筛选超跌股票"""
        oversold_stocks = []
        for stock in stock_pool:
            df = self.get_market_data(stock)
            if df is None:
                continue
            
            # 计算N日跌幅
            if len(df) > 0:
                price_change = ((df['收盘'].iloc[-1] - df['收盘'].iloc[0]) / df['收盘'].iloc[0]) * 100
                if price_change <= self.oversold_threshold:
                    oversold_stocks.append((stock, price_change))
        
        # 按跌幅排序
        oversold_stocks.sort(key=lambda x: x[1])
        return oversold_stocks

    def check_stop_loss(self):
        """检查止损"""
        stocks_to_sell = []
        for stock, (buy_price, buy_time) in self.positions.items():
            df = self.get_market_data(stock, days=5)
            if df is None:
                continue
            
            current_price = df['收盘'].iloc[-1]
            price_change = ((current_price - buy_price) / buy_price) * 100
            
            # 检查止损条件
            if price_change <= self.stop_loss:
                stocks_to_sell.append(stock)
            
            # 检查持有期
            if (datetime.now() - buy_time).days >= self.holding_period:
                stocks_to_sell.append(stock)
        
        return stocks_to_sell

    def execute_trade(self, action, stock_code, price, amount):
        """执行交易"""
        if action == "buy":
            if self.cash >= price * amount:
                self.cash -= price * amount
                self.positions[stock_code] = (price, datetime.now())
                logging.info(f"买入 {stock_code}: 价格={price}, 数量={amount}")
            else:
                logging.warning(f"资金不足，无法买入 {stock_code}")
        
        elif action == "sell":
            if stock_code in self.positions:
                self.cash += price * amount
                buy_price = self.positions[stock_code][0]
                profit = ((price - buy_price) / buy_price) * 100
                del self.positions[stock_code]
                logging.info(f"卖出 {stock_code}: 价格={price}, 数量={amount}, 收益率={profit:.2f}%")

    def run_strategy(self, stock_pool):
        """运行策略"""
        # 检查止损
        stocks_to_sell = self.check_stop_loss()
        for stock in stocks_to_sell:
            if stock in self.positions:
                df = self.get_market_data(stock, days=1)
                if df is not None:
                    current_price = df['收盘'].iloc[-1]
                    self.execute_trade("sell", stock, current_price, 100)  # 假设每次交易100股

        # 寻找新的超跌股票
        if len(self.positions) < self.position_limit:
            oversold_stocks = self.find_oversold_stocks(stock_pool)
            available_positions = self.position_limit - len(self.positions)
            
            for stock, _ in oversold_stocks[:available_positions]:
                if stock not in self.positions:
                    df = self.get_market_data(stock, days=1)
                    if df is not None:
                        current_price = df['收盘'].iloc[-1]
                        # 计算可买入数量（假设每个持仓均分资金）
                        amount = int((self.cash / available_positions) / current_price / 100) * 100
                        if amount > 0:
                            self.execute_trade("buy", stock, current_price, amount)

    def get_portfolio_status(self):
        """获取当前组合状态"""
        total_value = self.cash
        for stock, (buy_price, _) in self.positions.items():
            df = self.get_market_data(stock, days=1)
            if df is not None:
                current_price = df['收盘'].iloc[-1]
                position_value = current_price * 100  # 假设每个持仓100股
                total_value += position_value
        
        return {
            "总资产": total_value,
            "现金": self.cash,
            "持仓数量": len(self.positions),
            "持仓明细": self.positions
        } 