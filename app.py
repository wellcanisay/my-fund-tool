import streamlit as st
import pandas as pd
import os
import yfinance as yf
import requests
import json

# 强制屏蔽代理
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="多基金对账工具-透明版", layout="wide")

# ==========================================
# 1. 核心数据库 (持仓未变)
# ==========================================
if 'fund_configs' not in st.session_state:
    st.session_state.fund_configs = {
        "基金1：东方阿尔法科技智选混合 (025500)": {
            "code": "025500",
            "holdings": [
                {"代码": "001309.SZ", "名称": "德明利", "占比": 8.79},
                {"代码": "688525.SS", "名称": "佰维存储", "占比": 9.14},
                {"代码": "603986.SS", "名称": "兆易创新", "占比": 9.06},
                {"代码": "300475.SZ", "名称": "香农芯创", "占比": 8.74},
                {"代码": "301308.SZ", "名称": "江波龙", "占比": 7.97},
                {"代码": "688766.SS", "名称": "普冉股份", "占比": 7.90},
                {"代码": "688123.SS", "名称": "聚辰股份", "占比": 7.65},
                {"代码": "300223.SZ", "名称": "北京君正", "占比": 6.19},
                {"代码": "688110.SS", "名称": "东芯股份", "占比": 5.80},
                {"代码": "688249.SS", "名称": "晶合集成", "占比": 5.56},
            ]
        },
        "基金2：东方阿尔法精选混合 (009644)": {
            "code": "009644",
            "holdings": [
                {"代码": "300308.SZ", "名称": "中际旭创", "占比": 9.39},
                {"代码": "002384.SZ", "名称": "东山精密", "占比": 9.23},
                {"代码": "300502.SZ", "名称": "新易盛", "占比": 9.11},
                {"代码": "300476.SZ", "名称": "胜宏科技", "占比": 7.82},
                {"代码": "600183.SS", "名称": "生益科技", "占比": 6.75},
                {"代码": "603228.SS", "名称": "景旺电子", "占比": 6.10},
                {"代码": "002837.SZ", "名称": "英维克", "占比": 6.08},
                {"代码": "300394.SZ", "名称": "天孚通信", "占比": 5.77},
                {"代码": "688313.SS", "名称": "仕佳光子", "占比": 5.38},
                {"代码": "688498.SS", "名称": "源杰科技", "占比": 4.77},
            ]
        },
        "基金3：华夏纳斯达克100指数QDII (024239)": {
            "code": "024239",
            "holdings": [
                {"代码": "AVGO", "名称": "博通", "占比": 7.25},
                {"代码": "NVDA", "名称": "英伟达", "占比": 7.12},
                {"代码": "GOOG", "名称": "谷歌-C", "占比": 6.98},
                {"代码": "TSM", "名称": "台积电(ADR)", "占比": 6.72},
                {"代码": "AAPL", "名称": "苹果", "占比": 2.00},
                {"代码": "LUMN", "名称": "Lumen", "占比": 1.98},
                {"代码": "COHR", "名称": "Coherent", "占比": 1.94},
                {"代码": "CIEN", "名称": "Ciena", "占比": 1.30},
                {"代码": "TTMI", "名称": "TTM科技", "占比": 1.29},
                {"代码": "PLTR", "名称": "Palantir", "占比": 1.23},
            ]
        },
        "基金4：建信新兴市场混合QDII (018147)": {
            "code": "018147",
            "holdings": [
                {"代码": "NVDA", "名称": "英伟达", "占比": 9.86},
                {"代码": "000660.KS", "名称": "SK海力士", "占比": 9.79},
                {"代码": "2330.TW", "名称": "台积电", "占比": 9.07},
                {"代码": "AVGO", "名称": "博通", "占比": 7.98},
                {"代码": "005930.KS", "名称": "三星电子", "占比": 5.44},
                {"代码": "GLW", "名称": "康宁", "占比": 4.45},
                {"代码": "MPWR", "名称": "Monolithic", "占比": 3.89},
                {"代码": "LUMN", "名称": "Lumen", "占比": 3.79},
                {"代码": "CRDO", "名称": "Credo", "占比": 2.38},
                {"代码": "2317.TW", "名称": "鸿海精密", "占比": 2.35},
            ]
        }
    }

# --- 抓取函数 ---
def get_global_price(ticker_code):
    try:
        ticker = yf.Ticker(ticker_code)
        hist = ticker.history(period="2d")
        if len(hist) < 2: return None
        curr_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change_pct = (curr_price - prev_close) / prev_close * 100
        return {'price': curr_price, 'pct': change_pct}
    except: return None

