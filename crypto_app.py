import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. CONFIG & ELITE STYLING ---
st.set_page_config(page_title="Crypto Trak Command", layout="wide", page_icon="🔱")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: radial-gradient(circle at top right, #0f172a, #020617) !important; font-family: 'Inter', sans-serif; }
    
    /* Command Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 15px;
    }
    
    /* Neon Glow for Price Alerts */
    .alert-glow { border: 2px solid #fbbf24 !important; box-shadow: 0 0 15px #fbbf24 !important; }
    
    .main-header { background: linear-gradient(90deg, #60a5fa, #2dd4bf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.5rem; margin-bottom: 0px; }
    
    .stButton>button { 
        background: rgba(255,255,255,0.08) !important; color: white !important; 
        border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 6px; 
        font-size: 10px !important; height: 24px !important; width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=30000, key="cryptotrak_v14_command")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. INTELLIGENCE ENGINES ---
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
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- 3. SIDEBAR: P/L ENGINE & ALERTS ---
st.sidebar.markdown("<h2 style='color: #60a5fa;'>🎮 Command Panel</h2>", unsafe_allow_html=True)
user_data = {}
for cid in COIN_IDS:
    with st.sidebar.expander(f"{cid.upper()} Settings"):
        amt = st.number_input("Amount", min_value=0.0, step=0.001, key=f"amt_{cid}")
        buy_p = st.number_input("Avg Buy Price (£)", min_value=0.0, step=1.0, key=f"buy_{cid}")
        target_p = st.number_input("Target Alert (£)", min_value=0.0, step=1.0, key=f"target_{cid}")
        user_data[cid] = {"amt": amt, "buy": buy_p, "target": target_p}

# --- 4. TOP: MARKET HEALTH INDICATORS ---
st.markdown("<h1 class='main-header'>Crypto Trak Command</h1>", unsafe_allow_html=True)
market_data = fetch_market_intel()

if market_data and isinstance(market_data, list):
    h_col1, h_col2, h_col3 = st.columns(3)
    # Simulated 2026 Live Market Stats
    h_col1.metric("BTC Dominance", "44.2%", "+0.5%")
    h_col2.metric("Liquidations (24h)", "£142M", "-12%", delta_color="inverse")
    h_col3.metric("Network Gas (ETH)", "18 Gwei", "Low")
    
    st.divider()

    # --- 5. MAIN GRID ---
    for i in range(0, len(market_data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(market_data):
                coin = market_data[i + j]
                cid = coin['id']
                u_cfg = user_data[cid]
                
                # PRICE ALERT LOGIC: Glow if within 1% of target
                is_near_target = False
                if u_cfg['target'] > 0:
                    diff = abs(coin['current_price'] - u_cfg['target']) / u_cfg['target']
                    if diff < 0.01: is_near_target = True

                with cols[j]:
                    # Dynamic CSS for Price Alert Glow
                    glow_class = "alert-glow" if is_near_target else ""
                    st.markdown(f'<div class="{glow_class}">', unsafe_allow_html=True)
                    with st.container(border=True):
                        # SNUG HEADER
                        l_col, n_col = st.columns([0.15, 0.85], gap="small")
                        l_col.image(coin['image'], width=35)
                        n_col.markdown(f"**{coin['name']}**")
                        
                        # TIME SELECTOR
                        if f"state_{cid}" not in st.session_state: st.session_state[f"state_{cid}"] = "1"
                        btn_cols = st.columns(4)
                        if btn_cols[0].button("1D", key=f"b1_{cid}"): st.session_state[f"state_{cid}"] = "1"
                        if btn_cols[1].button("1W", key=f"b7_{cid}"): st.session_state[f"state_{cid}"] = "7"
                        if btn_cols[2].button("1M", key=f"b30_{cid}"): st.session_state[f"state_{cid}"] = "30"
                        if btn_cols[3].button("1Y", key=f"b365_{cid}"): st.session_state[f"state_{cid}"] = "365"
                        
                        df_zoom = fetch_zoom_data(cid, st.session_state[f"state_{cid}"])
                        
                        if not df_zoom.empty:
                            start_p, end_p = df_zoom.iloc[0]['Price'], df_zoom.iloc[-1]['Price']
                            roi = ((end_p - start_p) / start_p) * 100
                            color = "#2dd4bf" if roi >= 0 else "#f43f5e"
                            
                            st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:15px;'>{roi:+.2f}%</span>", unsafe_allow_html=True)
                            
                            # PROFIT/LOSS CALCULATION
                            if u_cfg['amt'] > 0 and u_cfg['buy'] > 0:
                                current_val = coin['current_price'] * u_cfg['amt']
                                investment = u_cfg['buy'] * u_cfg['amt']
                                pl_val = current_val - investment
                                pl_per = (pl_val / investment) * 100
                                pl_color = "#2dd4bf" if pl_val >= 0 else "#f43f5e"
                                st.markdown(f"<div style='font-size:12px; color:#94a3b8;'>P/L: <b style='color:{pl_color}'>£{pl_val:,.2f} ({pl_per:+.2f}%)</b></div>", unsafe_allow_html=True)

                            # CHART
                            fig = go.Figure(go.Scatter(x=df_zoom['Date'], y=df_zoom['Price'], fill='tozeroy', line=dict(color='#3b82f6', width=2), fillcolor='rgba(59,130,246,0.05)'))
                            fig.update_yaxes(range=[df_zoom['Price'].min()*0.998, df_zoom['Price'].max()*1.002], side="right", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=9, color='#64748b'))
                            fig.update_xaxes(visible=False)
                            fig.update_layout(height=180, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. WHALE WATCH HEATMAP ---
    st.divider()
    st.markdown("### 🐋 Whale Watch Heatmap (Last 1H)")
    whale_cols = st.columns(5)
    whales = [
        {"coin": "BTC", "amt": "1,200", "to": "Binance"},
        {"coin": "ETH", "amt": "15,000", "to": "Unknown"},
        {"coin": "SOL", "amt": "85,000", "to": "Coinbase"},
        {"coin": "XRP", "amt": "2M", "to": "Unknown"},
        {"coin": "DOGE", "amt": "10M", "to": "Robinhood"}
    ]
    for idx, w in enumerate(whales):
        whale_cols[idx].markdown(f"""
            <div style="background:rgba(139, 92, 246, 0.1); border:1px solid #8b5cf6; padding:10px; border-radius:12px; text-align:center;">
                <p style="margin:0; font-size:10px; color:#8b5cf6; font-weight:bold;">{w['coin']} MOVE</p>
                <p style="margin:0; font-size:14px; font-weight:bold;">{w['amt']}</p>
                <p style="margin:0; font-size:10px; color:#64748b;">➡ {w['to']}</p>
            </div>
        """, unsafe_allow_html=True)
