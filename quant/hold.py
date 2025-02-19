import backtrader as bt
import pandas as pd
from data.get2 import get_stock_data

class HoldStrategy(bt.Strategy):
    """
    简单的买入持有策略
    在回测开始时买入，并持有到结束
    """
    
    def __init__(self):
        # 记录交易
        self.trades = []
        
    def next(self):
        if not self.position:  # 如果没有持仓
            self.buy()  # 买入
            # 记录买入信息
            self.trades.append({
                'date': self.data.datetime.date(),
                'type': '买入',
                'price': self.data.close[0]
            })
            print(f'买入: 日期={self.data.datetime.date()}, 价格={self.data.close[0]:.2f}')

    def stop(self):
        # 策略结束时打印交易汇总
        print('\n====== 交易记录 ======')
        for trade in self.trades:
            print(f"日期: {trade['date']}, 类型: {trade['type']}, 价格: {trade['price']:.2f}")

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data()  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(HoldStrategy)
cerebro.broker.setcash(100000.0)  # 设置初始资金
cerebro.addsizer(bt.sizers.PercentSizer, percents=90)  # 仓位控制

# 添加分析器
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')  # 添加回撤分析器
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')    # 添加收益分析器
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
