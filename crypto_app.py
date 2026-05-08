import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. CONFIG & ELITE MIDNIGHT STYLING ---
st.set_page_config(page_title="Crypto Trak", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    /* Deep Midnight Background */
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
        transition: transform 0.3s ease;
    }

    /* Live Update Pulse */
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(45, 212, 191, 0); } 100% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0); } }
    .update-pulse { animation: pulse 2s infinite; border-radius: 50%; display: inline-block; width: 8px; height: 8px; background-color: #2dd4bf; margin-right: 8px; }
    
    /* Header & Badges */
    .ai-badge { background: linear-gradient(90deg, #8b5cf6, #3b82f6); color: white; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; }
    .main-header { background: linear-gradient(90deg, #60a5fa, #2dd4bf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 3rem; margin-bottom: 0px; }

    /* Sidebar Blur */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# AUTO-REFRESH (30s)
st_autorefresh(interval=30000, key="cryptotrak_v6_final")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. SIDEBAR MANAGER ---
st.sidebar.markdown("<h2 style='color: #60a5fa;'>💳 Portfolio</h2>", unsafe_allow_html=True)
user_holdings = {cid: st.sidebar.number_input(f"{cid.upper()}", min_value=0.0, step=0.0001, format="%.4f", key=f"h_{cid}") for cid in COIN_IDS}

# --- 3. DATA ENGINES ---
@st.cache_data(ttl=30)
def fetch_data():
    ids = ",".join(COIN_IDS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h&include_market_cap=true"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    return requests.get(url, headers=headers).json()

@st.cache_data(ttl=3600)
def fetch_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=365" # 365 days for 1Y support
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    res = requests.get(url, headers=headers).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    df['SMA7'] = df['Price'].rolling(window=7).mean()
    return df

# --- 4. TOP INTELLIGENCE ROW ---
st.markdown("<h1 class='main-header'>Crypto Trak</h1>", unsafe_allow_html=True)
data = fetch_data()

if data and isinstance(data, list):
    now_uk = datetime.now(UK_TZ)
    st.markdown(f"<div><span class='update-pulse'></span><span style='color:#94a3b8; font-size:14px;'>Intelligence Active • {now_uk.strftime('%H:%M:%S')} UK</span></div>", unsafe_allow_html=True)
    
    top_col1, top_col2 = st.columns([1, 2])
    with top_col1:
        with st.container(border=True):
            fg_value = 39 
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=fg_value, title={'text': "Market Sentiment", 'font': {'size': 16, 'color': 'white'}},
                gauge={'axis': {'range': [0, 100], 'tickcolor': "white"}, 'bar': {'color': "#f43f5e" if fg_value < 50 else "#2dd4bf"}}
            ))
            fig_gauge.update_layout(height=180, margin=dict(l=20,r=20,t=40,b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig_gauge, use_container_width=True)

    with top_col2:
        with st.container(border=True):
            portfolio_items = [{"Asset": c['symbol'].upper(), "Value": c['current_price'] * user_holdings[c['id']]} for c in data if user_holdings[c['id']] > 0]
            if portfolio_items:
                fig_donut = px.pie(pd.DataFrame(portfolio_items), values='Value', names='Asset', hole=.6, title="Diversification")
                fig_donut.update_layout(height=180, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, showlegend=False)
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("💡 Add holdings in the sidebar to see AI insights.")

    # --- 5. MAIN MARKET GRID ---
    st.divider()
    start_date_7d = now_uk - timedelta(days=7)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # SNUG LOGO AND NAME (Fixed Gap)
                        col_logo, col_name = st.columns([0.15, 0.85], gap="small")
                        with col_logo:
                            st.image(coin['image'], width=42)
                        with col_name:
                            api_utc = datetime.strptime(coin['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                            uk_time = api_utc.astimezone(UK_TZ).strftime("%H:%M")
                            is_whale = (coin['total_volume'] / coin['market_cap']) > 0.05
                            whale_tag = "<span class='ai-badge'>🐋 WHALE</span>" if is_whale else ""
                            st.markdown(f"""
                                <div style="line-height: 1.1;">
                                    <p style="margin: 0; font-weight: 700; font-size: 18px; color: white;">{coin['name']} {whale_tag}</p>
                                    <p style="margin: 0; color: #64748b; font-size: 11px;">{coin['symbol'].upper()} • {uk_time}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        change = coin['price_change_percentage_24h'] or 0
                        color = "#2dd4bf" if change >= 0 else "#f43f5e"
                        st.markdown(f"<h2 style='color:white; margin-top:10px;'>£{coin['current_price']:,.2f} <span style='color:{color}; font-size:16px;'>{change:+.2f}%</span></h2>", unsafe_allow_html=True)
                        
                        # AI CHART (Restore Mobile Buttons + Trendline)
                        df_hist = fetch_history(coin['id'])
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['Price'], name="Price", line=dict(color='#3b82f6', width=2.5)))
                        fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['SMA7'], name="AI Trend", line=dict(color='rgba(255,255,255,0.2)', width=1, dash='dot')))
                        
                        fig.update_xaxes(
                            type='date', range=[start_date_7d, now_uk], visible=True,
                            showgrid=False, zeroline=False,
                            rangeselector=dict(
                                buttons=list([
                                    dict(count=1, label="1D", step="day", stepmode="backward"),
                                    dict(count=7, label="7D", step="day", stepmode="backward"),
                                    dict(count=1, label="1M", step="month", stepmode="backward"),
                                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                                ]),
                                bgcolor="rgba(30, 41, 59, 0.9)", font=dict(color="white", size=12), y=1.12
                            )
                        )
                        fig.update_yaxes(autorange=True, visible=False)
                        fig.update_layout(height=240, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        if user_holdings[coin['id']] > 0:
                            st.markdown(f"<div style='background:rgba(59,130,246,0.1); padding:10px; border-radius:12px; border:1px solid rgba(59,130,246,0.2);'><span style='color:#94a3b8; font-size:12px;'>Stake Value</span><br><span style='color:white; font-weight:700;'>£{coin['current_price'] * user_holdings[coin['id']]:,.2f}</span></div>", unsafe_allow_html=True)
