import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# --- CONFIG ---
st.set_page_config(page_title="UK Crypto Live (Pro)", layout="wide")
st_autorefresh(interval=30000, key="pro_refresh")

UK_TZ = pytz.timezone('Europe/London')
API_KEY = "CG-zdKJGMzSeZTkt6xYURjcse11" # Your Key
COIN_IDS = ['bitcoin', 'ethereum', 'solana', 'ripple', 'toncoin', 'cardano']

# Sidebar for holdings
st.sidebar.title("💰 My Holdings")
user_holdings = {cid: st.sidebar.number_input(f"{cid.capitalize()}", min_value=0.0, step=0.0001, format="%.4f") for cid in COIN_IDS}

# --- DATA FETCHING (PRO VERSION) ---
@st.cache_data(ttl=30)
def fetch_prices_pro():
    ids = ",".join(COIN_IDS)
    # Pro/Demo Keys use this specific URL
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h"
    
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": API_KEY  # Authenticates your requests
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 429:
            return "RATE_LIMIT"
        return response.json()
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

# --- UI LOGIC ---
st.title("🇬🇧 UK Crypto Pro Feed")
now_uk = datetime.now(UK_TZ)
st.write(f"Last Sync: **{now_uk.strftime('%H:%M:%S')}**")

data = fetch_prices_pro()

if data == "RATE_LIMIT":
    st.error("🚨 Even with a key, the limit was hit. Please wait 1 minute.")
elif data is None or not isinstance(data, list):
    st.warning("📡 Waiting for market data...")
else:
    total_val = sum(c['current_price'] * user_holdings.get(c['id'], 0) for c in data)
    st.metric("Total Portfolio", f"£{total_val:,.2f}")
    st.divider()

    start_date_7d = now_uk - timedelta(days=7)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # Convert API time to UK
                        api_utc = datetime.strptime(coin['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                        uk_time = api_utc.astimezone(UK_TZ).strftime("%H:%M")

                        st.markdown(f"**{coin['name']}** <span style='float:right; color:gray; font-size:10px;'>{uk_time}</span>", unsafe_allow_html=True)
                        
                        change = coin['price_change_percentage_24h'] or 0
                        color = "green" if change >= 0 else "red"
                        st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:14px;'>({change:+.2f}%)</span>", unsafe_allow_html=True)
                        
                        # Show Zoomed 7D Chart by default
                        df_hist = fetch_history_pro(coin['id'])
                        if not df_hist.empty:
                            fig = px.line(df_hist, x='Date', y='Price', template="plotly_dark")
                            fig.update_xaxes(
                                type='date',
                                range=[start_date_7d, now_uk],
                                rangeslider_visible=False,
                                rangeselector=dict(
                                    buttons=list([
                                        dict(count=1, label="1D", step="day", stepmode="backward"),
                                        dict(count=7, label="7D", step="day", stepmode="backward"),
                                        dict(count=1, label="1M", step="month", stepmode="backward"),
                                    ]),
                                    bgcolor="#333", font=dict(size=11), y=1.1
                                )
                            )
                            fig.update_yaxes(autorange=True, visible=False)
                            fig.update_layout(height=240, margin=dict(l=5, r=5, t=5, b=5), hovermode="x unified")
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        amt = user_holdings.get(coin['id'], 0)
                        if amt > 0:
                            st.info(f"Value: £{coin['current_price'] * amt:,.2f}")
