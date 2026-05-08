import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz  # Library for timezone handling

# 1. Page Config
st.set_page_config(page_title="UK Crypto Live", layout="wide")

# 2. AUTO-REFRESH: Pings every 30 seconds
st_autorefresh(interval=30000, key="uk_refresh")

# 3. Define UK Timezone
uk_tz = pytz.timezone('Europe/London')

# 4. Your Portfolio
MY_PORTFOLIO = {
    'bitcoin': 0.1, 'ethereum': 1.0, 'solana': 10.0, 
    'ripple': 500.0, 'toncoin': 50.0, 'cardano': 250.0
}

@st.cache_data(ttl=30)
def fetch_prices():
    ids = ",".join(MY_PORTFOLIO.keys())
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h"
    return requests.get(url).json()

@st.cache_data(ttl=600)
def fetch_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=30&interval=daily"
    res = requests.get(url).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- UI START ---
st.title("🇬🇧 UK Crypto Monitor")

# Get current UK Time for the Header
now_uk = datetime.now(uk_tz).strftime("%H:%M:%S")
st.markdown(f"**Last Sync (UK Time):** `{now_uk}`")

try:
    data = fetch_prices()
    total_val = sum(c['current_price'] * MY_PORTFOLIO[c['id']] for c in data)
    st.metric("Total Balance", f"£{total_val:,.2f}")
    st.divider()

    # Define the 7D window based on UK time
    end_date = datetime.now(uk_tz)
    start_date_7d = end_date - timedelta(days=7)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # Convert API timestamp to UK Time
                        # API gives format like: 2026-05-08T10:30:12.123Z
                        api_utc = datetime.strptime(coin['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
                        uk_update_time = api_utc.astimezone(uk_tz).strftime("%H:%M:%S")

                        price = coin['current_price']
                        change = coin['price_change_percentage_24h'] or 0
                        color = "green" if change >= 0 else "red"
                        
                        # HEADER WITH UK TIME
                        st.markdown(f"<div style='display: flex; justify-content: space-between;'><b>{coin['name']}</b> <span style='color: gray; font-size: 12px;'>Updated: {uk_update_time}</span></div>", unsafe_allow_html=True)
                        st.markdown(f"### £{price:,.2f} <span style='font-size:14px; color:{color}'>({change:+.2f}%)</span>", unsafe_allow_html=True)
                        
                        # CHART
                        df = fetch_history(coin['id'])
                        fig = px.line(df, x='Date', y='Price', template="plotly_dark")
                        
                        fig.update_xaxes(
                            range=[start_date_7d, end_date],
                            rangeslider_visible=False,
                            rangeselector=dict(
                                buttons=list([
                                    dict(count=1, label="1D", step="day", stepmode="backward"),
                                    dict(count=7, label="7D", step="day", stepmode="backward"),
                                    dict(count=1, label="1M", step="month", stepmode="backward"),
                                ]),
                                bgcolor="#444", font=dict(size=11, color="white")
                            )
                        )
                        
                        fig.update_yaxes(autorange=True, visible=False)
                        fig.update_layout(height=230, margin=dict(l=5, r=5, t=10, b=10), hovermode="x unified")
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # PORTFOLIO DATA
                        amt = MY_PORTFOLIO[coin['id']]
                        if amt > 0:
                            st.caption(f"Value Owned: £{price * amt:,.2f}")

except Exception as e:
    st.info("Market data refreshing...")
