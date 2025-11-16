# config.py
EXCHANGES = ['binance', 'kraken', 
             'coinbase', 'okx', 
             'bybit']
SYMBOLS = [
    'BTC/USDT', 
    'ETH/USDT', 'SOL/USDT',
    'XRP/USDT', 'ADA/USDT', 'DOGE/USDT',
]
MIN_DIFF = 0.05  # Increased threshold (more exchanges = more noise)
FEE_RATE = 0.002  # 0.2% per trade
REFRESH_SEC = 30