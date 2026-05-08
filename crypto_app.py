import streamlit as st
import pandas as pd
import requests
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
        background: rgba(255,255,255,0.08) !important; 
        color: white !important; 
        border: 1px solid rgba(255,255,255,0.2) !important; 
        border-radius: 6px; 
        font-size: 11px !important; 
        height: 26px !important; 
        width: 100% !important;
    }
    .stButton>button:active { background: #3b82f6 !important; }
    </style>
    """, unsafe_allow_html=True)

st_autorefresh(interval=30000, key="cryptotrak_v13_force")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. THE FORCE-ZOOM DATA ENGINE ---
@st.cache_data(ttl=30)
def fetch_market_caps():
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={','.join(COIN_IDS)}"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    return requests.get(url, headers=headers).json()

@st.cache_data(ttl=60)
def fetch_zoom_data(coin_id, days):
    # Using a unique name for this function ensures the cache handles 1D vs 1Y separately
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days={days}"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    res = requests.get(url, headers=headers).json()
    
    prices = res.get('prices', [])
    if not prices: return pd.DataFrame()
    
    df = pd.DataFrame(prices, columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- 3. UI ---
st.markdown("<h1 class='main-header'>Crypto Trak</h1>", unsafe_allow_html=True)
market_data = fetch_market_caps()

if market_data and isinstance(market_data, list):
    st.sidebar.markdown("<h2 style='color: #60a5fa;'>💳 Portfolio</h2>", unsafe_allow_html=True)
    user_holdings = {c['id']: st.sidebar.number_input(f"{c['id'].upper()}", min_value=0.0, step=0.0001, format="%.4f", key=f"h_{c['id']}") for c in market_data}

    for i in range(0, len(market_data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(market_data):
                coin = market_data[i + j]
                cid = coin['id']
                
                with cols[j]:
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
                        
                        # FETCH DATA BASED ON STATE
                        current_days = st.session_state[f"state_{cid}"]
                        df_zoom = fetch_zoom_data(cid, current_days)
                        
                        if not df_zoom.empty:
                            # CALC ROI
                            start_p, end_p = df_zoom.iloc[0]['Price'], df_zoom.iloc[-1]['Price']
                            roi = ((end_p - start_p) / start_p) * 100
                            color = "#2dd4bf" if roi >= 0 else "#f43f5e"
                            
                            st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:15px;'>{roi:+.2f}%</span>", unsafe_allow_html=True)
                            
                            # --- THE CHART ---
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=df_zoom['Date'], 
                                y=df_zoom['Price'], 
                                fill='tozeroy',
                                line=dict(color='#3b82f6', width=2),
                                fillcolor='rgba(59, 130, 246, 0.1)',
                                hovertemplate='£%{y:,.2f}<extra></extra>'
                            ))
                            
                            # Tighten Y-axis to the data range
                            y_min = df_zoom['Price'].min() * 0.999
                            y_max = df_zoom['Price'].max() * 1.001
                            
                            fig.update_yaxes(
                                range=[y_min, y_max], 
                                side="right", 
                                showgrid=True, 
                                gridcolor='rgba(255,255,255,0.05)',
                                tickfont=dict(size=9, color='#64748b')
                            )
                            
                            fig.update_xaxes(visible=False)
                            fig.update_layout(
                                height=220, 
                                margin=dict(l=0,r=0,t=10,b=0),
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Stake Footer
                        amt = user_holdings.get(cid, 0)
                        if amt > 0:
                            st.caption(f"Portfolio: £{coin['current_price'] * amt:,.2f}")
