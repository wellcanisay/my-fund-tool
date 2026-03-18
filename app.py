import streamlit as st
import pandas as pd
import os
import yfinance as yf

# 强制屏蔽所有代理干扰
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
    os.environ[key] = ''

st.set_page_config(page_title="多基金加权估值工具", layout="wide")

# ==========================================
# 1. 核心持仓数据 (保底配置)
# ==========================================
if 'fund_configs' not in st.session_state:
    st.session_state.fund_configs = {
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

# --- 行情抓取函数 ---
def get_yahoo_price(code):
    ticker_code = f"{code}.SS" if code.startswith('6') else f"{code}.SZ"
    try:
        ticker = yf.Ticker(ticker_code)
        hist = ticker.history(period="2d")
        if len(hist) < 2: return None
        curr_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change_pct = (curr_price - prev_close) / prev_close * 100
        return {'price': curr_price, 'pct': change_pct}
    except: return None

# --- 表格着色逻辑 ---
def color_red_green(val):
    """
    针对字符串格式的涨跌幅进行着色
    """
    if not isinstance(val, str): return ''
    if '+' in val: return 'color: red; font-weight: bold'
    if '-' in val: return 'color: green; font-weight: bold'
    return ''

# ==========================================
# 2. 侧边栏：管理与命名
# ==========================================
with st.sidebar:
    st.header("📂 基金管理中心")
    
    # 基金切换
    fund_list = list(st.session_state.fund_configs.keys())
    current_selected = st.selectbox("选择要查看的基金", fund_list)
    
    st.divider()
    
    # 修改名字的功能
    st.subheader("✏️ 修改当前基金名")
    new_name = st.text_input("输入新名称并回车", value=current_selected)
    
    if new_name != current_selected and new_name.strip() != "":
        # 更新字典里的键名
        st.session_state.fund_configs[new_name] = st.session_state.fund_configs.pop(current_selected)
        st.rerun()

    st.divider()
    st.info(f"📊 数据源：Yahoo Finance\n🎨 颜色说明：红涨绿跌")

# ==========================================
# 3. 主界面显示
# ==========================================
st.title(f"📈 {new_name}")
st.markdown("---")

fund_data = st.session_state.fund_configs[new_name]
df_raw = pd.DataFrame(fund_data)

if not df_raw.empty:
    res_rows = []
    total_est = 0.0
    total_w = 0.0
    
    with st.spinner('正在同步全球行情...'):
        for _, row in df_raw.iterrows():
            code, name, w = str(row['股票代码']), row['股票名称'], row['持仓占比']
            info = get_yahoo_price(code)
            
            if info:
                contribution = info['pct'] * (w / 100)
                res_rows.append({
                    "代码": code,
                    "名称": name,
                    "现价": f"¥{info['price']:.2f}",
                    "今日涨跌": f"{info['pct']:+.2f}%",
                    "持仓占比": f"{w:.2f}%",
                    "贡献": f"{contribution:+.3f}%"
                })
                total_w += w
                total_est += contribution
            else:
                res_rows.append({"代码": code, "名称": name, "现价": "获取失败", "今日涨跌": "--", "持仓占比": f"{w:.2f}%", "贡献": "--"})

    # 转换为 DataFrame 准备显示
    display_df = pd.DataFrame(res_rows)

    # 【核心需求1】应用红绿颜色样式
    # 使用 Pandas Styler：subset 指定列名
    styled_df = display_df.style.applymap(color_red_green, subset=['今日涨跌', '贡献'])

    # 显示表格（改用 dataframe 以支持样式）
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # 底部看板
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    # 计算整体波动的颜色
    est_color = "red" if total_est > 0 else "green"
    col1.markdown(f"#### 今日预估总波动: :{est_color}[{total_est:+.3f}%]")
    col2.markdown(f"#### 已录入持仓权重: {total_w:.2f}%")
    
else:
    st.warning("暂无持仓数据。")
