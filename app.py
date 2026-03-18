import streamlit as st
import pandas as pd
import os
import yfinance as yf

# 强制屏蔽代理干扰
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

DB_FILE = "my_fund_assets.csv"
st.set_page_config(page_title="加权估值工具", layout="centered")

# --- 1. 强力数据加载：自动处理列冲突 ---
def load_data():
    target_cols = ['股票代码', '股票名称', '持仓占比']
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype={'股票代码': str})
            # 检查关键列是否存在，如果缺列，直接重置
            if not all(col in df.columns for col in target_cols):
                return pd.DataFrame(columns=target_cols)
            return df
        except:
            return pd.DataFrame(columns=target_cols)
    return pd.DataFrame(columns=target_cols)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- 2. 雅虎财经行情 (云端专用) ---
def get_yahoo_price(code):
    # A股后缀：6开头.SS (上海)，其他.SZ (深圳)
    ticker_code = f"{code}.SS" if code.startswith('6') else f"{code}.SZ"
    try:
        ticker = yf.Ticker(ticker_code)
        # 获取两日历史以计算今日涨幅
        hist = ticker.history(period="2d")
        if len(hist) < 2: return None
        
        curr_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change_pct = (curr_price - prev_close) / prev_close * 100
        return {'price': curr_price, 'pct': change_pct}
    except:
        return None

# --- 3. 界面展示 ---
st.title("🎯 基金加权估值工具 (云端稳定版)")

df_storage = load_data()

# 侧边栏：录入
with st.sidebar:
    st.header("📥 录入持仓")
    with st.form("input_form", clear_on_submit=True):
        st.info("请输入6位代码 (如 001309)")
        code_in = st.text_input("股票代码")
        name_in = st.text_input("股票简称")
        weight_in = st.number_input("持仓占比 (%)", min_value=0.0, max_value=100.0, step=0.01)
        
        if st.form_submit_button("确认录入"):
            if len(code_in) == 6:
                if code_in in df_storage['股票代码'].values:
                    df_storage.loc[df_storage['股票代码'] == code_in, '持仓占比'] = weight_in
                else:
                    new_item = pd.DataFrame({'股票代码': [code_in], '股票名称': [name_in], '持仓占比': [weight_in]})
                    df_storage = pd.concat([df_storage, new_item], ignore_index=True)
                save_data(df_storage)
                st.rerun()
    
    st.divider()
    if st.button("🗑️ 清空所有数据"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# 主展示区
if not df_storage.empty:
    st.subheader("📋 实时加权计算明细")
    res_rows = []
    total_est = 0.0
    total_w = 0.0
    
    for _, row in df_storage.iterrows():
        # 这里增加了防御性检查
        code = str(row.get('股票代码', ''))
        name = row.get('股票名称', '--')
        w = row.get('持仓占比', 0.0)
        
        if not code: continue
        
        info = get_yahoo_price(code)
        if info:
            # 核心计算：贡献 = 涨跌 × 占比
            contribution = info['pct'] * (w / 100)
            res_rows.append({
                "代码": code, "名称": name,
                "当前价": f"¥{info['price']:.2f}",
                "今日涨跌": f"{info['pct']:+.2f}%",
                "占比": f"{w:.2f}%",
                "贡献": f"{contribution:+.3f}%"
            })
            total_w += w
            total_est += contribution
        else:
            res_rows.append({"代码": code, "名称": name, "当前价": "获取失败", "今日涨跌": "--", "占比": f"{w:.2f}%", "贡献": "--"})

    st.table(pd.DataFrame(res_rows))
    
    # 结果看板
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("今日基金估值波动", f"{total_est:+.3f}%")
    c2.metric("累计录入权重", f"{total_w:.2f}%")
else:
    st.info("💡 请在左侧输入股票代码（6位）和占比。")
