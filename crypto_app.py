import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Mobile-first page config
st.set_page_config(page_title="Crypto Tracker 2026", layout="wide")

# The "Must-Watch" List (CoinGecko IDs)
COMMON_COINS = [
    'bitcoin', 'ethereum', 'solana', 'ripple', 'binancecoin', 
    'cardano', 'dogecoin', 'avalanche-2', 'tron', 'chainlink',
    'polkadot', 'matic-network', 'shiba-inu', 'litecoin', 'uniswap'
]

@st.cache_data(ttl=300)
def fetch_market_data():
    ids = ",".join(COMMON_COINS)
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids}&price_change_percentage=7d,30d"
    return requests.get(url).json()

def get_history(coin_id, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
    try:
        res = requests.get(url).json()
        return [p[1] for p in res['prices']]
    except:
        return []

st.title("💰 Market Watch 2026")

# Sidebar for total portfolio tracking
st.sidebar.header("My Portfolio Settings")
user_btc = st.sidebar.number_input("How much BTC do you own?", min_value=0.0, value=0.0)
user_eth = st.sidebar.number_input("How much ETH do you own?", min_value=0.0, value=0.0)

try:
    data = fetch_market_data()
    
    # Search Bar for Mobile
    search_query = st.text_input("🔍 Search for a coin...", "").lower()

    for coin in data:
        if search_query and search_query not in coin['name'].lower() and search_query not in coin['symbol'].lower():
            continue
            
        name = coin['name']
        symbol = coin['symbol'].upper()
        price = coin['current_price']
        c_7d = coin.get('price_change_percentage_7d_in_currency', 0)
        c_30d = coin.get('price_change_percentage_30d_in_currency', 0)

        # Main Card for each coin
        with st.expander(f"{name} ({symbol}) — ${price:,.2f}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Price", f"${price:,.2f}")
            col2.metric("7D Change", f"{c_7d:.2f}%", delta=f"{c_7d:.2f}%")
            col3.metric("30D Change", f"{c_30d:.2f}%", delta=f"{c_30d:.2f}%")

            # 30-Day Trend Chart
            history = get_history(coin['id'], 30)
            if history:
                fig = px.line(history, labels={'value': 'Price', 'index': 'Days Ago'}, height=250)
                fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("Live market data is currently refreshing. Please wait 30 seconds.")
