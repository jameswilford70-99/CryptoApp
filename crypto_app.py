import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. Page Config (Wide mode is better for charts)
st.set_page_config(page_title="Live Crypto Feed", layout="wide")

# 2. Your Portfolio (Set your actual amounts)
MY_PORTFOLIO = {
    'bitcoin': 0.1, 'ethereum': 1.0, 'solana': 10.0, 
    'ripple': 500.0, 'toncoin': 50.0, 'cardano': 250.0
}

@st.cache_data(ttl=60)
def fetch_prices():
    ids = ",".join(MY_PORTFOLIO.keys())
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h"
    return requests.get(url).json()

@st.cache_data(ttl=300)
def fetch_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=7&interval=daily"
    res = requests.get(url).json()
    prices = res.get('prices', [])
    df = pd.DataFrame(prices, columns=['time', 'price'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

# --- UI START ---
st.title("📈 Live Crypto Feed (£)")

try:
    data = fetch_prices()
    
    # Header Metric
    total_val = sum(c['current_price'] * MY_PORTFOLIO[c['id']] for c in data)
    st.metric("Total Balance", f"£{total_val:,.2f}")
    st.divider()

    # Loop through each coin and show the graph immediately
    for coin in data:
        c_id = coin['id']
        name = coin['name']
        price = coin['current_price']
        change = coin['price_change_percentage_24h'] or 0
        
        # Create a dedicated "card" for each coin
        with st.container():
            col1, col2 = st.columns([1, 1])
            col1.subheader(f"{name} ({coin['symbol'].upper()})")
            col2.metric("Price", f"£{price:,.2f}", f"{change:.2f}%")
            
            # Fetch and show chart immediately
            hist_df = fetch_history(c_id)
            fig = px.line(hist_df, x='time', y='price', template="plotly_dark")
            
            # Minimalist Chart Design for Mobile
            fig.update_layout(
                height=200, 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_visible=False, 
                yaxis_title=None, 
                xaxis_title=None
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.write(f"Holding: {MY_PORTFOLIO[c_id]} | Value: £{price * MY_PORTFOLIO[c_id]:,.2f}")
            st.divider()

except Exception:
    st.info("Refreshing live stream...")
