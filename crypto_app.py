import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. CONFIG & ELITE TITAN STYLING ---
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
    .heat-bar { height: 4px; width: 100%; border-radius: 2px; margin-bottom: 20px; transition: background 1s ease; }
    .main-header { background: linear-gradient(90deg, #60a5fa, #2dd4bf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.5rem; margin-bottom: 0px; }
    
    .stButton>button { 
        background: rgba(255,255,255,0.08) !important; color: white !important; 
        border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 6px; 
        font-size: 10px !important; height: 24px !important; width: 100% !important;
    }
    .stButton>button:active { background: #3b82f6 !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=30000, key="cryptotrak_titan_ultimate")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. INTELLIGENCE DATA: CATALYSTS ---
# Real historical and forward-looking events for 2025/2026
CATALYSTS = {
    "bitcoin": [
        {"date": "2024-04-19", "title": "4th Halving", "desc": "Mining rewards slashed to 3.125 BTC."},
        {"date": "2024-01-10", "title": "Spot ETF Approval", "desc": "Institutional wall of money activated."},
        {"date": "2026-05-05", "title": "Consensus Miami", "desc": "Focus on institutional BTC custody."}
    ],
    "ethereum": [
        {"date": "2024-03-13", "title": "Dencun Upgrade", "desc": "Enabled blobs; L2 fees dropped 99%."},
        {"date": "2025-05-07", "title": "Pectra Activation", "desc": "Introduced smart accounts & institutional staking."},
        {"date": "2025-12-03", "title": "Fusaka Hard Fork", "desc": "Scaled rollup data via PeerDAS."},
        {"date": "2026-03-15", "title": "Institutional Peak", "desc": "Corporate ETH holdings breach $16B."}
    ],
    "solana": [
        {"date": "2025-12-12", "title": "Firedancer Mainnet", "desc": "Critical reliability & performance client launch."},
        {"date": "2026-04-29", "title": "TOKEN2049 Dubai", "desc": "Massive global liquidity expansion."}
    ]
}

# --- 3. CALLBACKS & DATA ENGINES ---
def update_zoom(coin_id, days):
    st.session_state[f"state_{coin_id}"] = days

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

# --- 4. SIDEBAR SETTINGS ---
st.sidebar.markdown("<h2 style='color: #60a5fa;'>🛡️ Titan Panel</h2>", unsafe_allow_html=True)
stealth_mode = st.sidebar.toggle("Stealth Mode", value=False)
chart_style = st.sidebar.radio("Display Mode", ["Modern Line", "Pro Candlestick"])

user_data = {}
for cid in COIN_IDS:
    with st.sidebar.expander(f"{cid.upper()} Stats"):
        amt = st.number_input("Holdings", min_value=0.0, step=0.01, key=f"amt_{cid}")
        buy_p = st.number_input("Avg Buy (£)", min_value=0.0, step=1.0, key=f"buy_{cid}")
        user_data[cid] = {"amt": amt, "buy": buy_p}

# --- 5. MAIN COMMAND INTERFACE ---
market_data = fetch_market_intel()

if market_data and isinstance(market_data, list):
    # Heat Bar
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
                        # Header with Dip Detection
                        l_col, n_col, d_col = st.columns([0.15, 0.7, 0.15], gap="small")
                        l_col.image(coin['image'], width=35)
                        n_col.markdown(f"**{coin['name']}**")
                        if coin['ath_change_percentage'] < -15:
                            d_col.markdown("🎯 <span style='color:#60a5fa; font-size:9px;'>DIP</span>", unsafe_allow_html=True)
                        
                        # Controls
                        if f"state_{cid}" not in st.session_state: st.session_state[f"state_{cid}"] = "7"
                        btn_cols = st.columns(4)
                        btn_cols[0].button("1D", key=f"b1_{cid}", on_click=update_zoom, args=(cid, "1"))
                        btn_cols[1].button("1W", key=f"b7_{cid}", on_click=update_zoom, args=(cid, "7"))
                        btn_cols[2].button("1M", key=f"b30_{cid}", on_click=update_zoom, args=(cid, "30"))
                        btn_cols[3].button("1Y", key=f"b365_{cid}", on_click=update_zoom, args=(cid, "365"))
                        
                        days_selected = st.session_state[f"state_{cid}"]
                        df = fetch_zoom_data(cid, days_selected)
                        
                        if not df.empty:
                            start_p, end_p = df.iloc[0]['Price'], df.iloc[-1]['Price']
                            roi = ((end_p - start_p) / start_p) * 100
                            color = "#2dd4bf" if roi >= 0 else "#f43f5e"
                            
                            st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:15px;'>{roi:+.2f}%</span>", unsafe_allow_html=True)
                            
                            # Stealth P/L
                            u_cfg = user_data[cid]
                            if u_cfg['amt'] > 0 and u_cfg['buy'] > 0:
                                profit = (coin['current_price'] - u_cfg['buy']) * u_cfg['amt']
                                p_color = "#2dd4bf" if profit >= 0 else "#f43f5e"
                                stealth_css = "stealth-blur" if stealth_mode else ""
                                st.markdown(f"<div class='{stealth_css}' style='font-size:11px; color:#94a3b8;'>Stake Profit: <b style='color:{p_color}'>£{profit:,.2f}</b></div>", unsafe_allow_html=True)

                            # --- SMART CATALYST CHART ---
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df['Date'], y=df['Price'], fill='tozeroy', line=dict(color='#3b82f6', width=2), fillcolor='rgba(59,130,246,0.05)', hovertemplate='Price: £%{y:,.2f}<extra></extra>'))
                            
                            # Add "i" Catalyst Markers on 1Y View
                            if days_selected == "365" and cid in CATALYSTS:
                                for cat in CATALYSTS[cid]:
                                    cat_date = pd.to_datetime(cat['date'])
                                    if cat_date > df['Date'].min():
                                        # Find closest price for the marker
                                        # (Simple estimation for the chart position)
                                        fig.add_annotation(
                                            x=cat['date'], y=df.loc[(df['Date']-cat_date).abs().idxmin()]['Price'],
                                            text="ⓘ", showarrow=False, font=dict(color="#60a5fa", size=14),
                                            hovertext=f"<b>{cat['title']}</b><br>{cat['desc']}",
                                            bgcolor="rgba(15, 23, 42, 0.8)", bordercolor="#60a5fa", borderwidth=1
                                        )

                            fig.update_yaxes(range=[df['Price'].min()*0.998, df['Price'].max()*1.002], side="right", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=9, color='#64748b'))
                            fig.update_xaxes(visible=False)
                            fig.update_layout(height=220, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
