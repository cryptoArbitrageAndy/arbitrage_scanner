import streamlit as st
import pandas as pd
import time
from src.arbitrage_scanner import find_arbitrage

# === STREAMLIT UI ===
st.set_page_config(page_title="Crypto Arbitrage Dashboard", layout="wide")
st.title("Crypto Arbitrage Dashboard")
st.caption("Visualize arbitrage opportunities across multiple exchanges.")

with st.expander("Important Disclaimer", expanded=True):
    st.markdown("""
    - This is **not financial advice**.
    - Arbitrage opportunities may **disappear in seconds**.
    - Fees, slippage & latency are **estimates**.
    - Use at your own risk.
    """)

df = find_arbitrage()

if not df.empty:
    st.success(f"✅ {len(df)} arbitrage opportunity(ies) found!")
    st.dataframe(df, use_container_width=True)
else:
    st.info("⏳ No profitable opportunities right now...")

col1, col2 = st.columns([2, 1])
with col1:
    st.write(f"**Last scan:** {pd.Timestamp.now().strftime('%b %d, %Y %H:%M:%S')} UTC")

with col2:
    countdown_placeholder = st.empty()

# Countdown loop
for i in range(30, 0, -1):
    countdown_placeholder.metric("Next refresh in", f"{i}s")
    time.sleep(1)

st.rerun()