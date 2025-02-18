import backtrader as bt
import pandas as pd
import numpy as np
from data.get4 import get_stock_data

class MeanReversionStrategy(bt.Strategy):
    """
    均线回归策略
    - 使用Z-Score判断价格偏离程度
    - 动态调整开平仓阈值
    - ATR波动率自适应
    - 多重止损机制
    """
    params = (
        ('ma_period', 60),      # 均线周期
        ('entry_z', 2.0),       # 入场阈值
        ('exit_z', 0.5),        # 离场阈值
        ('atr_period', 14),     # ATR周期
        ('risk_pct', 0.02),     # 单次风险比例
        ('max_drawdown', 0.05), # 最大回撤限制
        ('vol_window', 20),     # 波动率计算窗口
        ('trend_ma', 200)       # 趋势过滤均线
    )

    def __init__(self):
        # 计算指标
        self.ma = bt.indicators.SMA(period=self.p.ma_period)
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        self.trend_ma = bt.indicators.SMA(period=self.p.trend_ma)
        
        # 计算Z-Score
        self.std = bt.indicators.StdDev(self.data.close, period=self.p.ma_period)
        self.zscore = (self.data.close - self.ma) / self.std
        
        # 记录交易和绩效
        self.trades = []
        self.entry_price = None
        self.stop_price = None
        self.max_value = self.broker.getvalue()
        self.drawdown = 0
        
    def get_dynamic_threshold(self):
        """动态调整Z-Score阈值"""
        vol = self.std[0] / self.ma[0]  # 相对波动率
        base_z = self.p.entry_z
        
        if vol > 0.03:  # 高波动率环境
            return base_z * 0.8
        elif vol < 0.01:  # 低波动率环境
            return base_z * 1.2
        return base_z
        
    def next(self):
        # 更新账户最大值和回撤
        current_value = self.broker.getvalue()
        self.max_value = max(self.max_value, current_value)
        self.drawdown = (self.max_value - current_value) / self.max_value
        
        # 检查是否触发风控
        if self.drawdown > self.p.max_drawdown:
            if self.position:
                self.close()
                print(f'触发风控平仓: 日期={self.data.datetime.date()}, 回撤={self.drawdown:.2%}')
            return
            
        # 获取动态阈值
        dyn_threshold = self.get_dynamic_threshold()
        
        if not self.position:  # 没有持仓
            # 计算动态仓位
            risk_amount = self.broker.getvalue() * self.p.risk_pct
            stop_range = self.atr[0] * 2
            size = risk_amount / stop_range
            
            # 开仓信号
            if self.zscore[0] < -dyn_threshold:  # 做多信号
                if self.data.close[0] > self.trend_ma[0]:  # 趋势过滤
                    self.entry_price = self.data.close[0]
                    self.stop_price = self.entry_price - stop_range
                    self.buy(size=size)
                    
                    # 记录交易
                    self.trades.append({
                        'date': self.data.datetime.date(),
                        'type': '做多',
                        'price': self.entry_price,
                        'size': size,
                        'stop': self.stop_price,
                        'zscore': self.zscore[0]
                    })
                    print(f'做多: 日期={self.data.datetime.date()}, '
                          f'价格={self.entry_price:.2f}, Z值={self.zscore[0]:.2f}')
                    
            elif self.zscore[0] > dyn_threshold:  # 做空信号
                if self.data.close[0] < self.trend_ma[0]:  # 趋势过滤
                    self.entry_price = self.data.close[0]
                    self.stop_price = self.entry_price + stop_range
                    self.sell(size=size)
                    
                    # 记录交易
                    self.trades.append({
                        'date': self.data.datetime.date(),
                        'type': '做空',
                        'price': self.entry_price,
                        'size': size,
                        'stop': self.stop_price,
                        'zscore': self.zscore[0]
                    })
                    print(f'做空: 日期={self.data.datetime.date()}, '
                          f'价格={self.entry_price:.2f}, Z值={self.zscore[0]:.2f}')
                    
        else:  # 持有仓位
            # 检查止损
            if self.position.size > 0:  # 多仓
                if self.data.close[0] < self.stop_price:
                    self.close()
                    print(f'多仓止损: 日期={self.data.datetime.date()}, '
                          f'价格={self.data.close[0]:.2f}')
                    return
                    
            else:  # 空仓
                if self.data.close[0] > self.stop_price:
                    self.close()
                    print(f'空仓止损: 日期={self.data.datetime.date()}, '
                          f'价格={self.data.close[0]:.2f}')
                    return
                    
            # 检查是否满足平仓条件
            if abs(self.zscore[0]) < self.p.exit_z:
                self.close()
                profit = (self.data.close[0] - self.entry_price) * self.position.size
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '平仓',
                    'price': self.data.close[0],
                    'profit': profit,
                    'zscore': self.zscore[0]
                })
                print(f'平仓: 日期={self.data.datetime.date()}, '
                      f'价格={self.data.close[0]:.2f}, 收益={profit:.2f}')
                
                self.entry_price = None
                self.stop_price = None

    def stop(self):
        # 策略结束时打印交易汇总
        print('\n====== 交易记录 ======')
        total_trades = len([t for t in self.trades if t['type'] in ['做多', '做空']])
        winning_trades = len([t for t in self.trades if t.get('profit', 0) > 0])
        
        print(f'总交易次数: {total_trades}')
        if total_trades > 0:
            win_rate = winning_trades / total_trades * 100
            print(f'胜率: {win_rate:.2f}%')
        
        for trade in self.trades:
            if trade['type'] in ['做多', '做空']:
                print(f"{trade['type']}: 日期={trade['date']}, "
                      f"价格={trade['price']:.2f}, Z值={trade['zscore']:.2f}")
            else:
                print(f"平仓: 日期={trade['date']}, "
                      f"价格={trade['price']:.2f}, 收益={trade.get('profit', 0):.2f}")

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data()  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(MeanReversionStrategy)
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