def get_tt_data(fund_code):
    """
    抓取天天基金数据，返回：涨跌幅, 更新时间, 数据日期
    """
    try:
        url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        content = r.text
        start, end = content.find('{'), content.find('}')
        data = json.loads(content[start:end+1])
        # gszzl: 估算涨跌, gztime: 估算时间, jzrq: 最后净值日期
        return {
            "val": float(data['gszzl']),
            "time": data['gztime'],
            "last_date": data['jzrq']
        }
    except: return None

# --- UI 样式 ---
def style_financial_table(row):
    color = ''
    if '+' in str(row['今日涨跌']): color = 'color: #ff4b4b; font-weight: bold'
    elif '-' in str(row['今日涨跌']): color = 'color: #00ad4c; font-weight: bold'
    return [color if col in ['现价', '今日涨跌', '贡献'] else '' for col in row.index]

# ==========================================
# 2. 界面展示
# ==========================================
with st.sidebar:
    st.header("📂 基金管理中心")
    fund_names = list(st.session_state.fund_configs.keys())
    if 'current_selected' not in st.session_state:
        st.session_state.current_selected = fund_names[0]
    selected_name = st.selectbox("选择基金", fund_names, index=fund_names.index(st.session_state.current_selected))
    st.session_state.current_selected = selected_name
    
st.title(f"🚀 {st.session_state.current_selected}")

current_cfg = st.session_state.fund_configs[st.session_state.current_selected]
df_holdings = pd.DataFrame(current_cfg['holdings'])

if not df_holdings.empty:
    res_rows = []
    total_est, total_w = 0.0, 0.0
    
    with st.spinner('正在同步行情...'):
        for _, row in df_holdings.iterrows():
            code, name, w = str(row['代码']), row['名称'], row['占比']
            info = get_global_price(code)
            if info:
                contribution = info['pct'] * (w / 100)
                res_rows.append({
                    "代码": code, "名称": name,
                    "现价": f"¥{info['price']:.2f}" if "." in code else f"${info['price']:.2f}",
                    "今日涨跌": f"{info['pct']:+.2f}%",
                    "占比": f"{w:.2f}%",
                    "贡献": f"{contribution:+.3f}%"
                })
                total_w += w
                total_est += contribution
            else:
                res_rows.append({"代码": code, "名称": name, "现价": "--", "今日涨跌": "--", "占比": f"{w:.2f}%", "贡献": "--"})

    # 持仓表
    display_df = pd.DataFrame(res_rows)
    styled_df = display_df.style.apply(style_financial_table, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=420)

    # --- 底部对账看板 (核心升级) ---
    st.markdown("---")
    tt_data = get_tt_data(current_cfg['code'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"#### 1. 你的加权预估")
        color = "#ff4b4b" if total_est > 0 else "#00ad4c"
        st.markdown(f"<h2 style='color:{color};'>{total_est:+.3f}%</h2>", unsafe_allow_html=True)
        st.caption(f"基于 {total_w:.2f}% 前十大重仓计算")

    with col2:
        if tt_data:
            # 判断是估算还是实际：看 time 的日期是否是今天
            import datetime
            is_today = str(datetime.date.today()) in tt_data['time']
            label = "🚩 天天基金·实时估算" if is_today else "✅ 官方正式净值"
            
            st.markdown(f"#### 2. {label}")
            color = "#ff4b4b" if tt_data['val'] > 0 else "#00ad4c"
            st.markdown(f"<h2 style='color:{color};'>{tt_data['val']:+.3f}%</h2>", unsafe_allow_html=True)
            st.caption(f"更新时间: {tt_data['time']}")
            actual_val = tt_data['val']
        else:
            st.markdown(f"#### 2. 官方实际/估算")
            st.markdown(f"<h2 style='color:grey;'>等待更新...</h2>", unsafe_allow_html=True)
            actual_val = None

    with col3:
        st.markdown(f"#### 3. 预估误差")
        if actual_val is not None:
            diff = total_est - actual_val
            st.markdown(f"<h2 style='color:black;'>{diff:+.3f}%</h2>", unsafe_allow_html=True)
            st.caption("预估 > 实际 为正")
        else:
            st.markdown(f"<h2 style='color:grey;'>--</h2>", unsafe_allow_html=True)

    # 解释说明
    if tt_data and is_today:
        st.warning(f"⚠️ 注意：当前官方数据为【收盘估算】，正式净值通常在 21:00-24:00 之间公布。当前显示的误差是你的前十大预估与天天全仓估算的偏差。")
