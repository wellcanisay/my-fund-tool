import streamlit as st
import pandas as pd
import os
import yfinance as yf

# 强制屏蔽所有代理干扰
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="全球基金估值看板", layout="wide")

# ==========================================
# 1. 核心持仓数据库 (四只基金全录入)
# ==========================================
if 'fund_configs' not in st.session_state:
    st.session_state.fund_configs = {
        "基金1：东方阿尔法科技智选": [
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
        ],
        "基金2：国内AI算力核心": [
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
        ],
        "基金3：美股算力巨头": [
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
        ],
        "基金4：全球半导体核心": [
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

# --- 跨国行情抓取函数 ---
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

# --- 表格红绿着色逻辑 ---
def color_red_green(val):
    if not isinstance(val, str): return ''
    if '+' in val: return 'color: #ff4b4b; font-weight: bold' # 亮红
    if '-' in val: return 'color: #00ad4c; font-weight: bold' # 亮绿
    return ''

# ==========================================
# 2. 侧边栏：管理中心
# ==========================================
with st.sidebar:
    st.header("📂 基金管理中心")
    
    fund_list = list(st.session_state.fund_configs.keys())
    if 'current_selected' not in st.session_state:
        st.session_state.current_selected = fund_list[0]
        
    current_selected = st.selectbox("选择要查看的基金", fund_list, index=fund_list.index(st.session_state.current_selected))
    st.session_state.current_selected = current_selected
    
    st.divider()
    st.subheader("✏️ 修改当前基金名")
    new_name = st.text_input("输入新名称并回车", value=current_selected)
    
    if new_name != current_selected and new_name.strip() != "":
        st.session_state.fund_configs[new_name] = st.session_state.fund_configs.pop(current_selected)
        st.session_state.current_selected = new_name
        st.rerun()

    st.divider()
    st.info("💡 颜色说明：红涨绿跌\n🌍 支持市场：中/美/韩/台")

# ==========================================
# 3. 主界面显示
# ==========================================
st.title(f"📊 {st.session_state.current_selected}")
st.markdown("---")

fund_data = st.session_state.fund_configs[st.session_state.current_selected]
df_raw = pd.DataFrame(fund_data)

if not df_raw.empty:
    res_rows = []
    total_est = 0.0
    total_w = 0.0
    
    with st.spinner(f'正在跨国抓取 {st.session_state.current_selected} 的最新行情...'):
        for _, row in df_raw.iterrows():
            t_code, t_name, t_w = str(row['代码']), row['名称'], row['占比']
            info = get_global_price(t_code)
            
            if info:
                contribution = info['pct'] * (t_w / 100)
                res_rows.append({
                    "代码": t_code,
                    "名称": t_name,
                    "现价": f"¥{info['price']:.2f}" if "." in t_code else f"${info['price']:.2f}",
                    "今日涨跌": f"{info['pct']:+.2f}%",
                    "持仓占比": f"{t_w:.2f}%",
                    "贡献": f"{contribution:+.3f}%"
                })
                total_w += t_w
                total_est += contribution
            else:
                res_rows.append({"代码": t_code, "名称": t_name, "现价": "休市/获取失败", "今日涨跌": "--", "持仓占比": f"{t_w:.2f}%", "贡献": "--"})

    display_df = pd.DataFrame(res_rows)

    # 应用红绿配色
    try:
        styled_df = display_df.style.map(color_red_green, subset=['今日涨跌', '贡献'])
    except:
        styled_df = display_df.style.applymap(color_red_green, subset=['今日涨跌', '贡献'])

    st.dataframe(styled_df, use_container_width=True, height=450)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    # 底部数值着色
    est_color = "red" if total_est > 0 else ("green" if total_est < 0 else "black")
    col1.markdown(f"#### 今日预估总波动: :{est_color}[{total_est:+.3f}%]")
    col2.markdown(f"#### 已录入持仓总权重: {total_w:.2f}%")
else:
    st.warning("暂无持仓数据。")
