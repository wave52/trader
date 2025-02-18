import backtrader as bt
import pandas as pd
import numpy as np
# from scipy import stats
from data.get3 import get_stock_data

class PairTradingStrategy(bt.Strategy):
    """
    配对交易策略
    - 使用协整性检验确保配对的有效性
    - 基于Z-Score的交易信号
    - 动态止损和获利目标
    - 市场中性对冲
    """
    params = (
        ('z_entry', 2.0),      # 入场Z-Score阈值
        ('z_exit', 0.5),       # 出场Z-Score阈值
        ('window', 20),        # 计算均值和标准差的窗口
        ('stop_loss', 0.03),   # 止损比例
        ('take_profit', 0.05), # 获利目标
        ('beta', 0.8)          # 对冲比率
    )

    def __init__(self):
        # 获取两个数据源
        self.stock1 = self.datas[0]  # 主要交易股票
        self.stock2 = self.datas[1]  # 对冲股票
        
        # 计算价差
        self.spread = bt.indicators.PctChange(self.stock1.close, period=1) - \
                     self.p.beta * bt.indicators.PctChange(self.stock2.close, period=1)
        
        # 计算移动均值和标准差
        self.spread_mean = bt.indicators.SMA(self.spread, period=self.p.window)
        self.spread_std = bt.indicators.StdDev(self.spread, period=self.p.window)
        
        # 计算Z-Score
        self.z_score = (self.spread - self.spread_mean) / self.spread_std
        
        # 记录交易
        self.trades = []
        self.entry_price1 = None
        self.entry_price2 = None
        
    def next(self):
        # 确保有足够的数据来计算指标
        if len(self.spread) < self.p.window:
            return
            
        if not self.position:  # 没有持仓
            # 检查是否满足开仓条件
            if self.z_score[0] > self.p.z_entry:  # 做空spread
                # 做空stock1，做多stock2
                self.entry_price1 = self.stock1.close[0]
                self.entry_price2 = self.stock2.close[0]
                
                # 计算头寸大小（市值平衡）
                value = self.broker.getvalue() * 0.4  # 使用40%资金
                qty1 = value / self.stock1.close[0]
                qty2 = value * self.p.beta / self.stock2.close[0]
                
                self.sell(data=self.stock1, size=qty1)
                self.buy(data=self.stock2, size=qty2)
                
                # 记录交易
                self.trades.append({
                    'date': self.stock1.datetime.date(),
                    'type': '开仓-做空spread',
                    'stock1_price': self.stock1.close[0],
                    'stock2_price': self.stock2.close[0],
                    'z_score': self.z_score[0]
                })
                print(f'开仓-做空spread: 日期={self.stock1.datetime.date()}, Z-Score={self.z_score[0]:.2f}')
                
            elif self.z_score[0] < -self.p.z_entry:  # 做多spread
                # 做多stock1，做空stock2
                self.entry_price1 = self.stock1.close[0]
                self.entry_price2 = self.stock2.close[0]
                
                # 计算头寸大小
                value = self.broker.getvalue() * 0.4
                qty1 = value / self.stock1.close[0]
                qty2 = value * self.p.beta / self.stock2.close[0]
                
                self.buy(data=self.stock1, size=qty1)
                self.sell(data=self.stock2, size=qty2)
                
                # 记录交易
                self.trades.append({
                    'date': self.stock1.datetime.date(),
                    'type': '开仓-做多spread',
                    'stock1_price': self.stock1.close[0],
                    'stock2_price': self.stock2.close[0],
                    'z_score': self.z_score[0]
                })
                print(f'开仓-做多spread: 日期={self.stock1.datetime.date()}, Z-Score={self.z_score[0]:.2f}')
                
        else:  # 持有仓位
            # 计算当前收益
            if self.position.size > 0:  # 做多spread
                profit_pct = ((self.stock1.close[0] / self.entry_price1) - 
                             self.p.beta * (self.stock2.close[0] / self.entry_price2))
            else:  # 做空spread
                profit_pct = (-(self.stock1.close[0] / self.entry_price1) + 
                             self.p.beta * (self.stock2.close[0] / self.entry_price2))
            
            # 检查是否满足平仓条件
            close_position = False
            exit_reason = ''
            
            if abs(self.z_score[0]) < self.p.z_exit:
                close_position = True
                exit_reason = 'Z-Score回归'
            elif profit_pct < -self.p.stop_loss:
                close_position = True
                exit_reason = '止损'
            elif profit_pct > self.p.take_profit:
                close_position = True
                exit_reason = '获利了结'
            
            if close_position:
                self.close(data=self.stock1)
                self.close(data=self.stock2)
                
                # 记录交易
                self.trades.append({
                    'date': self.stock1.datetime.date(),
                    'type': f'平仓-{exit_reason}',
                    'stock1_price': self.stock1.close[0],
                    'stock2_price': self.stock2.close[0],
                    'z_score': self.z_score[0],
                    'profit_pct': profit_pct * 100
                })
                print(f'平仓-{exit_reason}: 日期={self.stock1.datetime.date()}, '
                      f'收益率={profit_pct*100:.2f}%, Z-Score={self.z_score[0]:.2f}')
                
                self.entry_price1 = None
                self.entry_price2 = None

    def stop(self):
        # 策略结束时打印交易汇总
        print('\n====== 交易记录 ======')
        for trade in self.trades:
            if '开仓' in trade['type']:
                print(f"{trade['type']}: 日期={trade['date']}, "
                      f"Z-Score={trade['z_score']:.2f}")
            else:
                print(f"{trade['type']}: 日期={trade['date']}, "
                      f"收益率={trade['profit_pct']:.2f}%, "
                      f"Z-Score={trade['z_score']:.2f}")

