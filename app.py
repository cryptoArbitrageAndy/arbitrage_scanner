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
    h1 {color: #6c5ce7; text-align: center; font-size: 3rem;}
</style>
""", unsafe_allow_html=True)

st.title("Live Crypto Arbitrage Scanner")
st.markdown("##### Real-time • Zero Downtime")

with st.expander("Disclaimer", expanded=False):
    st.markdown("• Not financial advice • Opportunities vanish instantly • Use at your own risk")

# Placeholders (order = what user sees first)
arbitrage_ph = st.empty()      # ← Now FIRST
price_ph = st.empty()          # ← Now SECOND
status_ph = st.empty()
countdown_ph = st.empty()

# ────────────────────────────── Main Loop ──────────────────────────────
while True:
    price_matrix_df = get_all_prices_df()
    arbitrage_df = find_arbitrage()

    # ── 1. ARBITRAGE TABLE FIRST (most important) ──
    with arbitrage_ph.container():
        st.subheader("Arbitrage Opportunities (>1% profit after fees)")
        if not arbitrage_df.empty:
            df = arbitrage_df.copy()
            profit_col = "Profit (after fees)"
            if profit_col in df.columns:
                df[profit_col] = pd.to_numeric(
                    df[profit_col].astype(str).str.replace("%", "").str.strip(),
                    errors="coerce"
                )
            if "Spread" in df.columns:
                df["Spread"] = pd.to_numeric(df["Spread"].astype(str).str.replace("%", ""), errors="coerce")

            def highlight_profit(df_in):
                return pd.DataFrame(
                    ["background-color: rgba(0,255,157,0.15)" if v > 0 else "" for v in df_in[profit_col]],
                    index=df_in.index, columns=[profit_col]
                ).reindex(columns=df_in.columns, fill_value="")

            format_dict = {}
            if "Spread" in df.columns and pd.api.types.is_numeric_dtype(df["Spread"]):
                format_dict["Spread"] = "{:.2f}%"
            if profit_col in df.columns and pd.api.types.is_numeric_dtype(df[profit_col]):
                format_dict[profit_col] = "{:.2f}%"

            styled = df.style.apply(highlight_profit, axis=None).format(format_dict, na_rep="—")
            st.dataframe(styled)
            st.success(f"{len(df)} active arbitrage(s) right now!")
        else:
            st.info("No profitable arbitrage at the moment – scanner is running!")

    # ── 2. PRICE MATRIX SECOND ──
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

    # ── Status & Countdown ──
    status_ph.markdown(f"**Last update:** {datetime.now().strftime('%H:%M:%S')} UTC")

    for secs in range(REFRESH_SEC, 0, -1):
        countdown_ph.metric("Next refresh in", f"{secs}s")
        time.sleep(1)

    st.rerun()