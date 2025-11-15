import ccxt
import pandas as pd
import time
import logging
from datetime import datetime
from .config import EXCHANGES, SYMBOLS, MIN_DIFF, FEE_RATE, REFRESH_SEC

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === INITIALIZE EXCHANGES ===
exchanges = {}
for name in EXCHANGES:
    try:
        exchange_class = getattr(ccxt, name)
        exchanges[name] = exchange_class({
            'enableRateLimit': True,
            'timeout': 10000,
        })
        logger.info(f"✅ {name} initialized")
    except Exception as e:
        logger.error(f"❌ Failed to init {name}: {e}")

# === VALIDATE SYMBOLS ===
def get_supported_symbols(exchange, exchange_name):
    """Fetch supported symbols for an exchange"""
    try:
        exchange.load_markets()
        symbols = list(exchange.symbols)
        logger.debug(f"{exchange_name} supports {len(symbols)} pairs")
        return symbols
    except Exception as e:
        logger.error(f"Failed to load markets for {exchange_name}: {e}")
        return []

# === FETCH PRICE ===
def fetch_price(exchange, symbol, exchange_name):
    try:
        # Normalize symbol per exchange
        if exchange_name == 'kraken':
            normalized = symbol.replace('USDT', 'USD').replace('/', '')
        elif exchange_name == 'coinbase':
            normalized = symbol.replace('USDT', 'USD')
        elif exchange_name in ['huobi', 'okx', 'bybit']:
            normalized = symbol.lower()
        else:
            normalized = symbol
        
        ticker = exchange.fetch_ticker(normalized)
        bid, ask = ticker['bid'], ticker['ask']
        logger.debug(f"{exchange_name} {normalized}: bid={bid}, ask={ask}")
        return bid, ask
    except Exception as e:
        logger.debug(f"⚠️  {exchange_name} {symbol}: {str(e)[:50]}")
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
            logger.info(f"⚠️  {symbol}: Only {len(prices)} exchange(s) available")
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
            logger.info(f"✅ Arbitrage found: {symbol} ({profit:.2f}%)")

    return pd.DataFrame(results) if results else pd.DataFrame()