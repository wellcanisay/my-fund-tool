import streamlit as st
import pandas as pd
import os
import yfinance as yf
import requests
import json
import datetime
import time

# 屏蔽代理
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="全球基金全能工具-最终对账版", layout="wide")

# ==========================================
# 1. 核心数据库 (稳定 ID 模式)
# ==========================================
if 'fund_data_store' not in st.session_state:
    st.session_state.fund_data_store = {
        "F1": {"name": "基金1：东方阿尔法科技智选混合 (025500)", "code": "025500", "holdings": [
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
        ]},
        "F2": {"name": "基金2：东方阿尔法精选混合 (009644)", "code": "009644", "holdings": [
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
        ]},
        "F3": {"name": "基金3：华夏纳斯达克100指数QDII (024239)", "code": "024239", "holdings": [
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
        ]},
        "F4": {"name": "基金4：建信新兴市场混合QDII (018147)", "code": "018147", "holdings": [
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
        ]}
    }

if 'active_id' not in st.session_state:
    st.session_state.active_id = "F1"

# --- 功能：个股行情 ---
def get_global_price(ticker_code):
    try:
        ticker = yf.Ticker(ticker_code)
        hist = ticker.history(period="2d")
        if len(hist) < 2: return None
        curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
        return {'price': curr, 'pct': (curr - prev) / prev * 100}
    except: return None

# --- 功能：三源动态对账 ---
def fetch_best_actual_data(fund_code):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. 保底源：天天基金估值 (15:00 的基础数据)
    base_data = None
    try:
        r = requests.get(f"https://fundgz.1234567.com.cn/js/{fund_code}.js", headers=headers, timeout=3)
        if "{" in r.text:
            js_data = json.loads(r.text[r.text.find('{'):r.text.find('}')+1])
            base_data = {"val": float(js_data['gszzl']), "time": js_data['gztime'], "src": "盘后估算"}
    except: pass

    # 2. 冲刺源：新浪财经 (晚上 8 点后的正式净值)
    try:
        # 新浪接口：返回最近一天的正式变动
        r = requests.get(f"http://hq.sinajs.cn/list=f_{fund_code}", headers=headers, timeout=3)
        if "," in r.text:
            parts = r.text.split(',')
            # 新浪格式较复杂，通常第1位是名称，第2位是净值，我们要算涨跌需配合历史，
            # 简化逻辑：如果新浪返回的时间是今天，且数据存在，我们尝试用它
            # 由于新浪接口解析成本高，我们这里改用东财移动API作为正式源
            pass
    except: pass

    # 3. 核心源：东财移动API (晚上 8 点后最稳)
    try:
        url = f"https://fundmobapi.eastmoney.com/FundMApi/FundNetList.ashx?FCODE={fund_code}&pageIndex=1&pageSize=1"
        r = requests.get(url, headers=headers, timeout=3)
        res = r.json()
        if res['Datas']:
            item = res['Datas'][0]
            # 如果东财出了正式净值增长率(JZZZL)，它就是“实锤”
            return {"val": float(item['JZZZL']), "time": item['FSRQ'], "src": "官方正式"}
    except: pass

    return base_data

# ==========================================
# 2. 界面展示
# ==========================================
with st.sidebar:
    st.header("📂 基金管理中心")
    id_map = {fid: cfg['name'] for fid, cfg in st.session_state.fund_data_store.items()}
    def sync(): st.session_state.active_id = st.session_state.selector_key
    st.selectbox("切换基金", options=list(id_map.keys()), format_func=lambda x: id_map[x], 
                 key="selector_key", index=list(id_map.keys()).index(st.session_state.active_id), on_change=sync)
    active_cfg = st.session_state.fund_data_store[st.session_state.active_id]
    st.divider()
    new_name = st.text_input("重命名", value=active_cfg['name'])
    if new_name != active_cfg['name'] and new_name.strip() != "":
        st.session_state.fund_data_store[st.session_state.active_id]['name'] = new_name
        st.rerun()

st.title(f"🚀 {active_cfg['name']}")

# --- 持仓表格 ---
df_h = pd.DataFrame(active_cfg['holdings'])
res_rows, total_est, total_w = [], 0.0, 0.0
with st.spinner('正在同步全球行情...'):
    for _, row in df_h.iterrows():
        code, name, w = str(row['代码']), row['名称'], row['占比']
        info = get_global_price(code)
        if info:
            contrib = info['pct'] * (w / 100)
            res_rows.append({"代码": code, "名称": name, "现价": f"¥{info['price']:.2f}" if "." in code else f"${info['price']:.2f}", 
                             "今日涨跌": f"{info['pct']:+.2f}%", "占比": f"{w:.2f}%", "贡献": f"{contrib:+.3f}%"})
            total_w += w
            total_est += contrib
        else:
            res_rows.append({"代码": code, "名称": name, "现价": "--", "今日涨跌": "--", "占比": f"{w:.2f}%", "贡献": "--"})

def style_row(row):
    c = 'color: #ff4b4b; font-weight: bold' if '+' in str(row['今日涨跌']) else ('color: #00ad4c; font-weight: bold' if '-' in str(row['今日涨跌']) else '')
    return [c if col in ['现价', '今日涨跌', '贡献'] else '' for col in row.index]

st.dataframe(pd.DataFrame(res_rows).style.apply(style_row, axis=1), use_container_width=True, height=420)

# --- 底部对账看板 ---
st.markdown("---")
official = fetch_best_actual_data(active_cfg['code'])

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"#### 1. 你的加权预估")
    st.markdown(f"<h2 style='color:{'#ff4b4b' if total_est > 0 else '#00ad4c'};'>{total_est:+.3f}%</h2>", unsafe_allow_html=True)
    st.caption(f"基于 {total_w:.2f}% 权重计算")

with col2:
    if official:
        label = f"✅ {official['src']}" if official['src'] == "官方正式" else f"🚩 {official['src']}"
        st.markdown(f"#### 2. {label}")
        color = "#ff4b4b" if official['val'] > 0 else "#00ad4c"
        st.markdown(f"<h2 style='color:{color};'>{official['val']:+.3f}%</h2>", unsafe_allow_html=True)
        st.caption(f"数据时间: {official['time']}")
        act_val = official['val']
    else:
        st.markdown(f"#### 2. 官方实际/估算")
        st.markdown(f"<h2 style='color:grey;'>搜寻中...</h2>", unsafe_allow_html=True)
        act_val = None

with col3:
    st.markdown(f"#### 3. 预估误差")
    if act_val is not None:
        err = total_est - act_val
        st.markdown(f"<h2 style='color:black;'>{err:+.3f}%</h2>", unsafe_allow_html=True)
        st.caption("预估 > 实际 为正")
    else: st.markdown(f"<h2 style='color:grey;'>--</h2>", unsafe_allow_html=True)

st.info("💡 逻辑说明：白天显示天天基金估算；晚上 8 点后，若官方公布了正式净值，系统会自动抓取并替换，实现精准对账。")
