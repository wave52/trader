import backtrader as bt
import pandas as pd
from data.get3 import get_stock_data

class MACDStrategy(bt.Strategy):
    params = (
        ('fastperiod', 12),    # MACD快线周期
        ('slowperiod', 26),    # MACD慢线周期
        ('signalperiod', 9),   # MACD信号线周期
    )

    def __init__(self):
        # 添加MACD指标
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fastperiod,
            period_me2=self.p.slowperiod,
            period_signal=self.p.signalperiod
        )
        # DIF线
        self.macd_dif = self.macd.macd
        # DEA线（信号线）
        self.macd_dea = self.macd.signal
        # MACD柱状图
        self.macd_bar = self.macd.macd - self.macd.signal
        
        # 记录交易
        self.trades = []

    def next(self):
        if not self.position:  # 没有持仓
            # MACD金叉（DIF上穿DEA）且MACD柱由负变正
            if self.macd_dif[0] > self.macd_dea[0] and \
               self.macd_dif[-1] <= self.macd_dea[-1] and \
               self.macd_bar[0] > 0:
                self.buy()  # 买入信号
                # 记录买入信息
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '买入',
                    'price': self.data.close[0],
                    'DIF': self.macd_dif[0],
                    'DEA': self.macd_dea[0],
                    'MACD': self.macd_bar[0]
                })
                print(f'买入: 日期={self.data.datetime.date()}, 价格={self.data.close[0]:.2f}')
                
        else:  # 持有仓位
            # MACD死叉（DIF下穿DEA）且MACD柱由正变负
            if self.macd_dif[0] < self.macd_dea[0] and \
               self.macd_dif[-1] >= self.macd_dea[-1] and \
               self.macd_bar[0] < 0:
                self.close()  # 卖出信号
                # 记录卖出信息
                self.trades.append({
                    'date': self.data.datetime.date(),
                    'type': '卖出',
                    'price': self.data.close[0],
                    'DIF': self.macd_dif[0],
                    'DEA': self.macd_dea[0],
                    'MACD': self.macd_bar[0]
                })
                print(f'卖出: 日期={self.data.datetime.date()}, 价格={self.data.close[0]:.2f}')

    def stop(self):
        # 策略结束时打印交易汇总
        print('\n====== 交易记录 ======')
        # for trade in self.trades:
        #     print(f"日期: {trade['date']}, 类型: {trade['type']}, 价格: {trade['price']:.2f}")
        #     print(f"DIF: {trade['DIF']:.4f}, DEA: {trade['DEA']:.4f}, MACD: {trade['MACD']:.4f}\n")

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data()  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(MACDStrategy)
cerebro.broker.setcash(100000.0)  # 设置初始资金
cerebro.addsizer(bt.sizers.PercentSizer, percents=90)  # 仓位控制

# 添加分析器
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')  # 添加回撤分析器
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')    # 添加收益分析器

print('初始资金: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
strat = results[0]

# 输出回撤相关指标
drawdown = strat.analyzers.drawdown.get_analysis()
print('\n====== 策略评估 ======')
print('最大回撤: %.2f%%' % (drawdown['max']['drawdown'] * 100))
print('最大回撤周期: %d' % drawdown['max']['len'])

# 输出收益相关指标
returns = strat.analyzers.returns.get_analysis()
print('年化收益率: %.2f%%' % (returns['rnorm100']))
print('最终资金: %.2f' % cerebro.broker.getvalue())

cerebro.plot(style='candlestick')