import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="Crypto Detailed Grid", layout="wide")

# 2. Your Portfolio
MY_PORTFOLIO = {
    'bitcoin': 0.1, 'ethereum': 1.0, 'solana': 10.0, 
    'ripple': 500.0, 'toncoin': 50.0, 'cardano': 250.0
}

@st.cache_data(ttl=60)
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

st.title("📈 Detailed Market View (£)")

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
                        
                        st.markdown(f"**{coin['name']}**")
                        st.markdown(f"### £{price:,.2f} <span style='font-size:14px; color:{color}'>({change:+.2f}%)</span>", unsafe_allow_html=True)
                        
                        # Fetch Data
                        df = fetch_history(coin['id'])
                        
                        # Create Chart
                        fig = px.line(df, x='Date', y='Price', template="plotly_dark")
                        
                        # --- THE ZOOM LOGIC ---
                        fig.update_xaxes(
                            range=[start_date_7d, end_date], # Force default to 7 Days
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
                        
                        fig.update_yaxes(
                            autorange=True, # Automatically zooms in on the data points
                            fixedrange=False,
                            showgrid=False,
                            visible=False # Keep it clean
                        )
                        
                        fig.update_layout(
                            height=250,
                            margin=dict(l=5, r=5, t=10, b=10),
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Holding Info
                        amt = MY_PORTFOLIO[coin['id']]
                        if amt > 0:
                            st.caption(f"My Stake: {amt} {coin['symbol'].upper()} (Value: £{price * amt:,.2f})")

except Exception as e:
    st.error("Market data is refreshing...")
