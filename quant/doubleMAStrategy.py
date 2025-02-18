import backtrader as bt
import pandas as pd
from data.get2 import get_stock_data

class DoubleMAStrategy(bt.Strategy):
    params = (('fast', 5), ('slow', 20))

    def __init__(self):
        self.ma_fast = bt.indicators.SMA(period=self.p.fast)
        self.ma_slow = bt.indicators.SMA(period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:  # 金叉
                self.buy(size=100)
        elif self.crossover < 0:    # 死叉
            self.close()

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data()  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(DoubleMAStrategy)
cerebro.broker.setcash(100000.0)  # 设置初始资金
cerebro.addsizer(bt.sizers.PercentSizer, percents=90)  # 仓位控制

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

cerebro.plot(style='candlestick')