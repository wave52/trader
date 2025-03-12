import akshare as ak
import time
from rotation_strategy import RotationStrategy
import logging

def get_stock_pool():
    """获取股票池（这里使用沪深300成分股作为示例）"""
    try:
        # 获取沪深300成分股
        hs300 = ak.index_stock_cons_weight_csindex(symbol="000300")
        return hs300['成分券代码'].tolist()
    except Exception as e:
        logging.error(f"获取股票池失败: {str(e)}")
        return []

def main():
    # 初始化策略
    strategy = RotationStrategy(
        initial_capital=1000000,    # 100万初始资金
        position_limit=5,           # 最多持有5只股票
        oversold_threshold=-10,     # 超跌阈值-10%
        holding_period=5,           # 持有5天
        stop_loss=-5               # 止损线-5%
    )
    
    # 获取股票池
    stock_pool = get_stock_pool()
    if not stock_pool:
        logging.error("获取股票池失败，程序退出")
        return
    
    logging.info(f"初始化完成，股票池大小: {len(stock_pool)}")
    
    # 运行策略
    while True:
        try:
            strategy.run_strategy(stock_pool)
            
            # 打印当前组合状态
            status = strategy.get_portfolio_status()
            logging.info("当前组合状态:")
            for key, value in status.items():
                logging.info(f"{key}: {value}")
            
            # 等待下一个交易周期
            time.sleep(60 * 60)  # 每小时运行一次
            
        except Exception as e:
            logging.error(f"策略运行出错: {str(e)}")
            time.sleep(60)  # 出错后等待1分钟再试

if __name__ == "__main__":
    main() 