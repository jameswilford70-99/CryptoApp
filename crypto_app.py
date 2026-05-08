import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. CONFIG & TITAN STYLING ---
st.set_page_config(page_title="Crypto Trak Titan", layout="wide", page_icon="🔱")

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
    
    .stealth-blur { filter: blur(8px); pointer-events: none; user-select: none; }
    .heat-bar { height: 4px; width: 100%; border-radius: 2px; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #60a5fa, #2dd4bf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.5rem; margin-bottom: 0px; }
    
    .stButton>button { 
        background: rgba(255,255,255,0.08) !important; color: white !important; 
        border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 6px; 
        font-size: 10px !important; height: 24px !important; width: 100% !important;
    }
    .stButton>button:active { background: #3b82f6 !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=30000, key="cryptotrak_v16_final")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. CALLBACKS (THE FIX) ---
def update_zoom(coin_id, days):
    st.session_state[f"state_{coin_id}"] = days

# --- 3. DATA ENGINES ---
@st.cache_data(ttl=30)
def fetch_market_intel():
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={','.join(COIN_IDS)}&price_change_percentage=24h"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    return requests.get(url, headers=headers).json()

@st.cache_data(ttl=60)
def fetch_zoom_data(coin_id, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days={days}"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    res = requests.get(url, headers=headers).json()
    prices = res.get('prices', [])
    if not prices: return pd.DataFrame()
    df = pd.DataFrame(prices, columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- 4. SIDEBAR & STEALTH ---
st.sidebar.markdown("<h2 style='color: #60a5fa;'>🛡️ Titan Security</h2>", unsafe_allow_html=True)
stealth_mode = st.sidebar.toggle("Stealth Mode", value=False)
chart_style = st.sidebar.radio("Chart Type", ["Modern Line", "Pro Candlestick"])

user_data = {}
for cid in COIN_IDS:
    with st.sidebar.expander(f"{cid.upper()} Settings"):
        amt = st.number_input("Amount", min_value=0.0, step=0.001, key=f"amt_{cid}")
        buy_p = st.number_input("Avg Buy Price (£)", min_value=0.0, step=1.0, key=f"buy_{cid}")
        user_data[cid] = {"amt": amt, "buy": buy_p}

# --- 5. UI MAIN ---
market_data = fetch_market_intel()
if market_data and isinstance(market_data, list):
    avg_change = sum(c['price_change_percentage_24h'] for c in market_data) / len(market_data)
    heat_color = "#2dd4bf" if avg_change > 0 else "#f43f5e"
    st.markdown(f'<div class="heat-bar" style="background: {heat_color}; box-shadow: 0 0 10px {heat_color};"></div>', unsafe_allow_html=True)
    st.markdown("<h1 class='main-header'>Crypto Trak Titan</h1>", unsafe_allow_html=True)
    
    for i in range(0, len(market_data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(market_data):
                coin = market_data[i + j]
                cid = coin['id']
                
                with cols[j]:
                    with st.container(border=True):
                        # HEADER
                        l_col, n_col = st.columns([0.15, 0.85], gap="small")
                        l_col.image(coin['image'], width=35)
                        n_col.markdown(f"**{coin['name']}**")
                        
                        # BUTTONS WITH CALLBACKS (THE FIX)
                        if f"state_{cid}" not in st.session_state: st.session_state[f"state_{cid}"] = "7"
                        btn_cols = st.columns(4)
                        btn_cols[0].button("1D", key=f"b1_{cid}", on_click=update_zoom, args=(cid, "1"))
                        btn_cols[1].button("1W", key=f"b7_{cid}", on_click=update_zoom, args=(cid, "7"))
                        btn_cols[2].button("1M", key=f"b30_{cid}", on_click=update_zoom, args=(cid, "30"))
                        btn_cols[3].button("1Y", key=f"b365_{cid}", on_click=update_zoom, args=(cid, "365"))
                        
                        df_zoom = fetch_zoom_data(cid, st.session_state[f"state_{cid}"])
                        
                        if not df_zoom.empty:
                            start_p, end_p = df_zoom.iloc[0]['Price'], df_zoom.iloc[-1]['Price']
                            roi = ((end_p - start_p) / start_p) * 100
                            color = "#2dd4bf" if roi >= 0 else "#f43f5e"
                            st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:15px;'>{roi:+.2f}%</span>", unsafe_allow_html=True)
                            
                            # PROFIT/LOSS
                            u_cfg = user_data[cid]
                            if u_cfg['amt'] > 0 and u_cfg['buy'] > 0:
                                pl_val = (coin['current_price'] - u_cfg['buy']) * u_cfg['amt']
                                pl_color = "#2dd4bf" if pl_val >= 0 else "#f43f5e"
                                stealth_class = "stealth-blur" if stealth_mode else ""
                                st.markdown(f"<div class='{stealth_class}' style='font-size:12px; color:#94a3b8;'>P/L: <b style='color:{pl_color}'>£{pl_val:,.2f}</b></div>", unsafe_allow_html=True)

                            # CHART
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df_zoom['Date'], y=df_zoom['Price'], fill='tozeroy', line=dict(color='#3b82f6', width=2), fillcolor='rgba(59,130,246,0.1)'))
                            fig.update_yaxes(range=[df_zoom['Price'].min()*0.999, df_zoom['Price'].max()*1.001], side="right", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=9, color='#64748b'))
                            fig.update_xaxes(visible=False)
                            fig.update_layout(height=200, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
