import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="My Crypto Monitor (£)", layout="wide")

# 2. Top 20 Most Traded Coins (May 2026 Update)
# Adjust the 'holdings' numbers to your actual amounts!
MY_PORTFOLIO = {
    'bitcoin': 0.1, 'ethereum': 1.0, 'solana': 15.0, 'ripple': 500.0,
    'binancecoin': 0.5, 'dogecoin': 2000.0, 'cardano': 1000.0, 'tron': 0,
    'toncoin': 50.0, 'shiba-inu': 0, 'avalanche-2': 5.0, 'polkadot': 20.0,
    'chainlink': 15.0, 'near': 100.0, 'pepe': 0, 'litecoin': 2.0,
    'bitcoin-cash': 0, 'sui': 100.0, 'aptos': 0, 'render-token': 10.0
}

@st.cache_data(ttl=120)
def fetch_top_data_gbp():
    ids = ",".join(MY_PORTFOLIO.keys())
    # Note: vs_currency is now 'gbp'
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h,7d,30d"
    return requests.get(url).json()

@st.cache_data(ttl=3600)
def get_history_gbp(coin_id, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days={days}&interval=daily"
    res = requests.get(url).json()
    return [p[1] for p in res.get('prices', [])]

# --- APP UI ---
st.title("🇬🇧 Personal Crypto Dashboard")
st.markdown("Prices in British Pounds (£)")

try:
    data = fetch_top_data_gbp()
    total_val_gbp = 0
    
    # Pre-calculate Total Portfolio Value in GBP
    for coin in data:
        total_val_gbp += coin['current_price'] * MY_PORTFOLIO.get(coin['id'], 0)

    # Global Metric Header
    st.metric("Total Balance (£)", f"£{total_val_gbp:,.2f}")
    st.divider()

    # Search feature for quick access on mobile
    search = st.text_input("🔍 Search coins...", "").lower()

    for coin in data:
        if search and search not in coin['name'].lower() and search not in coin['symbol'].lower():
            continue
            
        name = coin['name']
        symbol = coin['symbol'].upper()
        price = coin['current_price']
        holdings = MY_PORTFOLIO.get(coin['id'], 0)
        coin_total = price * holdings
        
        # Change metrics
        c24 = coin.get('price_change_percentage_24h', 0) or 0
        c7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
        c30d = coin.get('price_change_percentage_30d_in_currency', 0) or 0

        # Mobile-friendly expandable view
        with st.expander(f"**{name}** ({symbol}) - £{price:,.2f}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("24h", f"{c24:+.1f}%")
            col2.metric("7d", f"{c7d:+.1f}%")
            col3.metric("30d", f"{c30d:+.1f}%")
            
            if holdings > 0:
                st.success(f"Holdings: {holdings} {symbol} | Value: £{coin_total:,.2f}")
            
            # Interactive Plotly Chart
            if st.button(f"Show 30D Trend for {symbol}", key=coin['id']):
                hist = get_history_gbp(coin['id'], 30)
                if hist:
                    fig = px.line(hist, labels={'value': 'Price (£)', 'index': 'Days Ago'})
                    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("API update pending. Please refresh in a moment.")
