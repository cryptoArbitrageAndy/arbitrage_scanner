import ccxt
import pandas as pd
import time
import os
import logging
from datetime import datetime
from .config import EXCHANGES, SYMBOLS, MIN_DIFF, FEE_RATE, REFRESH_SEC

# === LOGGING ===
# Configure logging level from env var to avoid INFO noise on Render
# Set LOG_LEVEL=INFO locally for debugging, or leave unset / set to WARNING/ERROR in production.
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()
_numeric = getattr(logging, LOG_LEVEL, logging.WARNING)
logging.basicConfig(level=_numeric, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Optionally reduce verbosity of noisy third-party loggers (adjust as needed)
for _name in ('urllib3', 'asyncio', 'ccxt', 'streamlit'):
    logging.getLogger(_name).setLevel(_numeric)

# === INITIALIZE EXCHANGES ===
exchanges = {}
for name in EXCHANGES:
    try:
        exchange_class = getattr(ccxt, name)
        init_kwargs = {
            'enableRateLimit': True,
            'timeout': 10000,
        }
        # Ensure Huobi uses spot API (avoids hbdm.com swap endpoints)
        if name.lower() in ('huobi', 'huobipro'):
            init_kwargs.setdefault('options', {})
            init_kwargs['options']['defaultType'] = 'spot'
        exchanges[name] = exchange_class(init_kwargs)
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
            normalized = symbol.replace('/', '-')  # e.g., BTC/USD -> BTC-USD
        elif exchange_name == 'kraken':
            # Kraken uses XXBTZUSD for BTC/USD, XETHZUSD for ETH/USD
            base = symbol.split('/')[0]
            quote = symbol.split('/')[1]
            if base == 'BTC':
                normalized = 'XXBTZUSD' if quote == 'USD' else 'XBTUSDT'
            elif base == 'ETH':
                normalized = 'XETHZUSD' if quote == 'USD' else 'ETHUSDT'
            elif base == 'LTC':
                normalized = 'XLTCZUSD' if quote == 'USD' else 'LTCUSDT'
            elif base == 'ADA':
                normalized = 'ADAUSD' if quote == 'USD' else 'ADAUSDT'
            elif base == 'DOGE':
                 normalized = 'DOGEUSD' if quote == 'USD' else 'DOGE/USDT'
            elif base == 'SOL':
                normalized = 'SOLUSD' if quote == 'USD' else 'SOLUSDT'
            elif base == 'XRP':
                normalized = 'XXRPZUSD' if quote == 'USD' else 'XRPUSDT'
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
                f'Profit (after fees {FEE_RATE*100:.2f}%)': f"{profit:.2f}%",
                'Time': datetime.now().strftime("%H:%M:%S")
            })
            logger.info(f"💰 Found arbitrage: {symbol} - {profit:.2f}% profit")

    if results:
        logger.info(f"✅ Scan complete. Found {len(results)} opportunity(ies).")
    else:
        logger.info(f"⏳ Scan complete. No profitable opportunities found.")
    
    return pd.DataFrame(results) if results else pd.DataFrame()


def get_all_prices_df() -> pd.DataFrame:
    """Returns a clean matrix: Pair | Binance | Kraken | Coinbase"""
    from config import SYMBOLS, EXCHANGES
    data = {"Pair": SYMBOLS}
    for name, exchange in exchanges.items():
        prices = []
        for symbol in SYMBOLS:
            bid, ask = fetch_price(exchange, symbol, name)
            mid = (bid + ask) / 2 if bid and ask else None
            prices.append(mid)
        data[name.upper()] = prices
    df = pd.DataFrame(data)
    return df