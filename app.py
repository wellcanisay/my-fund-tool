import streamlit as st
import pandas as pd
import os
import urllib.request
import urllib.parse
import re

# ==========================================
# 1. 环境强制净化：封杀所有代理变量，强迫 Python 走直连
# ==========================================
for env_key in ['http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ[env_key] = ''

DB_FILE = "my_fund_assets.csv"
st.set_page_config(page_title="加权估值工具", layout="centered")

# --- 数据持久化函数 ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame(columns=['股票名称', '持仓占比'])
    return pd.DataFrame(columns=['股票名称', '持仓占比'])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- 2. 核心抓取：极简双通道 (腾讯 + 新浪) ---
def get_live_info(name):
    """
    使用最基础的 HTTP 请求，模拟浏览器访问，穿透率最高
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*'
    }
    
    # 优先尝试腾讯渠道 (数据最全，包含北交所)
    try:
        search_api = f"https://smartbox.gtimg.cn/s3/?q={urllib.parse.quote(name)}&t=all"
        req = urllib.request.Request(search_api, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as r:
            code_raw = r.read().decode('utf-8').split('^')[1]
            code = ("sh" + code_raw) if code_raw.startswith('6') else ("sz" + code_raw)
            
        price_api = f"https://qt.gtimg.cn/q={code}"
        with urllib.request.urlopen(urllib.request.Request(price_api, headers=headers), timeout=3) as r:
            parts = r.read().decode('gbk').split('~')
            # 腾讯接口：第3位现价，第32位涨跌幅
            return {'price': float(parts[3]), 'pct': float(parts[32])}
    except:
        pass 

    # 备选尝试新浪渠道
    try:
        search_api = f"http://suggest3.sinajs.cn/suggest/type=key&key={urllib.parse.quote(name)}"
        with urllib.request.urlopen(urllib.request.Request(search_api, headers=headers), timeout=3) as r:
            code = re.findall(r'(\w{2}\d{6})', r.read().decode('gbk'))[0]
            
        price_api = f"https://hq.sinajs.cn/list={code}"
        req_sina = urllib.request.Request(price_api, headers={'Referer': 'https://finance.sina.com.cn', **headers})
        with urllib.request.urlopen(req_sina, timeout=3) as r:
            data = r.read().decode('gbk').split(',')
            curr, prev = float(data[3]), float(data[2])
            return {'price': curr, 'pct': (curr - prev) / prev * 100}
    except:
        return None

# --- 3. 界面逻辑 ---
st.title("🎯 基金加权估值助手")
st.markdown("##### 逻辑：Σ (个股涨跌 × 个股持仓占比)")

df_storage = load_data()

# 侧边栏：输入与管理
with st.sidebar:
    st.header("📥 录入持仓")
    with st.form("input_form", clear_on_submit=True):
        name_input = st.text_input("股票简称", placeholder="例如：德明利")
        weight_input = st.number_input("持仓占比 (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")
        if st.form_submit_button("确认录入"):
            if name_input:
                # 更新或新增
                if name_input in df_storage['股票名称'].values:
                    df_storage.loc[df_storage['股票名称'] == name_input, '持仓占比'] = weight_input
                else:
                    new_item = pd.DataFrame({'股票名称': [name_input], '持仓占比': [weight_input]})
                    df_storage = pd.concat([df_storage, new_item], ignore_index=True)
                save_data(df_storage)
                st.rerun()
    
    st.divider()
    if st.button("🗑️ 清空所有数据"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# 主展示区：表格与结果
if not df_storage.empty:
    st.subheader("📋 实时加权计算明细")
    res_rows = []
    total_weighted_sum = 0.0
    total_pos_weight = 0.0
    
    # 模拟加权计算过程
    with st.spinner('同步最新股价中...'):
        for _, row in df_storage.iterrows():
            s_name = row['股票名称']
            s_weight = row['持仓占比']
            live = get_live_info(s_name)
            
            if live:
                # 加权贡献 = 涨跌幅 * (占比 / 100)
                contribution = live['pct'] * (s_weight / 100)
                res_rows.append({
                    "股票名称": s_name,
                    "当前价": f"¥{live['price']:.2f}",
                    "今日涨跌": f"{live['pct']:+.2f}%",
                    "持仓占比": f"{s_weight:.2f}%",
                    "贡献净值": f"{contribution:+.3f}%"
                })
                total_pos_weight += s_weight
                total_weighted_sum += contribution
            else:
                res_rows.append({
                    "股票名称": s_name, "当前价": "网络超时", 
                    "今日涨跌": "--", "持仓占比": f"{s_weight:.2f}%", "贡献净值": "--"
                })

    # 展示表格
    st.table(pd.DataFrame(res_rows))
    
    # 结果看版
    st.divider()
    col1, col2 = st.columns(2)
    # 这个“估值波动”就是你截图里要求的加权总和
    col1.metric("今日基金估值波动", f"{total_weighted_sum:+.3f}%", help="所有个股贡献净值的加总")
    col2.metric("已录入持仓总权重", f"{total_pos_weight:.2f}%")
    
    st.info("💡 提示：贡献净值 = 今日涨跌 × 持仓占比。")
else:
    st.info("💡 尚未录入持仓。请在左侧侧边栏输入股票名和占比（如：德明利，8.79）。")
