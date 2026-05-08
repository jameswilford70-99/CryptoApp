import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Crypto Live Pro", layout="wide")

# 1. Your Portfolio
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
def fetch_long_history(coin_id):
    # Fetching 365 days so the buttons have data to work with
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=365&interval=daily"
    res = requests.get(url).json()
    prices = res.get('prices', [])
    df = pd.DataFrame(prices, columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

# --- UI ---
st.title("📈 Pro Crypto Monitor (£)")

try:
    data = fetch_prices()
    total_val = sum(c['current_price'] * MY_PORTFOLIO[c['id']] for c in data)
    st.metric("Total Balance", f"£{total_val:,.2f}")
    st.divider()

    for coin in data:
        c_id = coin['id']
        name = coin['name']
        price = coin['current_price']
        change = coin['price_change_percentage_24h'] or 0
        
        with st.container():
            st.subheader(f"{name} ({coin['symbol'].upper()})")
            
            # Fetch History
            df = fetch_long_history(c_id)
            
            # Create Plotly Chart
            fig = px.line(df, x='Date', y='Price', template="plotly_dark")
            
            # Add the Range Selector Buttons (Day, Week, Month, Year)
            fig.update_xaxes(
                rangeslider_visible=False,
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1D", step="day", stepmode="backward"),
                        dict(count=7, label="7D", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all", label="MAX")
                    ]),
                    bgcolor="#1E1E1E",
                    font=dict(color="white")
                ),
                showgrid=False
            )
            
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis_title=None,
                xaxis_title=None,
                hovermode="x unified"
            )
            
            # Display metrics and chart
            st.metric("Current Price", f"£{price:,.2f}", f"{change:.2f}%")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.write(f"**Value Owned:** £{price * MY_PORTFOLIO[c_id]:,.2f}")
            st.divider()

except Exception:
    st.info("Syncing with markets...")
