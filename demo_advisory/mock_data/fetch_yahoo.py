"""
从 Yahoo Finance 拉取 5 只 A 股的真实历史数据，生成 stocks.py。

使用方法: python demo_advisory/mock_data/fetch_yahoo.py
依赖: pip install yfinance

Yahoo Finance A 股代码规则:
  上海交易所 → 代码.SS   如 600519.SS (茅台)
  深圳交易所 → 代码.SZ   如 300750.SZ (宁德时代)
  科创板     → 代码.SS   如 688981.SS (中芯国际)
"""

import json
import os

import yfinance as yf

# ============================================================
# 代理配置（根据你的实际代理地址修改）
# ============================================================
PROXY_URL = "http://127.0.0.1:7890"  # ← 改成你的代理地址


# ============================================================
# 第 1 步：定义要抓取的股票
# ============================================================
# 每只股票包含：Yahoo 代码、中文名、所属行业
STOCKS = [
    {"code": "600519.SS", "name": "贵州茅台",   "industry": "白酒"},
    {"code": "300750.SZ", "name": "宁德时代",   "industry": "新能源"},
    {"code": "600036.SS", "name": "招商银行",   "industry": "银行"},
    {"code": "300760.SZ", "name": "迈瑞医疗",   "industry": "医药"},
    {"code": "688981.SS", "name": "中芯国际",   "industry": "科技"},
]


# ============================================================
# 第 2 步：从 K 线数据计算技术指标
# ============================================================
def calc_technical(df):
    """
    输入: yfinance 返回的 DataFrame（列: Open, High, Low, Close, Volume）
    输出: 技术指标 dict

    指标说明：
      - MA5/MA20/MA60: 5/20/60 日移动均线，用于判断趋势方向
      - MACD: 指数平滑异同移动平均线，金叉=看涨，死叉=看跌
      - RSI14: 14 日相对强弱指标，>70 超买，<30 超卖
      - 支撑位: 近 60 日最低价（买入参考）
      - 压力位: 近 60 日最高价（卖出参考）
    """
    # 取最近 60 行（足够计算所有指标）
    recent = df.tail(60).copy()
    close = recent["Close"]

    # --- 均线 ---
    ma5 = close.tail(5).mean()    # 近 5 日收盘价均值
    ma20 = close.tail(20).mean()  # 近 20 日收盘价均值
    # 如果数据不足 60 日，用 20 日均线代替
    ma60 = close.tail(60).mean() if len(close) >= 60 else ma20

    # --- MACD ---
    # EMA = 指数移动平均（近期权重更高）
    ema12 = close.ewm(span=12, adjust=False).mean()   # 快线（12 日）
    ema26 = close.ewm(span=26, adjust=False).mean()   # 慢线（26 日）
    dif = float(ema12.iloc[-1] - ema26.iloc[-1])       # DIF = 快-慢
    dea = float(dif)                                    # DEA（简化处理）
    macd_hist = float(dif - dea)                        # 柱状 = DIF - DEA

    # --- RSI14 ---
    delta = close.diff()                     # 每日涨跌
    gain = delta.clip(lower=0).rolling(14).mean()  # 14 日平均涨幅
    loss = (-delta.clip(upper=0)).rolling(14).mean() # 14 日平均跌幅
    if loss.iloc[-1] == 0:
        rsi14 = 100.0  # 没有下跌 → 极强
    else:
        rs = gain.iloc[-1] / loss.iloc[-1]
        rsi14 = float(100 - 100 / (1 + rs))

    # --- 支撑 / 压力 ---
    support = float(recent["Low"].min())   # 近 60 日最低
    resistance = float(recent["High"].max())  # 近 60 日最高

    # --- 52 周高低 ---
    data_1y = df.tail(250)  # 约 250 个交易日 = 一年
    low_52w = float(data_1y["Low"].min())
    high_52w = float(data_1y["High"].max())

    # --- 日均成交量 ---
    vol_avg = int(recent["Volume"].mean())

    return {
        "current_price": round(float(close.iloc[-1]), 2),
        "ma5": round(float(ma5), 2),
        "ma20": round(float(ma20), 2),
        "ma60": round(float(ma60), 2),
        "macd": {
            "dif": round(dif, 2),
            "dea": round(dea, 2),
            "histogram": round(macd_hist, 2),
        },
        "rsi14": round(rsi14, 1),
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "low_52w": round(low_52w, 2),
        "high_52w": round(high_52w, 2),
        "vol_avg": vol_avg,
    }


