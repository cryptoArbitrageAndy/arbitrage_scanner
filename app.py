# app.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Add src
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.arbitrage_scanner import find_arbitrage, get_all_prices_df
from src.config import REFRESH_SEC

# ────────────────────────────── Page Config & Theme ──────────────────────────────
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")

# Custom CSS – pure crypto vibe
st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem; padding-bottom: 3rem;}
    .css-1y0t9cy {background-color: #0e1117; color: #fafafa;}
    .stMetric {background: #1a1c2c; padding: 10px; border-radius: 10px; border-left: 5px solid #6c5ce7;}
    .profit-positive {color: #00ff9d !important; font-weight: bold;}
    .profit-negative {color: #ff3b5c !important;}
    h1 {color: #6c5ce7; text-align: center;}
    .stDataFrame {border: 1px solid #2d2d44;}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────── Title & Disclaimer ──────────────────────────────
st.title("Live Crypto Arbitrage Scanner")
st.markdown("##### Binance • Kraken • Coinbase Pro • Real-time • Zero downtime")

with st.expander("Disclaimer – Click to read", expanded=False):
    st.markdown("""
    - Not financial advice • Opportunities vanish in seconds  
    - Fees & slippage are estimates • Use at your own risk
    """)

# Placeholders that never get cleared
price_matrix_placeholder = st.empty()
arbitrage_placeholder = st.empty()
status_placeholder = st.empty()
countdown_placeholder = st.empty()

# ────────────────────────────── Main Refresh Loop (Zero Downtime) ──────────────────────────────
while True:
    # 1. Get fresh data (cached + background)
    price_matrix_df = get_all_prices_df()           # ← New function (see below)
    arbitrage_df = find_arbitrage()                 # Your existing function

    # 2. Live Price Matrix (all exchanges, all pairs)
    with price_matrix_placeholder.container():
        st.subheader("Live Price Overview")
        if not price_matrix_df.empty:
            # Style the matrix
            def color_high_low(val):
                if pd.isna(val): return ""
                col = price_matrix_df.drop("Pair", axis=1).loc[price_matrix_df["Pair"] == val.name[0]]
                if col.empty: return ""
                numeric = col.select_dtypes(include='number').stack()
                if numeric.empty: return ""
                color = "color: #00ff9d;" if val == numeric.max() else ("color: #ff3b5c;" if val == numeric.min() else "")
                return color
            styled = price_matrix_df.style.applymap(color_high_low, subset=pd.IndexSlice[:, price_matrix_df.columns[1:]])
            st.dataframe(styled.format("${:,.2f}"), width='stretch')
        else:
            st.info("Loading price matrix...")

    # 3. Arbitrage Opportunities Table
    with arbitrage_placeholder.container():
        st.subheader("Arbitrage Opportunities (>1% profit after fees)")
        if not arbitrage_df.empty:
            # Highlight profit column
            def highlight_profit(row):
                return [''] * len(row) if row["Profit (after fees)"].replace("%","") < "0" else ['background: rgba(0,255,157,0.15)'] * len(row)
            styled_arbitrage = arbitrage_df.style.apply(highlight_profit, axis=1).format({
                "Spread": "{:.2f}%", "Profit (after fees)": "{:.2f}%"
            })
            st.dataframe(styled_arbitrage, use_container_width=True)
            st.success(f"{len(arbitrage_df)} active arbitrage(s) right now!")
        else:
            st.info("No profitable arbitrage at the moment – keep scanning!")

    # 4. Status + Countdown
    status_placeholder.markdown(
        f"**Last update:** {datetime.now().strftime('%H:%M:%S')} UTC | "
        f"**Next refresh in...**"
    )

    # Smooth countdown
    for secs in range(REFRESH_SEC, 0, -1):
        countdown_placeholder.metric("Refresh in", f"{secs}s")
        time.sleep(1)

    # Instant rerun – old data stays visible until new data is ready
    st.rerun()