# app.py
import streamlit as st
import time
from datetime import datetime
import sys
import os

# Add src folder
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.arbitrage_scanner import find_arbitrage
from src.config import REFRESH_SEC

# ─────────────────────────────────────────────────────────────
# Cached data fetch – this runs in background automatically
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_SEC, show_spinner=False)
def get_latest_arbitrage_data(_timestamp):
    """The _timestamp forces re-run every refresh"""
    return find_arbitrage()


# ─────────────────────────────────────────────────────────────
# Page config & UI
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")

st.title("Live Crypto Arbitrage Scanner")
st.caption("Binance • Kraken • Coinbase • Instant updates • Zero downtime")

with st.expander("Disclaimer – Please read", expanded=True):
    st.markdown(
        """
        - This is **not financial advice**  
        - Opportunities can disappear in seconds  
        - Fees & slippage are estimates  
        - Use at your own risk
        """
    )

# Placeholders (never cleared)
data_placeholder = st.empty()
status_placeholder = st.empty()
countdown_placeholder = st.empty()

# ─────────────────────────────────────────────────────────────
# Main refresh loop (non-blocking, production-proof)
# ─────────────────────────────────────────────────────────────
while True:
    # 1. Trigger cached background fetch (runs parallel)
    current_data = get_latest_arbitrage_data(datetime.now())

    # 2. Instantly display the fresh data
    with data_placeholder.container():
        if not current_data.empty:
            st.success(f"{len(current_data)} arbitrage opportunity(ies) found!")
            st.dataframe(current_data, width='stretch')
        else:
            st.info("No profitable opportunities right now – scanning continues...")

    # 3. Status line
    status_placeholder.write(
        f"Last update: {datetime.now().strftime('%b %d, %Y %H:%M:%S')} UTC"
    )

    # 4. Smooth countdown (15 → 1)
    for remaining in range(REFRESH_SEC, 0, -1):
        countdown_placeholder.metric("Next refresh in", f"{remaining}s")
        time.sleep(1)

    # 5. Trigger next cycle → instant rerun
    st.rerun()