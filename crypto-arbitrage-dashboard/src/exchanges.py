import ccxt

def initialize_exchanges(exchange_names):
    exchanges = {}
    for name in exchange_names:
        exchange_class = getattr(ccxt, name)
        exchanges[name] = exchange_class({
            'enableRateLimit': True,
            'timeout': 10000,
        })
    return exchanges

def fetch_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['bid'], ticker['ask']
    except Exception as e:
        return None, None