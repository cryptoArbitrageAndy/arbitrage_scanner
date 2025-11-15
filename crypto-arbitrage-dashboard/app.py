import streamlit as st
import pandas as pd
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

placeholder = st.empty()
status = st.empty()

while True:
    with placeholder.container():
        df = find_arbitrage()
        if not df.empty:
            st.success(f"{len(df)} arbitrage opportunity(ies) found!")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No profitable opportunities right now. Waiting for refresh...")

    status.write(f"Last scan: {pd.Timestamp.now().strftime('%b %d, %Y %H:%M:%S')} UTC")
    time.sleep(15)