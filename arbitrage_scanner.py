# arbitrage_scanner.py
import ccxt
import streamlit as st
import pandas as pd
import time
from datetime import datetime

# === KONFIGURATION ===
EXCHANGES = ['binance', 'kraken', 'coinbasepro']
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
MIN_DIFF = 1.0  # Mindest-Differenz in %
FEE_RATE = 0.002  # 0.2% Gebühr pro Trade
REFRESH_SEC = 15

# === EXCHANGES INITIALISIEREN ===
exchanges = {}
for name in EXCHANGES:
    exchange_class = getattr(ccxt, name)
    exchanges[name] = exchange_class({
        'enableRateLimit': True,
        'timeout': 10000,
    })

# === PREIS HOLEN ===
def fetch_price(exchange, symbol):
    try:
        # Symbol anpassen (z.B. BTC/USDT → BTC/USDT:USDT für Kraken)
        try:
            ticker = exchange.fetch_ticker(symbol)
        except:
            # Kraken/Coinbase brauchen oft anderes Format
            alt_symbol = symbol.replace('/', '-') if name in ['kraken', 'coinbasepro'] else symbol
            ticker = exchange.fetch_ticker(alt_symbol)
        return ticker['bid'], ticker['ask']
    except Exception as e:
        st.warning(f"{name}: {symbol} nicht verfügbar")
        return None, None

# === ARBITRAGE FINDEN ===
def find_arbitrage():
    results = []
    for symbol in SYMBOLS:
        prices = {}
        for name, exchange in exchanges.items():
            bid, ask = fetch_price(exchange, symbol)
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
                'Kaufen': f"{buy_ex.upper()} @ ${prices[buy_ex]:,.2f}",
                'Verkaufen': f"{sell_ex.upper()} @ ${prices[sell_ex]:,.2f}",
                'Differenz': f"{diff_pct:.2f}%",
                'Gewinn (nach Gebühren)': f"{profit:.2f}%",
                'Zeit': datetime.now().strftime("%H:%M:%S")
            })

    return pd.DataFrame(results) if results else pd.DataFrame()

# === STREAMLIT UI ===
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.title("Live Crypto Arbitrage Scanner")
st.caption("Binance • Kraken • Coinbase • Aktualisierung alle 15s | Nicht als Handelsempfehlung")

with st.expander("Wichtige Hinweise", expanded=True):
    st.markdown("""
    - Dies ist **keine Finanzberatung**.
    - Arbitrage-Chancen können **in Sekunden verschwinden**.
    - Gebühren, Slippage & Latenz sind **nicht live berechnet**.
    - Nutzung auf eigene Gefahr.
    """)

placeholder = st.empty()
status = st.empty()

# Auto-Refresh
while True:
    with placeholder.container():
        df = find_arbitrage()
        if not df.empty:
            st.success(f"{len(df)} Arbitrage-Chance(n) gefunden!")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Keine profitablen Chancen im Moment. Warte auf Refresh...")
    
    status.write(f"Letzter Scan: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    time.sleep(REFRESH_SEC)