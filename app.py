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

# ────────────────────────────── Page & Theme ──────────────────────────────
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")

st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem;}
    .css-1y0t9cy {background-color: #0e1117; color: #fafafa;}
    .stMetric {background: #1a1c2c; padding: 12px; border-radius: 12px; border-left: 5px solid #6c5ce7;}
    h1 {color: #6c5ce7; text-align: center; font-size: 3rem; margin-bottom: 0;}
    .stDataFrame {border: 1px solid #2d2d44; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# Header
st.title("Live Crypto Arbitrage Scanner")
st.markdown("##### Binance • Kraken • Coinbase Pro • Real-time • Zero Downtime")

with st.expander("Disclaimer", expanded=False):
    st.markdown("• Not financial advice • Opportunities vanish instantly • Use at your own risk")

# Placeholders
price_ph = st.empty()
arbitrage_ph = st.empty()
status_ph = st.empty()
countdown_ph = st.empty()

# ────────────────────────────── Main Loop (Zero Downtime) ──────────────────────────────
while True:
    price_matrix_df = get_all_prices_df()
    arbitrage_df = find_arbitrage()

    # ── 1. Price Matrix (Green = highest, Red = lowest) ──
    with price_ph.container():
        st.subheader("Live Price Matrix")
        if not price_matrix_df.empty:
            def highlight_prices(styler):
                df = styler.data.iloc[:, 1:]  # Exclude "Pair" column
                styled = styler
                for col in df.columns:
                    max_val = df[col].max()
                    min_val = df[col].min()
                    styled = styled.map(
                        lambda x: "color: #00ff9d; font-weight: bold;" if pd.notna(x) and x == max_val else
                                  "color: #ff3b5c; font-weight: bold;" if pd.notna(x) and x == min_val else "",
                        subset=(slice(None), col)
                    )
                return styled.format("${:,.2f}", subset=df.columns, na_rep="—")

            st.dataframe(highlight_prices(price_matrix_df.style))
        else:
            st.info("Loading prices...")

    # ── 2. Arbitrage Table (Green glowing rows when profitable) ──
    with arbitrage_ph.container():
        st.subheader("Arbitrage Opportunities (>1% profit after fees)")
        if not arbitrage_df.empty:
            def highlight_profit_rows(df):
                # Return list of CSS styles for each row
                return pd.DataFrame([
                    ["background-color: rgba(0,255,157,0.15)"] * len(df.columns)
                    if "Profit (after fees)" in row and float(str(row["Profit (after fees)"]).replace("%","").strip()) > 0
                    else [""] * len(df.columns)
                    for _, row in df.iterrows()
                ], index=df.index, columns=df.columns)

            styled_arbitrage = (
                arbitrage_df.style
                .apply(highlight_profit_rows, axis=None)
                .format({
                    "Spread": "{:.2f}%",
                    "Profit (after fees)": "{:.2f}%"
                })
            )
            st.dataframe(styled_arbitrage)
            st.success(f"{len(arbitrage_df)} active arbitrage(s) right now!")
        else:
            st.info("No profitable arbitrage at the moment – scanner is running!")

    # ── 3. Status & Countdown ──
    status_ph.markdown(f"**Last update:** {datetime.now().strftime('%H:%M:%S')} UTC")

    for secs in range(REFRESH_SEC, 0, -1):
        countdown_ph.metric("Next refresh in", f"{secs}s")
        time.sleep(1)

    st.rerun()