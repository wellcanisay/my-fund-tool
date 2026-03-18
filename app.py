import streamlit as st
import pandas as pd
import os
import yfinance as yf

# 强制不使用代理（云端环境自带纯净网络）
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

DB_FILE = "my_fund_assets.csv"
st.set_page_config(page_title="云端加权估值工具", layout="centered")

# --- 数据持久化 ---
def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE, dtype={'股票代码': str})
        except: return pd.DataFrame(columns=['股票代码', '股票名称', '持仓占比'])
    return pd.DataFrame(columns=['股票代码', '股票名称', '持仓占比'])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- 核心抓取：雅虎财经 (适合海外服务器) ---
def get_yahoo_price(code):
    """
    输入纯代码(如 001309)，自动转换为雅虎格式并抓取价格
    """
    # A股后缀转换：6开头是.SS (上海)，其他是.SZ (深圳)
    ticker_code = f"{code}.SS" if code.startswith('6') else f"{code}.SZ"
    
    try:
        ticker = yf.Ticker(ticker_code)
        # 获取最新价格和昨收价计算涨幅
        data = ticker.fast_info
        curr_price = data.last_price
        # 计算涨跌幅 (yfinance 的 year_high 等字段较稳，我们取最近价格)
        history = ticker.history(period="2d")
        if len(history) < 2: return None
        
        prev_close = history['Close'].iloc[-2]
        change_pct = (curr_price - prev_close) / prev_close * 100
        
        return {'price': curr_price, 'pct': change_pct}
    except:
        return None

# --- 界面展示 ---
st.title("🎯 基金加权估值助手 (云端增强版)")
st.caption("逻辑：Σ (个股涨跌幅 × 持仓占比)")

df_storage = load_data()

# 侧边栏：录入
with st.sidebar:
    st.header("📥 录入持仓")
    with st.form("input_form", clear_on_submit=True):
        st.info("请输入6位股票代码 (如 001309)")
        code_in = st.text_input("股票代码")
        name_in = st.text_input("股票简称 (仅作显示用)")
        weight_in = st.number_input("持仓占比 (%)", min_value=0.0, max_value=100.0, step=0.01)
        
        if st.form_submit_button("确认录入"):
            if code_in and len(code_in) == 6:
                # 更新或添加
                if code_in in df_storage['股票代码'].values:
                    df_storage.loc[df_storage['股票代码'] == code_in, '持仓占比'] = weight_in
                else:
                    new_item = pd.DataFrame({'股票代码': [code_in], '股票名称': [name_in], '持仓占比': [weight_in]})
                    df_storage = pd.concat([df_storage, new_item], ignore_index=True)
                save_data(df_storage)
                st.rerun()
            else:
                st.error("请输入正确的6位股票代码")

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
        code = row['股票代码']
        name = row['股票名称']
        w = row['持仓占比']
        
        # 调用雅虎接口
        info = get_yahoo_price(code)
        
        if info:
            contribution = info['pct'] * (w / 100)
            res_rows.append({
                "代码": code, "名称": name,
                "当前价": f"¥{info['price']:.2f}",
                "今日涨跌": f"{info['pct']:+.2f}%",
                "占比": f"{w:.2f}%",
                "贡献净值": f"{contribution:+.3f}%"
            })
            total_w += w
            total_est += contribution
        else:
            res_rows.append({"代码": code, "名称": name, "当前价": "获取失败", "今日涨跌": "--", "占比": f"{w:.2f}%", "贡献净值": "--"})

    st.table(pd.DataFrame(res_rows))
    
    st.divider()
    c1, c2 = st.columns(2)
    # 结果看板：加权求和
    c1.metric("今日基金估值波动", f"{total_est:+.3f}%")
    c2.metric("已录入总权重", f"{total_w:.2f}%")
else:
    st.info("💡 请在左侧输入股票代码（6位）和占比。数据将实时通过雅虎财经同步。")
