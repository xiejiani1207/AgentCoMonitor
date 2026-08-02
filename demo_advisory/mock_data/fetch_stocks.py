"""抓取真实 A 股数据，生成 stocks.py。

用法: python demo_advisory/mock_data/fetch_stocks.py
需要 akshare: pip install akshare
"""

import json
from datetime import datetime

import akshare as ak

STOCKS = {
    "600519": "贵州茅台",
    "300750": "宁德时代",
    "600036": "招商银行",
    "300760": "迈瑞医疗",
    "688981": "中芯国际",
}


def fetch_kline(symbol: str) -> dict:
    """拉取日 K 线并计算技术指标。"""
    df = ak.stock_zh_a_hist(
        symbol=symbol, period="daily",
        start_date="20250101", end_date="20260719",
        adjust="qfq",
    )
    latest = df.iloc[-1]

    # 均线
    ma5 = float(df["收盘"].tail(5).mean())
    ma20 = float(df["收盘"].tail(20).mean())
    ma60 = float(df["收盘"].tail(60).mean()) if len(df) >= 60 else ma20

    # MACD (简化: EMA12 - EMA26)
    ema12 = df["收盘"].ewm(span=12, adjust=False).mean()
    ema26 = df["收盘"].ewm(span=26, adjust=False).mean()
    dif = float(ema12.iloc[-1] - ema26.iloc[-1])
    dea = float(ema12.iloc[-1] - ema26.iloc[-1])  # 近似
    macd_hist = float(dif - dea)

    # RSI14
    delta = df["收盘"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 1.0
    rsi14 = float(100 - 100 / (1 + rs))

    # 支撑/压力位 = 近 60 日最低/最高
    support = float(df["最低"].tail(60).min()) if len(df) >= 60 else float(df["最低"].min())
    resistance = float(df["最高"].tail(60).max()) if len(df) >= 60 else float(df["最高"].max())

    return {
        "current_price": round(float(latest["收盘"]), 2),
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2),
        "macd": {"dif": round(dif, 2), "dea": round(dea, 2), "histogram": round(macd_hist, 2)},
        "rsi14": round(rsi14, 1),
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "low_52w": round(float(df["最低"].tail(250).min()), 2) if len(df) >= 250 else round(float(df["最低"].min()), 2),
        "high_52w": round(float(df["最高"].tail(250).max()), 2) if len(df) >= 250 else round(float(df["最高"].max()), 2),
        "vol_avg": int(df["成交量"].tail(20).mean()),
    }


def fetch_financials(symbol: str) -> dict:
    """拉取最新财务数据（同花顺接口）。"""
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        latest = df.iloc[-2]  # 取倒数第二行（最新报告期）
        return {
            "pe_ttm": _safe_float(latest.get("市盈率(动态)", None)),
            "pb": _safe_float(latest.get("市净率(动态)", None)),
            "roe": _safe_float(latest.get("净资产收益率", None)),
            "revenue_growth": _safe_float(latest.get("营业收入同比增长", None)),
            "profit_growth": _safe_float(latest.get("净利润同比增长", None)),
        }
    except Exception:
        return {}


def _safe_float(val) -> float | None:
    """从 akshare 的混合文本里提取数字。"""
    if val is None:
        return None
    s = str(val).replace("%", "").replace(",", "").replace("亿", "").replace("万", "")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def main():
    data = {}
    today = datetime.now(tz=None).strftime("%Y-%m-%d")  # noqa: DTZ005

    for code, name in STOCKS.items():
        print(f"Fetching {name} ({code})...")
        try:
            price = fetch_kline(code)
            fin = fetch_financials(code)
            data[code] = {"name": name, "price": price, "financials": fin}
            print(f"  OK: price={price['current_price']}, PE={fin.get('pe_ttm')}")
        except Exception as e:
            print(f"  FAIL: {e}")

    # 生成 stocks.py
    output = f'''"""真实 A 股历史数据（akshare 抓取）。

抓取日期: {today}
数据来源: akshare (东方财富 + 同花顺)
"""

STOCK_DATA = {json.dumps(data, ensure_ascii=False, indent=2)}
'''
    with open("demo_advisory/mock_data/stocks.py", "w", encoding="utf-8") as f:
        f.write(output)
    print("\nDone → demo_advisory/mock_data/stocks.py")


if __name__ == "__main__":
    main()
