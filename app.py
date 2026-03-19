import streamlit as st
import pandas as pd
import os
import yfinance as yf
import requests
import json
import datetime
import time

# 强制屏蔽代理干扰，确保云端网络环境直通数据源
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="全球基金量化对账-北京时间版", layout="wide")

# ==========================================
# 1. 核心持仓数据库 (F1-F5 完整校准版)
# ==========================================
if 'fund_db' not in st.session_state:
    st.session_state.fund_db = {
        "F1": {"name": "基金1：东方阿尔法科技智选 (025500)", "code": "025500", "holdings": [
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
            {"代码": "LITE", "名称": "Lumentum", "占比": 1.98}, # 校准: LITE
            {"代码": "COHR", "名称": "Coherent", "占比": 1.94},
            {"代码": "CIEN", "名称": "Ciena", "占比": 1.30},
            {"代码": "TTMI", "名称": "TTM科技", "占比": 1.29},
            {"代码": "PLTR", "名称": "Palantir", "占比": 1.23},
        ]},
        "F4": {"name": "基金4：建信新兴市场混合QDII (018147)", "code": "018147", "holdings": [
            {"代码": "NVDA", "名称": "英伟达", "占比": 9.86},
            {"代码": "000660.KS", "名称": "SK海力士", "占比": 9.79},
            {"代码": "TSM", "名称": "台积电(ADR)", "占比": 9.07}, # 校准: TSM 美股
            {"代码": "AVGO", "名称": "博通", "占比": 7.98},
            {"代码": "005930.KS", "名称": "三星电子", "占比": 5.44},
            {"代码": "GLW", "名称": "康宁", "占比": 4.45},
            {"代码": "MPWR", "名称": "Monolithic", "占比": 3.89},
            {"代码": "LITE", "名称": "Lumentum", "占比": 3.79}, # 校准: LITE
            {"代码": "CRDO", "名称": "Credo", "占比": 2.38},
            {"代码": "2317.TW", "名称": "鸿海精密", "占比": 2.35},
        ]},
        "F5": {"name": "基金5：永赢先进制造智选混合发起C (018125)", "code": "018125", "holdings": [
            {"代码": "603179.SZ", "名称": "新泉股份", "占比": 9.21},
            {"代码": "603119.SS", "名称": "浙江荣泰", "占比": 7.91},
            {"代码": "301550.SZ", "名称": "斯菱股份", "占比": 7.39},
            {"代码": "603767.SS", "名称": "德昌电机控股", "占比": 6.21},
            {"代码": "603667.SS", "名称": "五洲新春", "占比": 5.36},
            {"代码": "002050.SZ", "名称": "三花智控", "占比": 5.13},
            {"代码": "300307.SZ", "名称": "拓普集团", "占比": 5.08},
            {"代码": "301120.SZ", "名称": "伟创电气", "占比": 4.63},
            {"代码": "603033.SS", "名称": "北特科技", "占比": 4.04},
            {"代码": "002048.SZ", "名称": "宁波华翔", "占比": 3.99},
        ]}
    }

if 'active_id' not in st.session_state:
    st.session_state.active_id = "F1"

# --- 核心函数：全球行情 ---
def get_global_price(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="2d")
        if len(hist) < 2: return None
        curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
        return {'price': curr, 'pct': (curr - prev) / prev * 100}
    except: return None

# --- 核心函数：天天基金数据 ---
def fetch_tiantian_nav(fund_code):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt={int(time.time())}"
        r = requests.get(url, headers=headers, timeout=5)
        if "{" in r.text:
            js = json.loads(r.text[r.text.find('{'):r.text.find('}')+1])
            return {"val": float(js['gszzl']), "time": js['gztime']}
    except: return None

