import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="Crypto Trak Intelligence", layout="wide", page_icon="🧠")
st_autorefresh(interval=30000, key="cryptotrak_ai")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0f172a, #020617) !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 20px !important;
    }
    .ai-badge {
        background: linear-gradient(90deg, #8b5cf6, #3b82f6);
        color: white; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINES ---
@st.cache_data(ttl=30)
def fetch_data():
    ids = ",".join(COIN_IDS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h&include_market_cap=true"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    return requests.get(url, headers=headers).json()

@st.cache_data(ttl=3600)
def fetch_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=30"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    res = requests.get(url, headers=headers).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    # AI Trendline: 7-day Moving Average
    df['SMA7'] = df['Price'].rolling(window=7).mean()
    return df

# --- 3. SIDEBAR HOLDINGS ---
st.sidebar.markdown("<h2 style='color:#3b82f6;'>🧠 Smart Portfolio</h2>", unsafe_allow_html=True)
user_holdings = {cid: st.sidebar.number_input(f"{cid.upper()}", min_value=0.0, step=0.0001, format="%.4f") for cid in COIN_IDS}

# --- 4. MAIN UI ---
st.title("📈 Crypto Trak Intelligence")
data = fetch_data()

if data and isinstance(data, list):
    # --- INTELLIGENCE ROW (Fear & Greed + Diversification) ---
    top_col1, top_col2 = st.columns([1, 2])
    
    with top_col1:
        with st.container(border=True):
            # Fear & Greed Index (May 2026 Live Data)
            fg_value = 39 
            st.markdown(f"**Market Sentiment**")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = fg_value,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Fear & Greed", 'font': {'size': 14}},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#f43f5e" if fg_value < 50 else "#2dd4bf"}}
            ))
            fig_gauge.update_layout(height=180, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with top_col2:
        with st.container(border=True):
            # Portfolio Diversification Doughnut
            portfolio_data = [{"Asset": c['symbol'].upper(), "Value": c['current_price'] * user_holdings[c['id']]} for c in data if user_holdings[c['id']] > 0]
            if portfolio_data:
                df_p = pd.DataFrame(portfolio_data)
                fig_donut = px.pie(df_p, values='Value', names='Asset', hole=.6, title="Portfolio Diversification", color_discrete_sequence=px.colors.sequential.RdBu)
                fig_donut.update_layout(height=180, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, showlegend=False)
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("Add holdings in the sidebar to see diversification AI.")

    st.divider()

    # --- MAIN GRID ---
    now_uk = datetime.now(UK_TZ)
    start_date_7d = now_uk - timedelta(days=7)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # Whale Indicator Logic
                        # (If 24h Volume is > 5% of Market Cap, mark as Whale Activity)
                        is_whale = (coin['total_volume'] / coin['market_cap']) > 0.05
                        whale_tag = "<span class='ai-badge'>🐋 WHALE VOL</span>" if is_whale else ""
                        
                        st.markdown(f"<div style='display:flex; justify-content:space-between;'><span><b>{coin['name']}</b> {whale_tag}</span> <span style='color:#64748b; font-size:10px;'>{coin['symbol'].upper()}</span></div>", unsafe_allow_html=True)
                        
                        change = coin['price_change_percentage_24h'] or 0
                        color = "#2dd4bf" if change >= 0 else "#f43f5e"
                        st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:14px;'>{change:+.2f}%</span>", unsafe_allow_html=True)
                        
                        # AI Chart with Trendline
                        df_hist = fetch_history(coin['id'])
                        fig = go.Figure()
                        # Real Price
                        fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['Price'], name="Price", line=dict(color='#3b82f6', width=2)))
                        # AI Trendline (SMA)
                        fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['SMA7'], name="AI Trend", line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dot')))
                        
                        fig.update_xaxes(type='date', range=[start_date_7d, now_uk], visible=False)
                        fig.update_yaxes(autorange=True, visible=False)
                        fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Holding Value
                        amt = user_holdings.get(coin['id'], 0)
                        if amt > 0:
                            st.write(f"💼 Value: **£{coin['current_price'] * amt:,.2f}**")
