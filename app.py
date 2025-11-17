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

# ────────────────────────────── Main Loop ──────────────────────────────
while True:
    price_matrix_df = get_all_prices_df()
    arbitrage_df = find_arbitrage()

    # ── 1. Arbitrage Table (Glowing green rows when profitable) ──
    with arbitrage_ph.container():
        st.subheader("Arbitrage Opportunities (>1% profit after fees)")
        if not arbitrage_df.empty:
            # CRITICAL FIX: Convert only numeric columns to proper types BEFORE styling
            df = arbitrage_df.copy()
            if "Profit (after fees)" in df.columns:
                df["Profit (after fees)"] = pd.to_numeric(
                    df["Profit (after fees)"].astype(str).str.replace("%", "").str.strip(),
                    errors="coerce"
                )
            if "Spread" in df.columns:
                df["Spread"] = pd.to_numeric(df["Spread"].astype(str).str.replace("%", ""), errors="coerce")

            # Highlight profitable rows
            def highlight_profit(df_in):
                return pd.DataFrame(
                    ["background-color: rgba(0,255,157,0.15)" if v > 0 else "" for v in df_in["Profit (after fees)"]],
                    index=df_in.index, columns=["Profit (after fees)"]
                ).reindex(columns=df_in.columns, fill_value="")

            # Only format columns that are actually numeric
            format_dict = {}
            if "Spread" in df.columns and pd.api.types.is_numeric_dtype(df["Spread"]):
                format_dict["Spread"] = "{:.2f}%"
            if "Profit (after fees)" in df.columns and pd.api.types.is_numeric_dtype(df["Profit (after fees)"]):
                format_dict["Profit (after fees)"] = "{:.2f}%"

            styled = (
                df.style
                .apply(highlight_profit, axis=None)
                .format(format_dict, na_rep="—")
            )
            st.dataframe(styled)
            st.success(f"{len(df)} active arbitrage(s) right now!")
        else:
            st.info("No profitable arbitrage – scanner running!")

    # ── 2. Price Matrix (Green = highest, Red = lowest) ──
    with price_ph.container():
        st.subheader("Live Price Matrix")
        if not price_matrix_df.empty:
            def highlight_extremes(styler):
                df = styler.data
                numeric_cols = df.select_dtypes(include='number').columns
                styled = styler
                for col in numeric_cols:
                    max_val = df[col].max()
                    min_val = df[col].min()
                    styled = styled.map(
                        lambda x: "color: #00ff9d; font-weight: bold;" if pd.notna(x) and x == max_val else
                                  "color: #ff3b5c; font-weight: bold;" if pd.notna(x) and x == min_val else "",
                        subset=(slice(None), col)
                    )
                return styled.format({col: "${:,.2f}" for col in numeric_cols}, na_rep="—")

            st.dataframe(highlight_extremes(price_matrix_df.style))
        else:
            st.info("Loading prices...")    

    # ── 3. Status & Countdown ──
    status_ph.markdown(f"**Last update:** {datetime.now().strftime('%H:%M:%S')} UTC")

    for secs in range(REFRESH_SEC, 0, -1):
        countdown_ph.metric("Next refresh in", f"{secs}s")
        time.sleep(1)

    st.rerun()