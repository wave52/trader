# 安装

```python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装新包后记得更新依赖
pip freeze > requirements.txt
```

# 运行

## 数据获取

get1: A股指数
get2: A股股票
get3: 美股
get4: ETF
后期统一

```python
python quant/data/get4.py
```

## 策略运行和回测

策略运行时会调用get获取数据

```python
python quant/yp2.py
```

# 依赖库

- backtrader: 回测框架
- akshare: A股数据获取
- yfinance: 美股数据获取
- pandas: 数据处理
- numpy: 科学计算
- matplotlib: 数据可视化
