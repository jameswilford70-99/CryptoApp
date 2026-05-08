import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# 1. Page Config
st.set_page_config(page_title="UK Crypto Live", layout="wide")

# 2. AUTO-REFRESH (30 seconds)
st_autorefresh(interval=30000, key="uk_refresh")

uk_tz = pytz.timezone('Europe/London')

# 3. Portfolio & Data Fetching
COIN_IDS = ['bitcoin', 'ethereum', 'solana', 'ripple', 'toncoin', 'cardano']

# Sidebar for holdings
st.sidebar.title("💰 My Holdings")
user_holdings = {}
for coin_id in COIN_IDS:
    user_holdings[coin_id] = st.sidebar.number_input(f"{coin_id.capitalize()}", min_value=0.0, step=0.001, format="%.4f")

@st.cache_data(ttl=30)
def fetch_prices():
    ids = ",".join(COIN_IDS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h"
    return requests.get(url).json()

@st.cache_data(ttl=600)
def fetch_history(coin_id):
    # Fetch 30 days of data to support the 1M button
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=30&interval=daily"
    res = requests.get(url).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- UI ---
st.title("🇬🇧 UK Crypto Monitor")
now_uk = datetime.now(uk_tz)
st.markdown(f"**Last Sync:** `{now_uk.strftime('%H:%M:%S')}`")

try:
    data = fetch_prices()
    total_val = sum(c['current_price'] * user_holdings.get(c['id'], 0) for c in data)
    st.metric("Total Balance", f"£{total_val:,.2f}")
    st.divider()

    # Calculate the 7D default window
    start_date_7d = now_uk - timedelta(days=7)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # Time Handling
                        api_utc = datetime.strptime(coin['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                        uk_time = api_utc.astimezone(uk_tz).strftime("%H:%M")

                        st.markdown(f"**{coin['name']}** <span style='float:right; color:gray; font-size:10px;'>{uk_time}</span>", unsafe_allow_html=True)
                        
                        color = "green" if coin['price_change_percentage_24h'] >= 0 else "red"
                        st.markdown(f"### £{coin['current_price']:,.2f} <span style='color:{color}; font-size:14px;'>({coin['price_change_percentage_24h']:+.2f}%)</span>", unsafe_allow_html=True)
                        
                        # Graphing
                        df = fetch_history(coin['id'])
                        fig = px.line(df, x='Date', y='Price', template="plotly_dark")
                        
                        # FIX: Explicitly add Range Selector Buttons back
                        fig.update_xaxes(
                            type='date',
                            range=[start_date_7d, now_uk], # This sets the 7D DEFAULT
                            rangeslider_visible=False,
                            rangeselector=dict(
                                buttons=list([
                                    dict(count=1, label="1D", step="day", stepmode="backward"),
                                    dict(count=7, label="7D", step="day", stepmode="backward"),
                                    dict(count=1, label="1M", step="month", stepmode="backward"),
                                ]),
                                bgcolor="#2c2c2c",
                                font=dict(color="white", size=11),
                                x=0, y=1.1 # Position buttons above chart
                            )
                        )
                        
                        fig.update_yaxes(autorange=True, visible=False)
                        fig.update_layout(height=240, margin=dict(l=5, r=5, t=5, b=5), hovermode="x unified")
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        amt = user_holdings.get(coin['id'], 0)
                        if amt > 0:
                            st.write(f"Value: **£{coin['current_price'] * amt:,.2f}**")

except Exception as e:
    st.info("Market data syncing...")
