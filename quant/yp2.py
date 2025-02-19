import backtrader as bt
import pandas as pd
from data.get2 import get_stock_data

class MA5Strategy(bt.Strategy):
    """
    5日均线策略
    - 当价格上涨超过5日均线1%时买入
    - 当价格低于5日均线时卖出
    """
    params = (
        ('ma_period', 5),     # 均线周期
        ('up_pct', 0.01),     # 上涨比例
    )

    def __init__(self):
        # 计算5日均线
        self.ma5 = bt.indicators.SMA(period=self.p.ma_period)
        
        # 记录交易
        self.trades = []
        self.entry_price = None

    def next(self):
        if not self.position:  # 没有持仓
            # 如果价格高出五日均线1%，则买入
            if self.data.close[0] > self.ma5[0] * (1 + self.p.up_pct):
                # 计算购买数量
                size = int(self.broker.getcash() / self.data.close[0])
                self.buy(size=size)
                
                # 记录买入信息
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '买入',
                    'price': self.data.close[0],
                    'ma5': self.ma5[0],
                    'size': size
                })
                print(f'买入: 日期={self.data.datetime.date()}, '
                      f'价格={self.data.close[0]:.2f}, '
                      f'MA5={self.ma5[0]:.2f}, '
                      f'数量={size}')
                
        else:  # 持有仓位
            # 如果价格低于五日均线，则卖出
            if self.data.close[0] < self.ma5[0]:
                self.close()  # 清仓
                
                # 记录卖出信息
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '卖出',
                    'price': self.data.close[0],
                    'ma5': self.ma5[0]
                })
                print(f'卖出: 日期={self.data.datetime.date()}, '
                      f'价格={self.data.close[0]:.2f}, '
                      f'MA5={self.ma5[0]:.2f}')

    def stop(self):
        # 策略结束时打印交易汇总
        print('\n====== 交易记录 ======')
        for trade in self.trades:
            if trade['type'] == '买入':
                print(f"买入: 日期={trade['date']}, 价格={trade['price']:.2f}, "
                      f"MA5={trade['ma5']:.2f}, 数量={trade['size']}")
            else:
                print(f"卖出: 日期={trade['date']}, 价格={trade['price']:.2f}, "
                      f"MA5={trade['ma5']:.2f}")

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data()  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(MA5Strategy)
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