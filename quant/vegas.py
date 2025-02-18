import backtrader as bt
import pandas as pd
from data.get3 import get_stock_data

class VegasStrategy(bt.Strategy):
    """
    Vegas通道策略
    - EMA12作为快速信号线
    - EMA144和EMA169构成核心通道
    - EMA576作为大周期趋势过滤
    - ATR用于动态止损和仓位管理
    """
    params = (
        ('ema_fast', 12),      # 快速均线
        ('ema_mid1', 144),     # 中期均线1
        ('ema_mid2', 169),     # 中期均线2
        ('ema_slow', 576),     # 慢速均线
        ('atr_period', 14),    # ATR周期
        ('risk_pct', 0.02),    # 单次风险比例
        ('atr_multiplier', 2)  # ATR止损倍数
    )

    def __init__(self):
        # 计算各周期均线
        self.ema_fast = bt.indicators.EMA(period=self.p.ema_fast)
        self.ema_mid1 = bt.indicators.EMA(period=self.p.ema_mid1)
        self.ema_mid2 = bt.indicators.EMA(period=self.p.ema_mid2)
        self.ema_slow = bt.indicators.EMA(period=self.p.ema_slow)
        
        # 计算ATR
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        
        # 记录交易
        self.trades = []
        self.entry_price = None
        
    def next(self):
        if not self.position:  # 没有持仓
            # 判断大趋势（价格在慢速均线上方）
            trend_up = self.data.close[0] > self.ema_slow[0]
            
            # Vegas通道突破（快线突破中期通道）
            channel_break = (self.ema_fast[0] > self.ema_mid1[0] and 
                           self.ema_fast[0] > self.ema_mid2[0] and
                           self.ema_fast[-1] <= self.ema_mid1[-1])
            
            if trend_up and channel_break:
                # 计算动态仓位
                risk_amount = self.broker.getvalue() * self.p.risk_pct
                stop_price = self.data.low[0] - self.p.atr_multiplier * self.atr[0]
                size = risk_amount / (self.data.close[0] - stop_price)
                
                # 执行买入
                self.entry_price = self.data.close[0]
                self.buy(size=size)
                
                # 记录交易
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '买入',
                    'price': self.data.close[0],
                    'size': size,
                    'stop': stop_price
                })
                print(f'买入: 日期={self.data.datetime.date()}, 价格={self.data.close[0]:.2f}, 止损={stop_price:.2f}')
                
        else:  # 持有仓位
            # 更新止损价
            current_stop = self.entry_price - self.p.atr_multiplier * self.atr[0]
            
            # 判断是否触及止损或通道下轨
            stop_triggered = self.data.close[0] < current_stop
            channel_break_down = (self.ema_fast[0] < self.ema_mid1[0] and 
                                self.ema_fast[0] < self.ema_mid2[0])
            
            if stop_triggered or channel_break_down:
                self.close()  # 平仓
                
                # 记录交易
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '卖出',
                    'price': self.data.close[0]
                })
                print(f'卖出: 日期={self.data.datetime.date()}, 价格={self.data.close[0]:.2f}')
                self.entry_price = None

    def stop(self):
        # 策略结束时打印交易汇总
        print('\n====== 交易记录 ======')
        for trade in self.trades:
            if trade['type'] == '买入':
                print(f"买入: 日期={trade['date']}, 价格={trade['price']:.2f}, "
                      f"数量={trade['size']:.2f}, 止损={trade['stop']:.2f}")
            else:
                print(f"卖出: 日期={trade['date']}, 价格={trade['price']:.2f}")

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data()  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(VegasStrategy)
cerebro.broker.setcash(100000.0)  # 设置初始资金

# 添加分析器
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')  # 回撤分析器
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')    # 收益分析器
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe') # 夏普比率分析器

print('初始资金: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
strat = results[0]

# 获取回测结果
drawdown = strat.analyzers.drawdown.get_analysis()
returns = strat.analyzers.returns.get_analysis()
sharpe = strat.analyzers.sharpe.get_analysis()

print('\n======= 核心指标 =======')
print('最大回撤: %.2f%%' % (drawdown['max']['drawdown'] * 100))
print('回撤周期: %d 天' % drawdown['max']['len'])
print('年化收益率: %.2f%%' % (returns['rnorm100']))
print('夏普比率: %.2f' % sharpe['sharperatio'])
print('最终资金: %.2f' % cerebro.broker.getvalue())

cerebro.plot(style='candlestick')
