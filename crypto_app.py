import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Crypto Trak", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: radial-gradient(circle at top right, #0f172a, #020617) !important; font-family: 'Inter', sans-serif; }
    
    /* Modern Glass Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 20px;
    }
    
    .main-header { background: linear-gradient(90deg, #60a5fa, #2dd4bf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.8rem; margin-bottom: 0px; }
    .stButton>button { background: rgba(255,255,255,0.05) !important; color: #94a3b8 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px; font-size: 10px; height: 24px; padding: 0 10px; }
    .stButton>button:hover { border: 1px solid #60a5fa !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=30000, key="cryptotrak_v7")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=30)
def fetch_data():
    ids = ",".join(COIN_IDS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&include_market_cap=true"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    return requests.get(url, headers=headers).json()

@st.cache_data(ttl=3600)
def fetch_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=365"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    res = requests.get(url, headers=headers).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- 3. UI START ---
st.markdown("<h1 class='main-header'>Crypto Trak</h1>", unsafe_allow_html=True)
data = fetch_data()

if data and isinstance(data, list):
    # Sidebar Holdings
    st.sidebar.markdown("<h2 style='color: #60a5fa;'>💳 Portfolio</h2>", unsafe_allow_html=True)
    user_holdings = {cid: st.sidebar.number_input(f"{cid.upper()}", min_value=0.0, step=0.0001, format="%.4f", key=f"h_{cid}") for cid in COIN_IDS}

    st.divider()
    now_uk = datetime.now(UK_TZ)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                cid = coin['id']
                
                with cols[j]:
                    with st.container(border=True):
                        # --- TIMEFRAME SELECTOR ---
                        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
                        # Default is 1W (7D)
                        if f"tf_{cid}" not in st.session_state: st.session_state[f"tf_{cid}"] = 7
                        
                        if t_col1.button("1D", key=f"btn1_{cid}"): st.session_state[f"tf_{cid}"] = 1
                        if t_col2.button("1W", key=f"btn7_{cid}"): st.session_state[f"tf_{cid}"] = 7
                        if t_col3.button("1M", key=f"btn30_{cid}"): st.session_state[f"tf_{cid}"] = 30
                        if t_col4.button("1Y", key=f"btn365_{cid}"): st.session_state[f"tf_{cid}"] = 365
                        
                        days = st.session_state[f"tf_{cid}"]
                        
                        # --- CALCULATION LOGIC ---
                        df_hist = fetch_history(cid)
                        # Filter data to the selected range
                        cutoff = now_uk - timedelta(days=days)
                        mask = df_hist['Date'] >= cutoff.replace(tzinfo=None)
                        df_filtered = df_hist.loc[mask]
                        
                        # Calculate % Change for the specific period
                        if not df_filtered.empty:
                            start_p = df_filtered.iloc[0]['Price']
                            end_p = df_filtered.iloc[-1]['Price']
                            period_change = ((end_p - start_p) / start_p) * 100
                        else:
                            period_change = 0
                        
                        # --- HEADER ---
                        l_col, n_col = st.columns([0.15, 0.85], gap="small")
                        l_col.image(coin['image'], width=40)
                        n_col.markdown(f"**{coin['name']}**<br><span style='color:#64748b; font-size:10px;'>{days}D Period Performance</span>", unsafe_allow_html=True)
                        
                        color = "#2dd4bf" if period_change >= 0 else "#f43f5e"
                        st.markdown(f"## £{coin['current_price']:,.2f} <span style='color:{color}; font-size:16px;'>{period_change:+.2f}%</span>", unsafe_allow_html=True)
                        
                        # --- CHART ---
                        fig = px.line(df_filtered, x='Date', y='Price', template="plotly_dark", color_discrete_sequence=['#3b82f6'])
                        fig.update_xaxes(visible=False)
                        fig.update_yaxes(autorange=True, visible=False)
                        fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Holding Footer
                        amt = user_holdings.get(cid, 0)
                        if amt > 0:
                            st.markdown(f"<div style='background:rgba(59,130,246,0.1); padding:10px; border-radius:12px; border:1px solid rgba(59,130,246,0.2);'><span style='color:#94a3b8; font-size:12px;'>My Holdings</span><br><span style='color:white; font-weight:700;'>£{coin['current_price'] * amt:,.2f}</span></div>", unsafe_allow_html=True)
