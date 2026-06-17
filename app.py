import streamlit as st
import pandas as pd
import os
import yfinance as yf
import requests
import json
import datetime
import time

# 强制清除代理干扰
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="全球基金量化对账-实时高速版", layout="wide")

# ==========================================
# 1. 基金持仓数据库（不变）
# ==========================================
if 'fund_db' not in st.session_state:
    st.session_state.fund_db = {
        "F1": {"name": "基金1：东方阿尔法科技智选混合发起C (025500)", "code": "025500", "holdings": [
            {"代码": "001309.SZ", "名称": "德明利", "占比": 9.66},
            {"代码": "301308.SZ", "名称": "江波龙", "占比": 9.03},
            {"代码": "688525.SS", "名称": "佰维存储", "占比": 8.81},
            {"代码": "603986.SS", "名称": "兆易创新", "占比": 8.80},
            {"代码": "300475.SZ", "名称": "香农芯创", "占比": 8.76},
            {"代码": "300223.SZ", "名称": "北京君正", "占比": 7.97},
            {"代码": "688766.SS", "名称": "普冉股份", "占比": 7.61},
            {"代码": "688416.SS", "名称": "恒烁股份", "占比": 6.14},
            {"代码": "688627.SS", "名称": "精智达", "占比": 5.25},
            {"代码": "688008.SS", "名称": "澜起科技", "占比": 5.00},
        ]},
        "F2": {"name": "基金2：永赢半导体产业智选混合发起C (020413)", "code": "020413", "holdings": [
            {"代码": "0981.HK", "名称": "中芯国际", "占比": 9.40},
            {"代码": "002222.SZ", "名称": "福晶科技", "占比": 9.25},
            {"代码": "688502.SS", "名称": "茂莱光学", "占比": 8.39},
            {"代码": "002156.SZ", "名称": "通富微电", "占比": 8.27},
            {"代码": "600584.SS", "名称": "长电科技", "占比": 7.75},
            {"代码": "688521.SS", "名称": "芯原股份", "占比": 7.28},
            {"代码": "603986.SS", "名称": "兆易创新", "占比": 7.14},
            {"代码": "688372.SS", "名称": "伟测科技", "占比": 4.09},
            {"代码": "003043.SZ", "名称": "华亚智能", "占比": 3.34},
            {"代码": "688362.SS", "名称": "甬矽电子", "占比": 2.80},
        ]},
        "F3": {"name": "基金3：华夏全球科技先锋混合(QDII)C (001528)", "code": "001528", "holdings": [
            {"代码": "CIEN", "名称": "Ciena科技", "占比": 5.56},
            {"代码": "TSM", "名称": "台积电", "占比": 4.87},
            {"代码": "LITE", "名称": "Lumentum", "占比": 4.72},
            {"代码": "COHR", "名称": "Coherent", "占比": 4.59},
            {"代码": "VIAV", "名称": "Viavi Solutions", "占比": 4.52},
            {"代码": "GLW", "名称": "康宁", "占比": 4.15},
            {"代码": "SNDK", "名称": "闪迪", "占比": 2.66},
            {"代码": "MU", "名称": "美光科技", "占比": 2.30},
            {"代码": "AEIS", "名称": "先进能源工业", "占比": 1.63},
            {"代码": "TER", "名称": "泰瑞达", "占比": 1.62},
        ]},
        "F4": {"name": "基金4：建信新兴市场混合(QDII)C (018147)", "code": "018147", "holdings": [
            {"代码": "TSM", "名称": "台积电", "占比": 10.26},
            {"代码": "NVDA", "名称": "英伟达", "占比": 10.14},
            {"代码": "000660.KS", "名称": "SK海力士", "占比": 8.65},
            {"代码": "AVGO", "名称": "博通", "占比": 8.52},
            {"代码": "005930.KS", "名称": "三星电子", "占比": 6.76},
            {"代码": "SNDK", "名称": "闪迪", "占比": 4.91},
            {"代码": "GLW", "名称": "康宁", "占比": 4.29},
            {"代码": "WDC", "名称": "西部数据", "占比": 3.73},
            {"代码": "LITE", "名称": "Lumentum", "占比": 3.58},
            {"代码": "MPWR", "名称": "Monolithic", "占比": 3.49},
        ]},
        "F5": {"name": "基金5：永赢先进制造智选混合发起C (018125)", "code": "018125", "holdings": [
            {"代码": "603179.SS", "名称": "新泉股份", "占比": 9.37},
            {"代码": "301550.SZ", "名称": "斯菱智驱", "占比": 9.29},
            {"代码": "0179.HK", "名称": "德昌电机控股", "占比": 5.95},
            {"代码": "002048.SZ", "名称": "宁波华翔", "占比": 5.02},
            {"代码": "603667.SS", "名称": "五洲新春", "占比": 4.97},
            {"代码": "300953.SZ", "名称": "震裕科技", "占比": 4.44},
            {"代码": "603009.SS", "名称": "北特科技", "占比": 4.38},
            {"代码": "601689.SS", "名称": "拓普集团", "占比": 3.44},
            {"代码": "603119.SS", "名称": "浙江荣泰", "占比": 3.35},
            {"代码": "002050.SZ", "名称": "三花智控", "占比": 3.30},
        ]}
    }

