import ccxt
import pandas as pd
import time
import logging
from datetime import datetime
from .config import EXCHANGES, SYMBOLS, MIN_DIFF, FEE_RATE, REFRESH_SEC

# === LOGGING ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

# === FETCH PRICE ===
def fetch_price(exchange, symbol, exchange_name):
    try:
        # Normalize symbol per exchange
        if exchange_name == 'binance':
            normalized = symbol.replace('/', '')
        elif exchange_name == 'coinbase':
            normalized = symbol.replace('/', '-')
        elif exchange_name == 'kraken':
            base = symbol.split('/')[0]
            quote = symbol.split('/')[1]
            if base == 'BTC':
                normalized = 'XXBTZUSD' if quote == 'USD' else 'XBTUSDT'
            elif base == 'ETH':
                normalized = 'XETHZUSD' if quote == 'USD' else 'ETHUSDT'
            else:
                normalized = symbol.replace('/', 'Z' if quote == 'USD' else '')
        elif exchange_name == 'okx':
            normalized = symbol.replace('/', '-')
        elif exchange_name == 'bybit':
            normalized = symbol.replace('/', '')
        elif exchange_name == 'huobi':
            normalized = symbol.replace('/', '').lower()
        else:
            normalized = symbol
        
        ticker = exchange.fetch_ticker(normalized)
        bid, ask = ticker['bid'], ticker['ask']
        return bid, ask
    except Exception as e:
        logger.error(f"❌ {exchange_name} {symbol}: {str(e)}")
        return None, None

# === FIND ARBITRAGE ===
def find_arbitrage():
    logger.info(f"🔍 Starting scan for {len(SYMBOLS)} symbols on {len(exchanges)} exchanges...")
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
            logger.info(f"💰 Found arbitrage: {symbol} - {profit:.2f}% profit")

    if results:
        logger.info(f"✅ Scan complete. Found {len(results)} opportunity(ies).")
    else:
        logger.info(f"⏳ Scan complete. No profitable opportunities found.")
    
    return pd.DataFrame(results) if results else pd.DataFrame()