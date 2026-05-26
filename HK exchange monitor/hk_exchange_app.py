import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta

# ====== 页面配置 ======
st.set_page_config(page_title="港元汇率看板", layout="centered")
st.title("🇭🇰 港元汇率看板")
st.caption("数据来源：ExchangeRate-API (实时) / Yahoo Finance (历史)")

# ====== 侧边栏 ======
st.sidebar.header("设置")
refresh_interval = st.sidebar.slider("自动刷新间隔（秒）", 10, 60, 30)

# ====== 缓存获取实时汇率（避免重复请求）=======
@st.cache_data(ttl=refresh_interval)
def get_live_rates():
    """从 ExchangeRate-API 获取以 HKD 为基的汇率"""
    url = "https://api.exchangerate-api.com/v4/latest/HKD"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["rates"]
    except Exception as e:
        st.error(f"获取实时汇率失败: {e}")
        return None

# ====== 缓存获取历史汇率（yfinance，一天缓存）=======
@st.cache_data(ttl=3600)
def get_historical_hkd_usd():
    """获取 HKD/USD 过去 7 天收盘价"""
    try:
        ticker = yf.Ticker("HKD=X")
        end = datetime.now()
        start = end - timedelta(days=7)
        hist = ticker.history(start=start, end=end)
        if hist.empty:
            return None
        return hist["Close"]
    except:
        return None

# ====== 主要展示区 ======
rates = get_live_rates()

if rates:
    # 选择主要货币
    major_currencies = ["USD", "CNY", "EUR", "GBP", "JPY", "AUD", "CAD", "SGD"]
    cols = st.columns(4)  # 一行四个指标

    # 获取 USD 作为锚点计算涨跌（用 HKD/USD 的隐含变动）
    # 注意：ExchangeRate-API 返回的是 1 HKD = X 其他货币
    # 对于 HKD/USD，显示的是 1 HKD = 0.128 USD，通常表示为 USD/HKD ≈ 7.8
    # 我们逆向显示为 USD/HKD（每美元兑港币），更常见
    usd_per_hkd = rates.get("USD", 0)
    if usd_per_hkd:
        usd_hkd = 1 / usd_per_hkd  # 转为 USD/HKD ≈ 7.8
        st.metric("美元/港币 (USD/HKD)", f"{usd_hkd:.4f}", delta=None)

    for i, currency in enumerate(major_currencies):
        rate = rates.get(currency)
        if rate:
            # 计算 delta（假设我们取上一个有效值为基准，这里简单用前一日收盘价，但实时接口不提供）
            # 为了演示，我们显示相对于开盘的变动（没有历史数据可用，用未知代替）
            with cols[i % 4]:
                st.metric(f"HKD/{currency}", f"{rate:.4f}", delta=None)
else:
    st.warning("无法获取实时数据，请检查网络或稍后重试。")

# ====== 历史趋势图 ======
st.subheader("📈 HKD/USD 近 7 日走势")
hist = get_historical_hkd_usd()
if hist is not None and len(hist) > 0:
    # Y 轴是 HKD/USD 价格（即每美元兑港币），需转换
    hist_usd_hkd = 1 / hist
    st.line_chart(hist_usd_hkd, use_container_width=True)
    # 可选：移动平均线
    st.caption("蓝色线：每日收盘价直接转换的美元/港币汇率")
else:
    st.info("暂未获取到历史数据（可能非交易时段或网络问题）")

# ====== 自动刷新 ======
st.empty()
if st.checkbox("自动刷新", value=True):
    st.write(f"每 {refresh_interval} 秒自动刷新…")
    # Streamlit 本身支持 auto-rerun 通过时间缓存，但为了明确，使用 st.empty() + 暂停？
    # 更优雅的方法是利用 st.cache_data 的 ttl 和 st.rerun
    # 这里使用简单的 time.sleep 机制
    import time
    time.sleep(4)  # 放慢闪烁
    # 强制重新运行（利用 st.empty 更新）
    st.rerun()  # 注意：st.rerun 自 Streamlit 1.27.0 可用
else:
    st.write("手动刷新（F5 或点击浏览器刷新）")

# ====== 底部信息 ======
st.divider()
st.caption("免责声明：数据仅供参考，不构成投资建议。汇率实时变动，请以官方报价为准。")