import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="Crypto Grid (£)", layout="wide")

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
                    # The 'border=True' creates the clean box around the content
                    with st.container(border=True):
                        st.markdown(f"### {coin['name']} ({coin['symbol'].upper()})")
                        
                        # Price and Change
                        price = coin['current_price']
                        change = coin['price_change_percentage_24h'] or 0
                        
                        # Color coding the percentage change for better visibility
                        color = "green" if change >= 0 else "red"
                        st.markdown(f"**£{price:,.2f}** <span style='color:{color}'>({change:+.2f}%)</span>", unsafe_allow_html=True)
                        
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
                                font=dict(size=10, color="black"),
                                bgcolor="#eeeeee"
                            )
                        )
                        
                        fig.update_layout(
                            height=220,
                            margin=dict(l=10, r=10, t=10, b=10),
                            yaxis_visible=False,
                            xaxis_title=None,
                            xaxis_visible=True
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        # Holding info
                        amt = MY_PORTFOLIO[coin['id']]
                        if amt > 0:
                            st.write(f"Value Owned: **£{price * amt:,.2f}**")

except Exception as e:
    st.error(f"Market data syncing... Error: {e}")
