import pytest
from src.arbitrage_scanner import find_arbitrage
from unittest.mock import patch

# Sample data for testing
mock_prices = {
    'binance': 50000,
    'kraken': 49500,
    'coinbase': 50500
}

def test_find_arbitrage():
    with patch('src.arbitrage_scanner.fetch_price') as mock_fetch:
        mock_fetch.side_effect = [
            (49000, 49500),  # Binance
            (48000, 49000),  # Kraken
            (50000, 50500)   # coinbase
        ]
        
        result = find_arbitrage()
        assert not result.empty
        assert len(result) == 1
        assert result['Pair'].iloc[0] == 'BTC/USDT'
        assert 'Buy' in result.columns
        assert 'Sell' in result.columns
        assert 'Spread' in result.columns
        assert 'Profit (after fees)' in result.columns

def test_no_arbitrage():
    with patch('src.arbitrage_scanner.fetch_price') as mock_fetch:
        mock_fetch.side_effect = [
            (50000, 50500),  # Binance
            (50000, 50500),  # Kraken
            (50000, 50500)   # coinbase
        ]
        
        result = find_arbitrage()
        assert result.empty