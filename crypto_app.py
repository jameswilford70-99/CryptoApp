import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. PAGE CONFIG & ELITE STYLING ---
st.set_page_config(page_title="Crypto Trak", layout="wide", page_icon="📈")

# Advanced CSS: Glassmorphism + Animations + Sticky UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #080c14) !important;
        font-family: 'Inter', sans-serif;
    }

    /* Glassmorphism Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 24px;
        transition: transform 0.3s ease, border 0.3s ease;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-5px);
    }

    /* Update Pulse Animation */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(45, 212, 191, 0); }
        100% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0); }
    }
    .update-pulse {
        animation: pulse 2s infinite;
        border-radius: 50%;
        display: inline-block;
        width: 8px; height: 8px;
        background-color: #2dd4bf;
        margin-right: 8px;
    }

    /* Sticky Modern Header */
    .main-header {
        background: linear-gradient(90deg, #60a5fa, #2dd4bf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0px;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: #f8fafc !important;
    }
    </style>
    """, unsafe_allow_html=True)

# AUTO-REFRESH (30s)
st_autorefresh(interval=30000, key="cryptotrak_ultra")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 

COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. SIDEBAR ---
st.sidebar.markdown("<h2 style='color: #60a5fa;'>💳 Portfolio</h2>", unsafe_allow_html=True)
user_holdings = {cid: st.sidebar.number_input(f"{cid.upper()}", min_value=0.0, step=0.0001, format="%.4f", key=f"v4_{cid}") for cid in COIN_IDS}

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=30)
def fetch_prices_pro():
    ids = ",".join(COIN_IDS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except: return None

@st.cache_data(ttl=3600)
def fetch_history_pro(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=30&interval=daily"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15).json()
        df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        return df
    except: return pd.DataFrame()

# --- 4. UI START ---
st.markdown("<h1 class='main-header'>Crypto Trak</h1>", unsafe_allow_html=True)
now_uk = datetime.now(UK_TZ)
st.markdown(f"<div><span class='update-pulse'></span><span style='color:#94a3b8; font-size:14px;'>Live Intelligence • {now_uk.strftime('%H:%M:%S')} UK</span></div>", unsafe_allow_html=True)

data = fetch_prices_pro()

if data and isinstance(data, list):
    total_val = sum(c['current_price'] * user_holdings.get(c['id'], 0) for c in data)
    st.metric("Aggregate Balance", f"£{total_val:,.2f}")
    st.divider()

    start_date_7d = now_uk - timedelta(days=7)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # Coin Logo + Name Row
                        col_logo, col_name = st.columns([1, 5])
                        with col_logo:
                            st.image(coin['image'], width=40)
                        with col_name:
                            api_utc = datetime.strptime(coin['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                            uk_time = api_utc.astimezone(UK_TZ).strftime("%H:%M")
                            st.markdown(f"<p style='margin-bottom:0; font-weight:700;'>{coin['name']}</p><p style='color:#64748b; font-size:10px;'>Synced {uk_time}</p>", unsafe_allow_html=True)
                        
                        change = coin['price_change_percentage_24h'] or 0
                        color = "#2dd4bf" if change >= 0 else "#f43f5e"
                        st.markdown(f"<h2 style='margin-top:0; color:white;'>£{coin['current_price']:,.2f} <span style='color:{color}; font-size:16px;'>{change:+.2f}%</span></h2>", unsafe_allow_html=True)
                        
                        # High-End Plotly Chart
                        df_hist = fetch_history_pro(coin['id'])
                        if not df_hist.empty:
                            fig = px.line(df_hist, x='Date', y='Price', template="plotly_dark", color_discrete_sequence=['#3b82f6'])
                            fig.update_xaxes(
                                type='date', range=[start_date_7d, now_uk],
                                rangeslider_visible=False,
                                rangeselector=dict(
                                    buttons=list([
                                        dict(count=1, label="1D", step="day", stepmode="backward"),
                                        dict(count=7, label="7D", step="day", stepmode="backward"),
                                        dict(count=1, label="1M", step="month", stepmode="backward"),
                                    ]),
                                    bgcolor="rgba(255, 255, 255, 0.05)", font=dict(size=10, color="#cbd5e1"), y=1.1
                                ),
                                showgrid=False, zeroline=False
                            )
                            fig.update_yaxes(autorange=True, visible=False)
                            fig.update_layout(
                                height=200, margin=dict(l=0, r=0, t=0, b=0),
                                hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Footer holding
                        amt = user_holdings.get(coin['id'], 0)
                        if amt > 0:
                            st.markdown(f"<div style='background:rgba(59,130,246,0.1); padding:10px; border-radius:12px; border:1px solid rgba(59,130,246,0.2);'><span style='color:#94a3b8; font-size:12px;'>Holdings Value</span><br><span style='color:white; font-weight:700;'>£{coin['current_price'] * amt:,.2f}</span></div>", unsafe_allow_html=True)
else:
    st.warning("🔄 Re-establishing Satellite Connection...")