if 'active_id' not in st.session_state:
    st.session_state.active_id = "F1"

# ==========================================
# 2. 高速实时获取引擎（防限流版）
# ==========================================
def fetch_single_price_light(ticker):
    """
    轻量级获取实时价格：仅调用 info，不下载历史数据。
    若 info 缺失则返回 None。
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if info and 'regularMarketPrice' in info and 'regularMarketPreviousClose' in info:
            curr = info['regularMarketPrice']
            prev = info['regularMarketPreviousClose']
            if curr and prev:
                return {'price': curr, 'pct': (curr - prev) / prev * 100}
    except:
        pass
    return None

def fetch_batch_prices(tickers_list):
    """
    主函数：批量下载2日数据，缺失或非今日数据的股票用 info 补强。
    """
    result_map = {}
    valid_tickers = [t for t in tickers_list if t and isinstance(t, str)]
    if not valid_tickers:
        return {}

    # ----- 第一步：批量下载（唯一的大请求） -----
    try:
        tickers_str = " ".join(valid_tickers)
        data = yf.download(tickers_str, period="2d", group_by='ticker', progress=False, timeout=8)
        
        if data is not None and not data.empty:
            for ticker in valid_tickers:
                try:
                    if len(valid_tickers) == 1:
                        df = data
                    else:
                        df = data[ticker]
                    if df is not None and not df.empty and 'Close' in df:
                        close = df['Close'].dropna()
                        if len(close) >= 2:
                            curr = close.iloc[-1]
                            prev = close.iloc[-2]
                            result_map[ticker] = {'price': curr, 'pct': (curr - prev) / prev * 100}
                            continue
                except:
                    pass
                result_map[ticker] = None
        else:
            for ticker in valid_tickers:
                result_map[ticker] = None
    except:
        for ticker in valid_tickers:
            result_map[ticker] = None

    # ----- 第二步：检查实时性，补强 info（仅当需要时） -----
    today = datetime.datetime.now().date()
    # 收集需要补强的股票
    need_refresh = []
    for ticker in valid_tickers:
        base = result_map.get(ticker)
        if base is None:
            need_refresh.append(ticker)
            continue
        # 若批量数据存在，检查其最新日期是否今天
        try:
            if len(valid_tickers) == 1:
                df = data
            else:
                df = data[ticker]
            if df is not None and not df.empty:
                last_date = df.index[-1].date()
                if last_date == today:
                    continue  # 已有今日数据，无需补强
        except:
            pass
        need_refresh.append(ticker)

    # 对需要补强的股票逐个获取 info，加入短延时避免触发限流
    for ticker in need_refresh:
        real = fetch_single_price_light(ticker)
        if real:
            result_map[ticker] = real
        # 若补强失败，保留原结果（可能 None 或旧数据）
        time.sleep(0.2)  # 缓冲

    return result_map

# --- 天天基金估值接口（不变） ---
def fetch_tiantian_nav(fund_code):
    try:
        url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt={int(time.time())}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if "{" in r.text:
            js = json.loads(r.text[r.text.find('{'):r.text.find('}')+1])
            return {"val": float(js['gszzl']), "time": js['gztime']}
    except: return None

# ==========================================
# 3. 侧边栏与主界面（布局不变）
# ==========================================
with st.sidebar:
    st.header("📂 基金管理中心")
    id_map = {fid: cfg['name'] for fid, cfg in st.session_state.fund_db.items()}
    def sync_fund(): st.session_state.active_id = st.session_state.selector
    
    st.selectbox("切换基金对账", options=list(id_map.keys()), format_func=lambda x: id_map[x],
                 key="selector", index=list(id_map.keys()).index(st.session_state.active_id), on_change=sync_fund)
    
    active_cfg = st.session_state.fund_db[st.session_state.active_id]

st.title(f"🚀 {active_cfg['name']}")

beijing_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
st.caption(f"🕒 数据同步时间 (**北京时间**): **{beijing_time.strftime('%Y-%m-%d %H:%M:%S')}**")

df_holdings = pd.DataFrame(active_cfg['holdings'])
res_rows, total_est, total_w = [], 0.0, 0.0

tickers_to_fetch = df_holdings['代码'].tolist()

with st.spinner('🚀 高速批量获取行情 + 智能实时补强...'):
    prices_database = fetch_batch_prices(tickers_to_fetch)
    
    for _, row in df_holdings.iterrows():
        code, name, w = row['代码'], row['名称'], row['占比']
        info = prices_database.get(code)
        
        if info:
            contrib = info['pct'] * (w / 100)
            sym = "¥"
            if ".HK" in code: sym = "HK$"
            elif ".KS" in code: sym = "₩"
            elif "." not in code or ".TW" in code: sym = "$"
            
            res_rows.append({
                "代码": code, "名称": name,
                "现价": f"{sym}{info['price']:.2f}",
                "今日涨跌": f"{info['pct']:+.2f}%", "占比": f"{w:.2f}%", "贡献": f"{contrib:+.3f}%"
            })
            total_est += contrib
            total_w += w
        else:
            res_rows.append({"代码": code, "名称": name, "现价": "--", "今日涨跌": "--", "占比": f"{w:.2f}%", "贡献": "--"})

def style_row(row):
    c = 'color: #ff4b4b; font-weight: bold' if '+' in str(row['今日涨跌']) else ('color: #00ad4c; font-weight: bold' if '-' in str(row['今日涨跌']) else '')
    return [c if col in ['今日涨跌', '贡献', '现价'] else '' for col in row.index]

st.dataframe(pd.DataFrame(res_rows).style.apply(style_row, axis=1), use_container_width=True, height=450)

# 底部对账面板
st.markdown("---")
actual_val_obj = fetch_tiantian_nav(active_cfg['code'])
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### 1. 你的加权预估")
    color = "#ff4b4b" if total_est > 0 else "#00ad4c"
    st.markdown(f"<h1 style='color:{color};'>{total_est:+.3f}%</h1>", unsafe_allow_html=True)
with col2:
    st.markdown("#### 2. 天天基金估值/实际")
    if actual_val_obj:
        color = "#ff4b4b" if actual_val_obj['val'] > 0 else "#00ad4c"
        st.markdown(f"<h1 style='color:{color};'>{actual_val_obj['val']:+.2f}%</h1>", unsafe_allow_html=True)
        st.caption(f"同步时间: {actual_val_obj['time']}")
        act_val = actual_val_obj['val']
    else:
        st.metric("官方成绩", "获取中...")
        act_val = None
with col3:
    st.markdown("#### 3. 预估误差")
    if act_val is not None:
        st.markdown(f"<h1>{total_est - act_val:+.3f}%</h1>", unsafe_allow_html=True)

st.info("💡 **优化说明**：一次批量下载所有股票，避免 API 高频请求；仅对未含今日数据的个股轻量级补强 info，且请求间加缓冲，完美规避限流。")