# ==========================================
# 2. 交互逻辑
# ==========================================
with st.sidebar:
    st.header("📂 基金管理中心")
    id_map = {fid: cfg['name'] for fid, cfg in st.session_state.fund_db.items()}
    def sync_id(): st.session_state.active_id = st.session_state.selector
    
    st.selectbox("切换基金对账", options=list(id_map.keys()), format_func=lambda x: id_map[x],
                 key="selector", index=list(id_map.keys()).index(st.session_state.active_id), on_change=sync_id)
    
    active_cfg = st.session_state.fund_db[st.session_state.active_id]
    st.divider()
    new_name = st.text_input("修改名称并回车", value=active_cfg['name'])
    if new_name != active_cfg['name'] and new_name.strip() != "":
        st.session_state.fund_db[st.session_state.active_id]['name'] = new_name
        st.rerun()

# ==========================================
# 3. 主界面显示 (北京时间校准)
# ==========================================
st.title(f"🚀 {active_cfg['name']}")

# --- 关键修改：北京时间显示 ---
# 获取 UTC 时间并手动加 8 小时
beijing_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
st.caption(f"🕒 最后数据刷新 (**北京时间**): **{beijing_time.strftime('%Y-%m-%d %H:%M:%S')}**")

df_holdings = pd.DataFrame(active_cfg['holdings'])
res_rows, total_est, total_w = [], 0.0, 0.0

with st.spinner('同步全球实时行情...'):
    for _, row in df_holdings.iterrows():
        info = get_global_price(row['代码'])
        if info:
            contrib = info['pct'] * (row['占比'] / 100)
            res_rows.append({
                "代码": row['代码'], "名称": row['名称'],
                "现价": f"¥{info['price']:.2f}" if "." in row['代码'] else f"${info['price']:.2f}",
                "今日涨跌": f"{info['pct']:+.2f}%", "占比": f"{row['占比']:.2f}%", "贡献": f"{contrib:+.3f}%"
            })
            total_est += contrib; total_w += row['占比']
        else:
            res_rows.append({"代码": row['代码'], "名称": row['名称'], "现价": "--", "今日涨跌": "--", "占比": f"{row['占比']:.2f}%", "贡献": "--"})

# 上色渲染
def style_row(row):
    c = 'color: #ff4b4b; font-weight: bold' if '+' in str(row['今日涨跌']) else ('color: #00ad4c; font-weight: bold' if '-' in str(row['今日涨跌']) else '')
    return [c if col in ['今日涨跌', '贡献', '现价'] else '' for col in row.index]

st.dataframe(pd.DataFrame(res_rows).style.apply(style_row, axis=1), use_container_width=True, height=420)

# --- 底部三位一体对账 ---
st.markdown("---")
actual = fetch_tiantian_nav(active_cfg['code'])

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### 1. 你的加权预估")
    color = "#ff4b4b" if total_est > 0 else "#00ad4c"
    st.markdown(f"<h1 style='color:{color};'>{total_est:+.3f}%</h1>", unsafe_allow_html=True)
    st.caption(f"基于前十大 {total_w:.2f}% 权重计算")

with c2:
    st.markdown("#### 2. 天天基金估值/实际")
    if actual:
        color = "#ff4b4b" if actual['val'] > 0 else "#00ad4c"
        st.markdown(f"<h1 style='color:{color};'>{actual['val']:+.3f}%</h1>", unsafe_allow_html=True)
        st.caption(f"更新时间: {actual['time']}")
        act_val = actual['val']
    else:
        st.metric("官方成绩", "获取中...")
        act_val = None

with c3:
    st.markdown("#### 3. 预估误差")
    if act_val is not None:
        err = total_est - act_val
        st.markdown(f"<h1 style='color:black;'>{err:+.3f}%</h1>", unsafe_allow_html=True)
        st.caption("误差 = 预估 - 实际")
    else: st.metric("误差", "--")

st.info("💡 提示：该工具已校准北京时间显示。持仓数据已修正 Lumentum (LITE) 与台积电美股代码 (TSM)。")
