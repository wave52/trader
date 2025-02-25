import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from caichang_dama import CaichangDamaStrategy
from caichang_dama_backtest import CaichangDamaBacktest

def main():
    """
    菜场大妈策略主程序
    """
    print("=" * 50)
    print("菜场大妈策略 - 质好价低市值小")
    print("=" * 50)
    
    # 1. 选股
    print("\n1. 开始选股...")
    strategy = CaichangDamaStrategy()
    selected_stocks = strategy.select_stocks(top_n=10)
    strategy.print_results()
    
    # 2. 回测
    print("\n2. 开始回测...")
    backtest = CaichangDamaBacktest()
    
    # 使用较短的回测周期，从2022年开始
    start_date = '2022-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    results = backtest.backtest(
        start_date=start_date,
        end_date=end_date,
        top_n=10,
        initial_capital=1000000
    )
    
    if results:
        print("\n====== 回测结果 ======")
        print(f"回测区间: {start_date} 至 {end_date} ({results['years']:.2f}年)")
        print(f"总收益率: {results['total_return']*100:.2f}% (基准: {results['benchmark_return']*100:.2f}%)")
        print(f"年化收益率: {results['annual_return']*100:.2f}% (基准: {results['benchmark_annual_return']*100:.2f}%)")
        print(f"夏普比率: {results['sharpe_ratio']:.2f}")
        print(f"最大回撤: {results['max_drawdown']*100:.2f}%")
        print(f"胜率: {results['win_rate']*100:.2f}%")
        print(f"月均换手次数: {results['turnover']:.2f}")
        print("\n回测结果图表已保存为 caichang_dama_backtest.png 和 caichang_dama_backtest_log.png")
    
    print("\n" + "=" * 50)
    print("菜场大妈策略运行完成")
    print("=" * 50)

if __name__ == "__main__":
    main() 