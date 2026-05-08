import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Crypto Grid (£)", layout="wide")

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
def fetch_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=365&interval=daily"
    res = requests.get(url).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

st.title("📊 Crypto Grid (£)")

try:
    data = fetch_prices()
    total_val = sum(c['current_price'] * MY_PORTFOLIO[c['id']] for c in data)
    st.sidebar.metric("Total Balance", f"£{total_val:,.2f}")

    # Process data in chunks of 2 to create rows
    for i in range(0, len(data), 2):
        cols = st.columns(2) # Create 2 side-by-side columns
        
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    # Compact Header
                    st.markdown(f"**{coin['symbol'].upper()}** £{coin['current_price']:,}")
                    
                    # Chart Logic
                    df = fetch_history(coin['id'])
                    fig = px.line(df, x='Date', y='Price', template="plotly_dark")
                    
                    # Shrink chart for side-by-side view
                    fig.update_xaxes(
                        rangeslider_visible=False,
                        rangeselector=dict(
                            buttons=list([
                                dict(count=7, label="7D", step="day", stepmode="backward"),
                                dict(count=1, label="1M", step="month", stepmode="backward"),
                                dict(step="all", label="MAX")
                            ]),
                            font=dict(size=10) # Smaller font for small screen
                        )
                    )
                    fig.update_layout(
                        height=250, # Shorter height to fit 2-up
                        margin=dict(l=0, r=0, t=20, b=0),
                        yaxis_visible=False, # Hide Y axis to save space
                        xaxis_title=None
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

except Exception:
    st.info("Market data syncing...")
