import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. Page Configuration for Mobile
st.set_page_config(page_title="GBP Crypto Live", layout="wide", initial_sidebar_state="collapsed")

# 2. Your Portfolio (Enter the amount you own here)
MY_PORTFOLIO = {
    'bitcoin': 0.1, 'ethereum': 1.0, 'solana': 10.0, 'ripple': 500.0,
    'binancecoin': 0.5, 'dogecoin': 1000.0, 'cardano': 500.0, 'toncoin': 20.0,
    'chainlink': 15.0, 'pepe': 0, 'shiba-inu': 0, 'litecoin': 5.0
}

# 3. Data Fetching Functions
@st.cache_data(ttl=120) # Auto-refresh data every 2 mins
def fetch_market_data():
    ids = ",".join(MY_PORTFOLIO.keys())
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp&ids={ids}&price_change_percentage=24h,7d"
    return requests.get(url).json()

@st.cache_data(ttl=600) # Charts cached for 10 mins
def fetch_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=30&interval=daily"
    response = requests.get(url).json()
    prices = response.get('prices', [])
    df = pd.DataFrame(prices, columns=['time', 'price'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

# --- APP UI ---
st.title("🇬🇧 Live Crypto Tracker")

try:
    data = fetch_market_data()
    total_gbp = sum(coin['current_price'] * MY_PORTFOLIO.get(coin['id'], 0) for coin in data)

    # Big Total at the top
    st.metric("Total Portfolio Value", f"£{total_gbp:,.2f}")
    st.divider()

    # Search Bar
    search = st.text_input("🔍 Search coins...", "").lower()

    for coin in data:
        if search and search not in coin['name'].lower() and search not in coin['symbol'].lower():
            continue
            
        # Extract coin details
        c_id = coin['id']
        name = coin['name']
        price = coin['current_price']
        change_24h = coin['price_change_percentage_24h'] or 0
        
        # Display Coin Summary
        with st.expander(f"**{name}** | £{price:,.2f} | ({change_24h:+.2f}%)"):
            st.write(f"**Your Holding:** {MY_PORTFOLIO[c_id]} {coin['symbol'].upper()} (£{price * MY_PORTFOLIO[c_id]:,.2f})")
            
            # THE LIVE GRAPH
            if st.button(f"Load 30D Graph for {name}", key=f"btn_{c_id}"):
                with st.spinner('Loading live data...'):
                    history_df = fetch_history(c_id)
                    fig = px.line(history_df, x='time', y='price', 
                                 title=f"{name} Price Trend (30 Days)",
                                 template="plotly_dark")
                    fig.update_layout(xaxis_title="", yaxis_title="Price (£)", height=300)
                    st.plotly_chart(fig, use_container_width=True)

except Exception:
    st.warning("Data is refreshing... please wait a few seconds.")
