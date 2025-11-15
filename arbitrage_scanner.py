# arbitrage_scanner.py
import ccxt
import streamlit as st
import pandas as pd
import time
from datetime import datetime

# === CONFIG ===
EXCHANGES = ['binance', 'kraken', 'coinbasepro']
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
MIN_DIFF = 1.0  # Minimum profit % to show
FEE_RATE = 0.002  # 0.2% per trade (conservative)
REFRESH_SEC = 15

# === INITIALIZE EXCHANGES ===
exchanges = {}
for name in EXCHANGES:
    exchange_class = getattr(ccxt, name)
    exchanges[name] = exchange_class({
        'enableRateLimit': True,
        'timeout': 10000,
    })

# === FETCH PRICE ===
def fetch_price(exchange, symbol, exchange_name):
    try:
        # Adjust symbol format per exchange
        if exchange_name == 'kraken':
            symbol = symbol.replace('USDT', 'USD').replace('/', '')
        elif exchange_name == 'coinbasepro':
            symbol = symbol.replace('USDT', 'USD')
        ticker = exchange.fetch_ticker(symbol)
        return ticker['bid'], ticker['ask']
    except Exception as e:
        return None, None

# === FIND ARBITRAGE ===
def find_arbitrage():
    results = []
    for symbol in SYMBOLS:
        prices = {}
        for name, exchange in exchanges.items():
            bid, ask = fetch_price(exchange, symbol, name)
            if bid and ask:
                mid_price = (bid + ask) / 2
                prices[name] = mid_price

        if len(prices) < 2:
            continue

        max_price = max(prices.values())
        min_price = min(prices.values())
        diff_pct = (max_price - min_price) / min_price * 100
        profit = diff_pct - (FEE_RATE * 2 * 100)

        if profit > MIN_DIFF:
            buy_ex = min(prices, key=prices.get)
            sell_ex = max(prices, key=prices.get)
            results.append({
                'Pair': symbol,
                'Buy': f"{buy_ex.upper()} @ ${prices[buy_ex]:,.2f}",
                'Sell': f"{sell_ex.upper()} @ ${prices[sell_ex]:,.2f}",
                'Spread': f"{diff_pct:.2f}%",
                'Profit (after fees)': f"{profit:.2f}%",
                'Time': datetime.now().strftime("%H:%M:%S")
            })

    return pd.DataFrame(results) if results else pd.DataFrame()

# === STREAMLIT UI (ENGLISH) ===
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.title("Live Crypto Arbitrage Scanner")
st.caption("Binance • Kraken • Coinbase • Updates every 15s | Not financial advice")

with st.expander("Important Disclaimer", expanded=True):
    st.markdown("""
    - This is **not financial advice**.
    - Arbitrage opportunities may **disappear in seconds**.
    - Fees, slippage & latency are **estimates**.
    - Use at your own risk.
    """)

placeholder = st.empty()
status = st.empty()

while True:
    with placeholder.container():
        df = find_arbitrage()
        if not df.empty:
            st.success(f"{len(df)} arbitrage opportunity(ies) found!")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No profitable opportunities right now. Waiting for refresh...")
    
    status.write(f"Last scan: {datetime.now().strftime('%b %d, %Y %H:%M:%S')} UTC")
    time.sleep(REFRESH_SEC)