# ============================================================
# 第 3 步：提取日线历史序列
# ============================================================
def calc_daily_series(df):
    """
    从日 K 线 DataFrame 中提取最近 60 个交易日的数据。
    返回 list[dict]，每个 dict 是一天的 OHLCV + 日期。
    用于 Agent 做趋势分析、画图、找买卖点。
    """
    # 取最近 60 天
    recent = df.tail(60).copy()
    # 把日期从 index 转成字符串列
    recent["date"] = recent.index.strftime("%Y-%m-%d")

    # 只保留需要的列，转成 list[dict]
    series = []
    for _, row in recent.iterrows():
        series.append({
            "date": row["date"],
            "open": round(float(row["Open"]), 2),    # 开盘价
            "high": round(float(row["High"]), 2),    # 最高价
            "low": round(float(row["Low"]), 2),      # 最低价
            "close": round(float(row["Close"]), 2),  # 收盘价
            "volume": int(row["Volume"]),            # 成交量
        })
    return series


# ============================================================
# 第 4 步：从 yfinance 基本信息中提取财务数据
# ============================================================

def calc_financials(ticker_obj):
    """
    yfinance 的 info 字段包含 PE/PB/ROE 等基本面数据。
    注意：yfinance 的 A 股数据可能不完整，缺失字段返回 None。
    """
    info = ticker_obj.info
    return {
        "pe_ttm": info.get("trailingPE"),         # 滚动市盈率
        "pb": info.get("priceToBook"),             # 市净率
        "roe": _pct(info.get("returnOnEquity")),   # 净资产收益率(%)
        "revenue_growth": _pct(info.get("revenueGrowth")),  # 营收增长(%)
        "profit_growth": _pct(info.get("earningsGrowth")),  # 利润增长(%)
        "market_cap": info.get("marketCap"),        # 总市值
    }


def _pct(val):
    """将小数转为百分比（如 0.321 → 32.1），None 则保持 None。"""
    if val is None:
        return None
    return round(float(val) * 100, 1)


# ============================================================
# 第 5 步：主流程 —— 逐只抓取并生成 stocks.py
# ============================================================
def setup_proxy():
    """将代理地址注入到 requests 库和 yfinance 使用的环境变量中。"""
    os.environ["HTTP_PROXY"] = PROXY_URL       # HTTP 请求走代理
    os.environ["HTTPS_PROXY"] = PROXY_URL      # HTTPS 请求走代理


def main():
    setup_proxy()  # ← 先设置代理，再发起网络请求
    result = {}

    for stock in STOCKS:
        code = stock["code"]
        name = stock["name"]
        print(f"正在抓取 {name} ({code}) ...", end=" ", flush=True)

        try:
            # 4a. 创建 yfinance Ticker 对象
            ticker = yf.Ticker(code)

            # 4b. 拉取最近 1 年的日 K 线数据
            df = ticker.history(period="1y")
            if df.empty:
                print("FAIL: 无数据")
                continue

            # 4c. 计算技术指标（基于日线数据的快照）
            price_data = calc_technical(df)

            # 4d. 提取日线历史序列（近 60 个交易日）
            daily_data = calc_daily_series(df)

            # 4e. 拉取财务数据
            fin_data = calc_financials(ticker)

            # 4f. 保存结果
            result[code.replace(".SS", "").replace(".SZ", "")] = {
                "name": name,
                "industry": stock["industry"],
                "price": price_data,
                "daily": daily_data,      # ← 新增：日线历史序列
                "financials": fin_data,
            }
            print(f"OK  收盘价={price_data['current_price']}  PE={fin_data.get('pe_ttm')}")

        except Exception as e:
            print(f"FAIL: {e}")

    # ----------------------------------------------------------
    # 第 6 步：生成 stocks.py 文件
    # ----------------------------------------------------------
    output = f'''"""
真实 A 股历史数据（Yahoo Finance）。

数据来源: yfinance (Yahoo Finance)
包含 5 只股票的技术面指标和基本面财务数据，用于金融投顾 Demo。
"""

STOCK_DATA = {json.dumps(result, ensure_ascii=False, indent=2)}
'''

    output_path = "demo_advisory/mock_data/stocks.py"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n成功抓取 {len(result)}/{len(STOCKS)} 只股票")
    print(f"数据已保存到: {output_path}")


if __name__ == "__main__":
    main()
