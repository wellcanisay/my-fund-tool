import streamlit as st
import pandas as pd
import os
import yfinance as yf
import requests
import json
import datetime
import time

# 屏蔽代理干扰
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="全球基金终极对账版", layout="wide")

# ==========================================
# 1. 核心数据库
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

# --- 核心函数：全球行情 ---
def get_global_price(ticker_code):
    try:
        ticker = yf.Ticker(ticker_code)
        hist = ticker.history(period="2d")
        if len(hist) < 2: return None
        curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
        return {'price': curr, 'pct': (curr - prev) / prev * 100}
    except: return None

# --- 核心函数：新浪多源实锤抓取 ---
def fetch_official_actual(fund_code):
    headers = {'User-Agent': 'Mozilla/5.0'}
    # 源 1：新浪财经 (晚上更新最快，5.78% 这种正式数在这里)
    try:
        url = f"http://fund.sina.com.cn/api/openapi.php/FundService.getFundNetValue?symbol={fund_code}&_={int(time.time())}"
        r = requests.get(url, headers=headers, timeout=5)
        res = r.json()['result']['data']
        if res and 'lsu_jz' in res:
            return {"val": float(res['lsu_jz']), "date": res['fdate'], "source": "新浪财经"}
    except: pass

    # 源 2：东方财富 (作为备份)
    try:
        url = f"https://fundmobapi.eastmoney.com/FundMApi/FundNetList.ashx?FCODE={fund_code}&pageIndex=1&pageSize=1&_={int(time.time())}"
        r = requests.get(url, headers=headers, timeout=5)
        item = r.json()['Datas'][0]
        return {"val": float(item['JZZZL']), "date": item['FSRQ'], "source": "东财实际"}
    except: pass
    
    return None

# ==========================================
# 2. 界面显示
# ==========================================
with st.sidebar:
    st.header("📂 基金管理中心")
    id_map = {fid: cfg['name'] for fid, cfg in st.session_state.fund_data_store.items()}
    def sync_id(): st.session_state.active_id = st.session_state.selector_key
    st.selectbox("选择基金", options=list(id_map.keys()), format_func=lambda x: id_map[x], 
                 key="selector_key", index=list(id_map.keys()).index(st.session_state.active_id), on_change=sync_id)
    
    active_cfg = st.session_state.fund_data_store[st.session_state.active_id]
    st.divider()
    new_name = st.text_input("修改名称", value=active_cfg['name'])
    if new_name != active_cfg['name'] and new_name.strip() != "":
        st.session_state.fund_data_store[st.session_state.active_id]['name'] = new_name
        st.rerun()

st.title(f"📈 {active_cfg['name']}")

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
            total_est += contribution = contrib
        else: res_rows.append({"代码": code, "名称": name, "现价": "--", "今日涨跌": "--", "占比": f"{w:.2f}%", "贡献": "--"})

def style_row(row):
    c = 'color: #ff4b4b; font-weight: bold' if '+' in str(row['今日涨跌']) else ('color: #00ad4c; font-weight: bold' if '-' in str(row['今日涨跌']) else '')
    return [c if col in ['现价', '今日涨跌', '贡献'] else '' for col in row.index]

st.dataframe(pd.DataFrame(res_rows).style.apply(style_row, axis=1), use_container_width=True, height=420)

# --- 底部实锤看板 ---
st.markdown("---")
official = fetch_official_actual(active_cfg['code'])

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"#### 1. 你的加权预估")
    st.markdown(f"<h2 style='color:{'#ff4b4b' if total_est > 0 else '#00ad4c'};'>{total_est:+.3f}%</h2>", unsafe_allow_html=True)
    st.caption(f"基于 {total_w:.2f}% 前十大重仓")

with col2:
    st.markdown(f"#### 2. 官方最新实际")
    if official:
        c = "#ff4b4b" if official['val'] > 0 else "#00ad4c"
        st.markdown(f"<h2 style='color:{c};'>{official['val']:+.3f}%</h2>", unsafe_allow_html=True)
        st.caption(f"日期: {official['date']} ({official['source']})")
        act_val = official['val']
    else:
        st.markdown(f"<h2 style='color:grey;'>正在同步...</h2>", unsafe_allow_html=True)
        act_val = None

with col3:
    st.markdown(f"#### 3. 预估误差")
    if act_val is not None:
        err = total_est - act_val
        st.markdown(f"<h2 style='color:black;'>{err:+.3f}%</h2>", unsafe_allow_html=True)
        st.caption("预估 > 实际 为正")
    else: st.markdown(f"<h2 style='color:grey;'>--</h2>", unsafe_allow_html=True)