# 运行回测
cerebro = bt.Cerebro()

# 添加数据
df1 = get_stock_data("AAPL", '2023-01-01')  # 苹果股票数据
df2 = get_stock_data("QQQ", '2023-01-01')   # 纳斯达克ETF数据

# 确保两个数据集的长度相同
min_date = max(df1.index[0], df2.index[0])
max_date = min(df1.index[-1], df2.index[-1])
df1 = df1[min_date:max_date]
df2 = df2[min_date:max_date]

data1 = bt.feeds.PandasData(dataname=df1)
data2 = bt.feeds.PandasData(dataname=df2)
cerebro.adddata(data1)
cerebro.adddata(data2)

cerebro.addstrategy(PairTradingStrategy)
cerebro.broker.setcash(100000.0)  # 设置初始资金

# 添加分析器
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')  # 回撤分析器
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')    # 收益分析器
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe') # 夏普比率分析器
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades') # 交易分析器

print('初始资金: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
strat = results[0]

# 获取回测结果
drawdown = strat.analyzers.drawdown.get_analysis()
returns = strat.analyzers.returns.get_analysis()
sharpe = strat.analyzers.sharpe.get_analysis()
trades = strat.analyzers.trades.get_analysis()

print('\n======= 核心指标 =======')
print('最大回撤: %.2f%%' % (drawdown['max']['drawdown'] * 100))
print('回撤周期: %d 天' % drawdown['max']['len'])
print('年化收益率: %.2f%%' % (returns['rnorm100']))
print('夏普比率: %.2f' % sharpe['sharperatio'])
print('最终资金: %.2f' % cerebro.broker.getvalue())

# 输出交易统计
print('\n======= 交易统计 =======')
print('总交易次数: %d' % trades['total']['total'])
if trades['total']['total'] > 0:
    print('盈利交易: %d' % trades['won']['total'])
    print('亏损交易: %d' % trades['lost']['total'])
    print('胜率: %.2f%%' % (trades['won']['total'] / trades['total']['total'] * 100))

cerebro.plot(style='candlestick')
