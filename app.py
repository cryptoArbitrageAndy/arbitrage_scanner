# app.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Add src folder
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.arbitrage_scanner import find_arbitrage, get_all_prices_df
from src.config import REFRESH_SEC

# ────────────────────────────── Page Config & Crypto Theme ──────────────────────────────
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")

st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem;}
    .css-1y0t9cy {background-color: #0e1117; color: #fafafa;}
    .stMetric {background: #1a1c2c; padding: 12px; border-radius: 12px; border-left: 5px solid #6c5ce7;}
    h1 {color: #6c5ce7; text-align: center; font-size: 3rem;}
    .stDataFrame {border: 1px solid #2d2d44; border-radius: 10px;}
    .profit-row {background-color: rgba(0, 255, 157, 0.15) !important;}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────── Title ──────────────────────────────
st.title("Live Crypto Arbitrage Scanner")
st.markdown("##### Binance • Kraken • Coinbase Pro • Real-time • Zero Downtime")

with st.expander("Disclaimer", expanded=False):
    st.markdown("• Not financial advice • Opportunities disappear instantly • Use at your own risk")

# Persistent placeholders
price_matrix_ph = st.empty()
arbitrage_ph = st.empty()
status_ph = st.empty()
countdown_ph = st.empty()

# ────────────────────────────── Main Loop (Zero Downtime) ──────────────────────────────
while True:
    # 1. Fetch fresh data
    price_matrix_df = get_all_prices_df()
    arbitrage_df = find_arbitrage()

    # 2. Live Price Matrix – highest = green, lowest = red
    with price_matrix_ph.container():
        st.subheader("Live Price Matrix")
        if not price_matrix_df.empty:
            def style_prices_row(row):
                # row is a Series for the entire row; first column is Pair (non-numeric)
                # compute styles for numeric columns only
                numeric = pd.to_numeric(row.iloc[1:], errors='coerce')
                maxv = numeric.max()
                minv = numeric.min()
                styles = []
                for v in numeric:
                    if pd.isna(v):
                        styles.append("")
                    elif v == maxv:
                        styles.append("color: #00ff9d; font-weight: bold;")   # Highest = green
                    elif v == minv:
                        styles.append("color: #ff3b5c; font-weight: bold;")   # Lowest = red
                    else:
                        styles.append("")
                # prepend empty style for the Pair column
                return [""] + styles

            styled_matrix = price_matrix_df.style.apply(
                style_prices_row,
                axis=1,
                subset=pd.IndexSlice[:, price_matrix_df.columns[1:]]
            ).format("${:,.2f}", na_rep="—")
            st.dataframe(styled_matrix, width='stretch')
        else:
            st.info("Loading price matrix...")

    # 3. Arbitrage Opportunities Table
    with arbitrage_ph.container():
        st.subheader("Arbitrage Opportunities (>1% profit after fees)")
        if not arbitrage_df.empty:
            def style_prices_row(row):
                # row is a Series for the entire row; first column is Pair (non-numeric)
                # compute styles for numeric columns only
                numeric = pd.to_numeric(row.iloc[1:], errors='coerce')
                maxv = numeric.max()
                minv = numeric.min()
                styles = []
                for v in numeric:
                    if pd.isna(v):
                        styles.append("")
                    elif v == maxv:
                        styles.append("color: #00ff9d; font-weight: bold;")   # Highest = green
                    elif v == minv:
                        styles.append("color: #ff3b5c; font-weight: bold;")   # Lowest = red
                    else:
                        styles.append("")
                # prepend empty style for the Pair column
                return [""] + styles

            styled_matrix = (
                price_matrix_df.style
                .apply(style_prices_row, axis=1)
                .format("${:,.2f}", na_rep="—")
            )
            st.dataframe(styled_matrix, width='stretch')
            st.success(f"{len(arbitrage_df)} active arbitrage(s) right now!")
        else:
            st.info("No profitable arbitrage at the moment – scanner is running!")

    # 4. Status + Countdown
    status_ph.markdown(f"**Last update:** {datetime.now().strftime('%H:%M:%S')} UTC")

    # Smooth countdown
    for secs in range(REFRESH_SEC, 0, -1):
        countdown_ph.metric("Next refresh in", f"{secs}s")
        time.sleep(1)

    # Instant rerun – old tables stay visible until new data is ready
    st.rerun()