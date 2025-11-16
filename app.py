import streamlit as st
import pandas as pd
import time
from src.arbitrage_scanner import find_arbitrage, exchanges, SYMBOLS

st.set_page_config(page_title="Crypto Arbitrage Dashboard", layout="wide")
st.markdown("""
    <style>
    .arbitrage-row {background-color: #ffe082 !important;}
    .dataframe th, .dataframe td {font-size: 1.1em;}
    .stDataFrame {background: #f8fafc;}
    .main {background-color: #f4f6fa;}
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Crypto Arbitrage Dashboard")
st.caption("Visualize arbitrage opportunities and live prices across multiple exchanges.")

# --- Fetch data ---
arbitrage_df = find_arbitrage()

# --- Always show most profitable trade per symbol ---
def get_best_opportunity_per_symbol(arbitrage_df):
    if arbitrage_df.empty:
        return pd.DataFrame()
    # Ensure 'Pair' and 'Profit (after fees)' columns exist
    arbitrage_df['Profit (after fees)'] = arbitrage_df['Profit (after fees)'].str.rstrip('%').astype(float)
    best_trades = arbitrage_df.sort_values('Profit (after fees)', ascending=False).groupby('Pair').head(1)
    # Restore formatting
    best_trades['Profit (after fees)'] = best_trades['Profit (after fees)'].map(lambda x: f"{x:.2f}%")
    return best_trades

best_arbs_df = get_best_opportunity_per_symbol(arbitrage_df)

# --- Fetch all recent prices ---
def get_all_prices():
    rows = []
    for symbol in SYMBOLS:
        row = {"Pair": symbol}
        for ex_name, ex in exchanges.items():
            try:
                bid, ask = ex.fetch_ticker(symbol.replace('/', '') if ex_name == 'binance' else symbol)['bid'], \
                           ex.fetch_ticker(symbol.replace('/', '') if ex_name == 'binance' else symbol)['ask']
                if bid and ask:
                    row[ex_name.upper()] = f"${(bid + ask) / 2:,.2f}"
                else:
                    row[ex_name.upper()] = "-"
            except Exception:
                row[ex_name.upper()] = "-"
        rows.append(row)
    return pd.DataFrame(rows)

prices_df = get_all_prices()

# --- Arbitrage Table ---
st.markdown("### 🏆 **Most Profitable Trades Per Pair**")
if not best_arbs_df.empty:
    st.dataframe(
        best_arbs_df.style.apply(
            lambda x: ['background-color: #ffe082' for _ in x], axis=1
        ),
        width='stretch',
        hide_index=True
    )
else:
    st.info("⏳ No opportunities found for any pair right now...")

# --- Prices Table ---
st.markdown("### 💹 **Recent Prices Across Exchanges**")

# Place last scan and next refresh here
last_scan = pd.Timestamp.now().strftime('%b %d, %Y %H:%M:%S')
col1, col2 = st.columns([2, 1])
with col1:
    st.write(f"**Last scan:** {last_scan} UTC")
with col2:
    countdown_placeholder = st.empty()

st.dataframe(prices_df, width='stretch', hide_index=True)

# --- Disclaimer at the bottom ---
with st.expander("Important Disclaimer", expanded=False):
    st.markdown("""
    - This is **not financial advice**.
    - Arbitrage opportunities may **disappear in seconds**.
    - Fees, slippage & latency are **estimates**.
    - Use at your own risk.
    """)

# --- Countdown ---
for i in range(30, 0, -1):
    countdown_placeholder.metric("Next refresh in", f"{i}s")
    time.sleep(1)

st.rerun()