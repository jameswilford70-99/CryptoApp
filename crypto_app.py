import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="Crypto Grid (£)", layout="wide")

# Custom CSS to make sure the borders are clearly visible
st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stVerticalBlock"]) {
        border-radius: 10px;
    }
    </style>
    """, unsafe_base_with_rows=True)

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
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=gbp&days=365&interval=daily"
    res = requests.get(url).json()
    df = pd.DataFrame(res.get('prices', []), columns=['Date', 'Price'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    return df

st.title("📊 Crypto Grid (£)")

try:
    data = fetch_prices()
    total_val = sum(c['current_price'] * MY_PORTFOLIO[c['id']] for c in data)
    
    # Header Info
    st.metric("Total Portfolio Balance", f"£{total_val:,.2f}")
    st.divider()

    # Process data in chunks of 2 for the grid
    for i in range(0, len(data), 2):
        cols = st.columns(2)
        
        for j in range(2):
            if i + j < len(data):
                coin = data[i + j]
                with cols[j]:
                    # The 'border=True' creates the white/grey box around the crypto
                    with st.container(border=True):
                        st.markdown(f"**{coin['name']}** ({coin['symbol'].upper()})")
                        
                        # Price and Change
                        price = coin['current_price']
                        change = coin['price_change_percentage_24h'] or 0
                        st.caption(f"Price: £{price:,.2f} ({change:+.2f}%)")
                        
                        # Chart
                        df = fetch_history(coin['id'])
                        fig = px.line(df, x='Date', y='Price', template="plotly_dark")
                        
                        fig.update_xaxes(
                            rangeslider_visible=False,
                            rangeselector=dict(
                                buttons=list([
                                    dict(count=7, label="7D", step="day", stepmode="backward"),
                                    dict(count=1, label="1M", step="month", stepmode="backward"),
                                    dict(step="all", label="MAX")
                                ]),
                                font=dict(size=9),
                                y=1.1 # Move buttons slightly up
                            )
                        )
                        
                        fig.update_layout(
                            height=200,
                            margin=dict(l=5, r=5, t=5, b=5),
                            yaxis_visible=False,
                            xaxis_title=None,
                            xaxis_visible=True # Show dates on the bottom
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Holding info at the bottom of the box
                        amt = MY_PORTFOLIO[coin['id']]
                        if amt > 0:
                            st.markdown(f"<small>Value: £{price * amt:,.2f}</small>", unsafe_allow_html=True)

except Exception as e:
    st.info("Awaiting market data... (CoinGecko API may be busy)")
