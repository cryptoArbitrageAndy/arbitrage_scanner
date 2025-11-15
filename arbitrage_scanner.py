# arbitrage_scanner.py
import ccxt
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import telegram  # pip install python-telegram-bot

# === CONFIG ===
EXCHANGES = ['binance', 'kraken', 'coinbasepro']
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
MIN_DIFF = 1.0  # % für Anzeige
FEE_RATE = 0.002  # 0.2% pro Trade (konservativ)
REFRESH_SEC = 15

# === INIT EXCHANGES ===
exchanges = {}
for name in EXCHANGES:
    exchange_class = getattr(ccxt, name)
    exchanges[name] = exchange_class({
        'enableRateLimit': True,
    })

# === TELEGRAM (optional) ===
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", None)
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", None)
bot = telegram.Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

def send_alert(text):
    if bot and TELEGRAM_CHAT_ID:
        try:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        except:
            pass

def fetch_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['bid'], ticker['ask']
    except:
        return None, None

def find_arbitrage():
    results = []
    for symbol in SYMBOLS:
        prices = {}
        for name, exchange in exchanges.items():
            bid, ask = fetch_price(exchange, symbol.replace('/', ''))
            if bid and ask:
                prices[name] = (bid + ask) / 2  # Mid-Price
        if len(prices) < 2:
            continue

        max_price = max(prices.values())
        min_price = min(prices.values())
        diff_pct = (max_price - min_price) / min_price * 100
        profit_after_fees = diff_pct - (FEE_RATE * 2 * 100)

        if profit_after_fees > MIN_DIFF:
            buy_ex = min(prices, key=prices.get)
            sell_ex = max(prices, key=prices.get)
            results.append({
                'Pair': symbol,
                'Buy': f"{buy_ex.upper()} @ ${prices[buy_ex]:,.2f}",
                'Sell': f"{sell_ex.upper()} @ ${prices[sell_ex]:,.2f}",
                'Diff %': f"{diff_pct:.2f}%",
                'Profit (after fees)': f"{profit_after_fees:.2f}%",
                'Time': datetime.now().strftime("%H:%M:%S")
            })

            # Alert
            alert = f"ARBITRAGE: {symbol}\nBuy {buy_ex.upper()} @ ${prices[buy_ex]:,.0f}\nSell {sell_ex.upper()} @ ${prices[sell_ex]:,.0f}\nProfit: {profit_after_fees:.2f}%"
            send_alert(alert)

    return pd.DataFrame(results)

# === STREAMLIT UI ===
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.title("Live Crypto Arbitrage Scanner")
st.caption("Scanne Binance, Kraken, Coinbase • Aktualisierung alle 15s")

placeholder = st.empty()
status = st.empty()

while True:
    with placeholder.container():
        df = find_arbitrage()
        if not df.empty:
            st.success(f"{len(df)} Arbitrage-Gelegenheit(en) gefunden!")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Keine profitablen Gelegenheiten gerade. Warte auf Refresh...")
    
    status.write(f"Letzter Scan: {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(REFRESH_SEC)