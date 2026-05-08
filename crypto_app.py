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
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 15px;
    }
    
    .main-header { background: linear-gradient(90deg, #60a5fa, #2dd4bf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.5rem; }
    
    .stButton>button { 
        background: rgba(255,255,255,0.05) !important; 
        color: #94a3b8 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 6px; 
        font-size: 10px !important; 
        height: 22px !important; 
        padding: 0 8px !important;
    }
    .stButton>button:hover { border: 1px solid #60a5fa !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=30000, key="cryptotrak_v10")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. DATA ENGINE (DYNAMIC RESOLUTION) ---
@st.cache_data(ttl=30)
def fetch_data():
    ids = ",".join(COIN_IDS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    return requests.get(url, headers=headers).json()

@st.cache_data(ttl=300) # 5 min cache for history
def fetch_dynamic_history(coin_id, days):
    # If days <= 2, CoinGecko automatically provides minute/hourly data for more detail
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days={days}"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    res = requests.get(url, headers=headers).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- 3. UI ---
st.markdown("<h1 class='main-header'>Crypto Trak</h1>", unsafe_allow_html=True)
data = fetch_data()

if data and isinstance(data, list):
    st.sidebar.markdown("<h2 style='color: #60a5fa;'>💳 Portfolio</h2>", unsafe_allow_html=True)
    user_holdings = {cid: st.sidebar.number_input(f"{cid.upper()}", min_value=0.0, step=0.0001, format="%.4f", key=f"h_{cid}") for cid in COIN_IDS}

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                cid = coin['id']
                
                with cols[j]:
                    with st.container(border=True):
                        # Row 1: Snug Header + Buttons
                        h_cols = st.columns([0.15, 0.12, 0.12, 0.12, 0.12, 0.37], gap="small")
                        h_cols[0].image(coin['image'], width=30)
                        
                        if f"tf_{cid}" not in st.session_state: st.session_state[f"tf_{cid}"] = 7
                        
                        if h_cols[1].button("1D", key=f"1d_{cid}"): st.session_state[f"tf_{cid}"] = 1
                        if h_cols[2].button("1W", key=f"1w_{cid}"): st.session_state[f"tf_{cid}"] = 7
                        if h_cols[3].button("1M", key=f"1m_{cid}"): st.session_state[f"tf_{cid}"] = 30
                        if h_cols[4].button("1Y", key=f"1y_{cid}"): st.session_state[f"tf_{cid}"] = 365
                        
                        days = st.session_state[f"tf_{cid}"]
                        
                        # Fetch Data based on Button Selection
                        df_filtered = fetch_dynamic_history(cid, days)
                        
                        # Calculate ROI for the period
                        start_p, end_p = df_filtered.iloc[0]['Price'], df_filtered.iloc[-1]['Price']
                        period_change = ((end_p - start_p) / start_p) * 100
                        
                        color = "#2dd4bf" if period_change >= 0 else "#f43f5e"
                        st.markdown(f"**{coin['name']}**")
                        st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:15px;'>{period_change:+.2f}%</span>", unsafe_allow_html=True)
                        
                        # --- THE ULTRA-DETAIL CHART ---
                        fig = px.line(df_filtered, x='Date', y='Price', template="plotly_dark")
                        
                        fig.update_traces(
                            line=dict(color='#3b82f6', width=2),
                            fill='tozeroy', 
                            fillcolor='rgba(59, 130, 246, 0.1)',
                            hoverinfo='text+name',
                            mode='lines'
                        )
                        
                        fig.update_xaxes(visible=False)
                        
                        # The Secret for "Deep Detail": autorange=True + dynamic margins
                        fig.update_yaxes(
                            showgrid=True, 
                            gridcolor='rgba(255,255,255,0.05)',
                            tickfont=dict(size=10, color='#64748b'),
                            side="right",
                            autorange=True,
                            fixedrange=False, # Allows you to zoom manually on mobile
                            title=None
                        )
                        
                        fig.update_layout(
                            height=250,
                            margin=dict(l=0,r=0,t=10,b=0),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        amt = user_holdings.get(cid, 0)
                        if amt > 0:
                            st.markdown(f"<p style='color: #94a3b8; font-size: 11px;'>My Stake: <b style='color:white;'>£{coin['current_price'] * amt:,.2f}</b></p>", unsafe_allow_html=True)
