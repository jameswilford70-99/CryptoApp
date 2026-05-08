import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- 1. PAGE CONFIG & MODERN THEMEING ---
st.set_page_config(page_title="Crypto Trak", layout="wide", page_icon="📈")

# Inject Custom CSS for a "Stylish" look
st.markdown("""
    <style>
    /* Main background color */
    .stApp {
        background-color: #f8f9fb;
    }
    /* Style the containers/boxes */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border: 1px solid #e1e4e8 !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    /* Headers and Text */
    h1, h2, h3 {
        color: #1a1a1a;
        font-family: 'Inter', sans-serif;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e1e4e8;
    }
    </style>
    """, unsafe_allow_html=True)

# AUTO-REFRESH: Every 30 seconds
st_autorefresh(interval=30000, key="cryptotrak_refresh")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" 

# TOP 10 TRADED LIST
COIN_IDS = ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple', 'usd-coin', 'binancecoin', 'dogecoin', 'tron', 'toncoin']

# --- 2. SIDEBAR MANAGER ---
st.sidebar.title("💳 Crypto Trak")
st.sidebar.markdown("Manage your portfolio holdings below.")

user_holdings = {}
for cid in COIN_IDS:
    user_holdings[cid] = st.sidebar.number_input(
        f"{cid.upper()}", 
        min_value=0.0, step=0.0001, format="%.4f", key=f"trak_{cid}"
    )

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=30)
def fetch_prices_pro():
    ids = ",".join(COIN_IDS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json() if response.status_code == 200 else "RATE_LIMIT"
    except:
        return None

@st.cache_data(ttl=3600)
def fetch_history_pro(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=30&interval=daily"
    headers = {"accept": "application/json", "x-cg-demo-api-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15).json()
        df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        return df
    except:
        return pd.DataFrame()

# --- 4. UI START ---
st.title("📈 Crypto Trak")
now_uk = datetime.now(UK_TZ)
st.caption(f"Real-time Intelligence • {now_uk.strftime('%H:%M:%S')} UK")

data = fetch_prices_pro()

if data == "RATE_LIMIT":
    st.error("🚨 API Limit Reached. Refreshing soon...")
elif data is None or not isinstance(data, list):
    st.warning("📡 Syncing market data...")
else:
    # Portfolio Balance Card
    total_val = sum(c['current_price'] * user_holdings.get(c['id'], 0) for c in data)
    st.metric("Total Balance", f"£{total_val:,.2f}")
    st.divider()

    start_date_7d = now_uk - timedelta(days=7)

    # 2-Column Grid
    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # Time Sync
                        api_utc = datetime.strptime(coin['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                        uk_time = api_utc.astimezone(UK_TZ).strftime("%H:%M")

                        st.markdown(f"**{coin['name']}** <span style='float:right; color:#888; font-size:10px;'>{uk_time}</span>", unsafe_allow_html=True)
                        
                        change = coin['price_change_percentage_24h'] or 0
                        # Professional blue color for positive, coral for negative
                        color = "#0066cc" if change >= 0 else "#ff4b4b"
                        st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:14px;'>({change:+.2f}%)</span>", unsafe_allow_html=True)
                        
                        # Graph with "Modern Light" Theme
                        df_hist = fetch_history_pro(coin['id'])
                        if not df_hist.empty:
                            # Use a specific blue line for a stylish look
                            fig = px.line(df_hist, x='Date', y='Price', template="plotly_white", color_discrete_sequence=['#0066cc'])
                            fig.update_xaxes(
                                type='date', range=[start_date_7d, now_uk],
                                rangeslider_visible=False,
                                rangeselector=dict(
                                    buttons=list([
                                        dict(count=1, label="1D", step="day", stepmode="backward"),
                                        dict(count=7, label="7D", step="day", stepmode="backward"),
                                        dict(count=1, label="1M", step="month", stepmode="backward"),
                                    ]),
                                    bgcolor="#f0f2f6", font=dict(size=11, color="#1a1a1a"), y=1.1
                                ),
                                showgrid=False
                            )
                            fig.update_yaxes(autorange=True, visible=False, showgrid=False)
                            fig.update_layout(
                                height=240, 
                                margin=dict(l=5, r=5, t=5, b=5), 
                                hovermode="x unified",
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Holding Footer
                        amt = user_holdings.get(coin['id'], 0)
                        if amt > 0:
                            st.markdown(f"<p style='font-size:13px; font-weight:bold; color:#555;'>Stake Value: £{coin['current_price'] * amt:,.2f}</p>", unsafe_allow_html=True)
