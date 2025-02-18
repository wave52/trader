import backtrader as bt
import pandas as pd
from data.get3 import get_stock_data

class MACDDivergenceStrategy(bt.Strategy):
    params = (
        ('fastperiod', 12),    # MACD快线周期
        ('slowperiod', 26),    # MACD慢线周期
        ('signalperiod', 9),   # MACD信号线周期
        ('lookback', 20),      # 用于判断背离的回看周期
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
        
        # 用于判断高点和低点
        self.highest_price = bt.indicators.Highest(self.data.close, period=self.p.lookback)
        self.lowest_price = bt.indicators.Lowest(self.data.close, period=self.p.lookback)
        
    def is_price_making_higher_high(self):
        """判断价格是否创新高"""
        return self.data.close[0] > self.highest_price[-1]
        
    def is_price_making_lower_low(self):
        """判断价格是否创新低"""
        return self.data.close[0] < self.lowest_price[-1]
        
    def is_macd_making_lower_high(self):
        """判断MACD是否形成更低的高点"""
        return self.macd_bar[0] < max([self.macd_bar[-i] for i in range(1, self.p.lookback)])
        
    def is_macd_making_higher_low(self):
        """判断MACD是否形成更高的低点"""
        return self.macd_bar[0] > min([self.macd_bar[-i] for i in range(1, self.p.lookback)])

    def next(self):
        if not self.position:  # 没有持仓
            # 判断底背离：价格创新低但MACD没有创新低
            if self.is_price_making_lower_low() and self.is_macd_making_higher_low():
                self.buy()  # 买入信号
                print(f'底背离买入，价格：{self.data.close[0]:.2f}')
                
        else:  # 持有仓位
            # 判断顶背离：价格创新高但MACD没有创新高
            if self.is_price_making_higher_high() and self.is_macd_making_lower_high():
                self.close()  # 卖出信号
                print(f'顶背离卖出，价格：{self.data.close[0]:.2f}')

# 运行回测
cerebro = bt.Cerebro()
df = get_stock_data()  # 获取股票数据
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.addstrategy(MACDDivergenceStrategy)
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
print('最大回撤: %.2f%%' % (drawdown['max']['drawdown'] * 100))
print('最大回撤周期: %d' % drawdown['max']['len'])

# 输出收益相关指标
returns = strat.analyzers.returns.get_analysis()
print('年化收益率: %.2f%%' % (returns['rnorm100']))
print('最终资金: %.2f' % cerebro.broker.getvalue())

cerebro.plot(style='candlestick')