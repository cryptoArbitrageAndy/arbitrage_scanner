# config.py
EXCHANGES = ['binance', 'kraken', 'coinbase', 'huobi', 'okx', 'bybit']
SYMBOLS = [
    # Major pairs
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT',
    # Alt coins (higher volatility)
    'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'MATIC/USDT', 'LINK/USDT',
    'AVAX/USDT', 'ARB/USDT', 'OP/USDT',
    # Fiat pairs
    'BTC/USD', 'ETH/EUR'
]
MIN_DIFF = 0.05  # Increased threshold (more exchanges = more noise)
FEE_RATE = 0.002  # 0.2% per trade
REFRESH_SEC = 15