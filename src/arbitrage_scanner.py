import ccxt
import pandas as pd
import time
from datetime import datetime
from .config import EXCHANGES, SYMBOLS, MIN_DIFF, FEE_RATE, REFRESH_SEC

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
        # Normalize symbol per exchange
        if exchange_name == 'kraken':
            symbol = symbol.replace('USDT', 'USD').replace('/', '')
        elif exchange_name == 'coinbase':
            symbol = symbol.replace('USDT', 'USD')
        elif exchange_name in ['huobi', 'okx', 'bybit']:
            # These support standard format
            symbol = symbol.lower()
        
        ticker = exchange.fetch_ticker(symbol)
        return ticker['bid'], ticker['ask']
    except Exception as e:
        # Silently skip unsupported pairs
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