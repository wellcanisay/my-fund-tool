import streamlit as st
import pandas as pd
import os
import yfinance as yf

# 强制屏蔽所有代理干扰
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="多基金加权估值工具", layout="centered")

# ==========================================
# 【核心数据仓】在这里管理你的所有基金持仓
# ==========================================
DEFAULT_FUNDS = {
    "基金1：半导体精选": [
        {"股票代码": "001309", "股票名称": "德明利", "持仓占比": 8.79},
        {"股票代码": "688525", "股票名称": "佰维存储", "持仓占比": 9.14},
        {"股票代码": "603986", "股票名称": "兆易创新", "持仓占比": 9.06},
        {"股票代码": "300475", "股票名称": "香农芯创", "持仓占比": 8.74},
        {"股票代码": "301308", "股票名称": "江波龙", "持仓占比": 7.97},
        {"股票代码": "688766", "股票名称": "普冉股份", "持仓占比": 7.90},
        {"股票代码": "688123", "股票名称": "聚辰股份", "持仓占比": 7.65},
        {"股票代码": "300223", "股票名称": "北京君正", "持仓占比": 6.19},
        {"股票代码": "688110", "股票名称": "东芯股份", "持仓占比": 5.80},
        {"股票代码": "688249", "股票名称": "晶合集成", "持仓占比": 5.56},
    ],
    "基金2：AI算力/光模块": [
        {"股票代码": "300308", "股票名称": "中际旭创", "持仓占比": 9.39},
        {"股票代码": "002384", "股票名称": "东山精密", "持仓占比": 9.23},
        {"股票代码": "300502", "股票名称": "新易盛", "持仓占比": 9.11},
        {"股票代码": "300476", "股票名称": "胜宏科技", "持仓占比": 7.82},
        {"股票代码": "600183", "股票名称": "生益科技", "持仓占比": 6.75},
        {"股票代码": "603228", "股票名称": "景旺电子", "持仓占比": 6.10},
        {"股票代码": "002837", "股票名称": "英维克", "持仓占比": 6.08},
        {"股票代码": "300394", "股票名称": "天孚通信", "持仓占比": 5.77},
        {"股票代码": "688313", "股票名称": "仕佳光子", "持仓占比": 5.38},
        {"股票代码": "688498", "股票名称": "源杰科技", "持仓占比": 4.77},
    ]
}

# --- 行情抓取函数 (Yahoo Finance 版) ---
def get_yahoo_price(code):
    # 后缀转换逻辑
    ticker_code = f"{code}.SS" if code.startswith('6') else f"{code}.SZ"
    try:
        ticker = yf.Ticker(ticker_code)
        # 获取两日数据计算涨跌幅
        hist = ticker.history(period="2d")
        if len(hist) < 2: return None
        curr_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change_pct = (curr_price - prev_close) / prev_close * 100
        return {'price': curr_price, 'pct': change_pct}
    except: return None

# ==========================================
# 界面逻辑
# ==========================================

with st.sidebar:
    st.header("📂 基金选择")
    # 下拉切换基金
    selected_fund = st.selectbox("请选择要查看的基金", list(DEFAULT_FUNDS.keys()))
    
    st.divider()
    st.info(f"📍 当前查看：{selected_fund}\n🌐 数据源：雅虎财经")
    st.caption("注：数据已固化在代码中，刷新不会消失。")

# 主标题
st.title(f"🚀 {selected_fund}")
st.subheader("实时加权平均估值明细")

# 获取对应基金的持仓
fund_data = DEFAULT_FUNDS[selected_fund]
df_storage = pd.DataFrame(fund_data)

if not df_storage.empty:
    res_rows = []
    total_est = 0.0
    total_w = 0.0
    
    with st.spinner(f'正在为您计算 {selected_fund} 的最新加权波动...'):
        for _, row in df_storage.iterrows():
            code = str(row['股票代码'])
            name = row['股票名称']
            w = row['持仓占比']
            
            info = get_yahoo_price(code)
            if info:
                # 核心逻辑：单股贡献 = 今日涨跌 * (占比 / 100)
                contribution = info['pct'] * (w / 100)
                res_rows.append({
                    "代码": code,
                    "名称": name,
                    "现价": f"¥{info['price']:.2f}",
                    "今日涨跌": f"{info['pct']:+.2f}%",
                    "占比": f"{w:.2f}%",
                    "贡献净值": f"{contribution:+.3f}%"
                })
                total_w += w
                total_est += contribution
            else:
                res_rows.append({"代码": code, "名称": name, "现价": "获取失败", "今日涨跌": "--", "占比": f"{w:.2f}%", "贡献净值": "--"})

    # 展示表格
    st.table(pd.DataFrame(res_rows))
    
    # 底部汇总面板
    st.divider()
    col1, col2 = st.columns(2)
    # 这里的估值波动就是 Σ(涨跌*占比)
    col1.metric(f"今日预估净值涨跌", f"{total_est:+.3f}%")
    col2.metric("已录入持仓总权重", f"{total_w:.2f}%")
else:
    st.warning("暂无持仓数据。")
