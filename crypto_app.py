import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="Live Crypto Pro (£)", layout="wide")

# 2. AUTO-REFRESH: Pings every 30 seconds
st_autorefresh(interval=30000, key="cryptorefresh")

# 3. Your Portfolio
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
st.title("📈 Live Market Grid (£)")

# Show a global update time at the very top
current_time = datetime.now().strftime("%H:%M:%S")
st.markdown(f"**Last Global Sync:** `{current_time}`")

try:
    data = fetch_prices()
    total_val = sum(c['current_price'] * MY_PORTFOLIO[c['id']] for c in data)
    st.metric("Portfolio Total", f"£{total_val:,.2f}")
    st.divider()

    # Calculation for the 7D default window
    end_date = datetime.now()
    start_date_7d = end_date - timedelta(days=7)

    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    with st.container(border=True):
                        price = coin['current_price']
                        change = coin['price_change_percentage_24h'] or 0
                        color = "green" if change >= 0 else "red"
                        
                        # HEADER
                        st.markdown(f"**{coin['name']}**")
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
                                bgcolor="#333", font=dict(size=11)
                            )
                        )
                        
                        fig.update_yaxes(autorange=True, visible=False)
                        fig.update_layout(height=230, margin=dict(l=5, r=5, t=10, b=10), hovermode="x unified")
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # HOLDING INFO & TIMESTAMP
                        amt = MY_PORTFOLIO[coin['id']]
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.caption(f"Value: £{price * amt:,.2f}")
                        with col_b:
                            # Pull the specific 'last_updated' from the API data
                            api_time = datetime.strptime(coin['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
                            # Format for UK time (adjusting to local if needed)
                            formatted_api_time = api_time.strftime("%H:%M:%S")
                            st.markdown(f"<p style='text-align:right; font-size:12px; color:gray;'>Updated: {formatted_api_time}</p>", unsafe_allow_html=True)

except Exception:
    st.info("Syncing prices...")
