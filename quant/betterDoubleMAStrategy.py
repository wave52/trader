import backtrader as bt
import pandas as pd
from data.get3 import get_stock_data

class BetterDoubleMAStrategy(bt.Strategy):
    """
    改进型双均线策略
    - 使用EMA代替SMA提高灵敏度
    - 加入ATR动态止损
    - 基于波动率的仓位管理
    - 移动止损保护盈利
    """
    params = (
        ('fast_period', 10),    # 快速均线周期
        ('slow_period', 30),    # 慢速均线周期
        ('atr_period', 14),     # ATR周期
        ('risk_pct', 0.02),     # 单次风险比例
        ('atr_multiplier', 2),  # ATR止损倍数
        ('trailing_pct', 0.8)   # 移动止损比例
    )

    def __init__(self):
        # 计算指标
        self.ema_fast = bt.indicators.EMA(period=self.p.fast_period)
        self.ema_slow = bt.indicators.EMA(period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.ema_fast, self.ema_slow)
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        
        # 记录交易
        self.trades = []
        self.entry_price = None
        self.stop_price = None
        self.trailing_stop = None
        
    def next(self):
        if not self.position:  # 没有持仓
            if self.crossover > 0:  # 金叉
                # 计算动态仓位
                risk_amount = self.broker.getvalue() * self.p.risk_pct
                stop_price = self.data.close[0] - self.p.atr_multiplier * self.atr[0]
                size = risk_amount / (self.data.close[0] - stop_price)
                
                # 执行买入
                self.entry_price = self.data.close[0]
                self.stop_price = stop_price
                self.trailing_stop = stop_price  # 初始移动止损价
                self.buy(size=size)
                
                # 记录交易
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '买入',
                    'price': self.data.close[0],
                    'size': size,
                    'stop': stop_price
                })
                print(f'金叉买入: 日期={self.data.datetime.date()}, '
                      f'价格={self.data.close[0]:.2f}, 止损={stop_price:.2f}')
                
        else:  # 持有仓位
            # 更新移动止损
            potential_stop = self.data.close[0] - self.p.atr_multiplier * self.atr[0]
            if potential_stop > self.trailing_stop:
                self.trailing_stop = potential_stop
            
            # 判断是否触及止损或死叉
            stop_triggered = self.data.close[0] < self.trailing_stop
            death_cross = self.crossover < 0
            
            if stop_triggered or death_cross:
                self.close()  # 平仓
                
                # 记录交易
                exit_reason = "移动止损" if stop_triggered else "死叉"
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '卖出',
                    'price': self.data.close[0],
                    'reason': exit_reason
                })
                print(f'{exit_reason}卖出: 日期={self.data.datetime.date()}, '
                      f'价格={self.data.close[0]:.2f}')
                
                # 重置状态
                self.entry_price = None
                self.stop_price = None
                self.trailing_stop = None

    def stop(self):
        # 策略结束时打印交易汇总
        print('\n====== 交易记录 ======')
        for trade in self.trades:
            if trade['type'] == '买入':
                print(f"买入: 日期={trade['date']}, 价格={trade['price']:.2f}, "
                      f"数量={trade['size']:.2f}, 止损={trade['stop']:.2f}")
            else:
                print(f"卖出: 日期={trade['date']}, 价格={trade['price']:.2f}, "
                      f"原因={trade['reason']}")

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data("VOO", '2023-01-01')  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(BetterDoubleMAStrategy)
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
