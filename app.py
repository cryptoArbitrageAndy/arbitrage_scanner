# app.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.arbitrage_scanner import find_arbitrage, get_all_prices_df
from src.config import REFRESH_SEC

# ────────────────────────────── PAGE & DESIGN ──────────────────────────────
st.set_page_config(page_title="Arbitrage Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp {background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #e0e0ff; font-family: 'Inter', sans-serif;}
    .hero-title {
        font-size: 4.5rem; font-weight: 800; background: linear-gradient(90deg, #6c5ce7, #00cec9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center;
        margin-bottom: 0; text-shadow: 0 0 30px rgba(108,92,231,0.5);
    }
    .hero-subtitle {font-size: 1.6rem; text-align: center; opacity: 0.9; margin-top: 10px;}
    
    /* Top bar – no longer covering content */
    .top-bar {
        background: rgba(15,12,41,0.85); backdrop-filter: blur(12px);
        padding: 12px 20px; text-align: center; font-size: 1rem;
        border-bottom: 1px solid rgba(108,92,231,0.3);
        margin-bottom: 20px;
    }
    
    .glass-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid rgba(108,92,231,0.2);
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        margin-bottom: 24px;
    }
    
    /* Countdown orb – now clearly visible */
    .countdown-orb {
        width: 100px; height: 100px; border-radius: 50%;
        background: radial-gradient(circle, #6c5ce7, #0984e3);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-size: 2rem; font-weight: bold; color: white;
        box-shadow: 0 0 50px rgba(108,92,231,0.8);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {0%,100%{box-shadow:0 0 50px rgba(108,92,231,0.8)} 50%{box-shadow:0 0 70px rgba(108,92,231,1)}}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────── HEADER (always visible) ──────────────────────────────
last_update = datetime.now(timezone.utc).strftime("%H:%M:%S")
st.markdown("<h1 class='hero-title'>Arbitrage Pro</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>Real-time crypto arbitrage • Zero downtime • Studio-grade</p>", unsafe_allow_html=True)
st.markdown(f"""
<div class="top-bar">
    Live Arbitrage Scanner • <strong>Last update: {last_update} UTC</strong>
</div>
""", unsafe_allow_html=True)

# Placeholders for tables
arbitrage_ph = st.empty()
price_ph = st.empty()

# ────────────────────────────── MAIN LOOP ──────────────────────────────
while True:
    price_matrix_df = get_all_prices_df()
    arbitrage_df = find_arbitrage()

    # Update last-update in top bar (runs every cycle)
    current_time = datetime.now(timezone.utc).strftime("%H:%M:%S")
    st.markdown(f"""
    <script>
        document.querySelector('.top-bar strong').innerText = 'Last update: {current_time} UTC';
    </script>
    """, unsafe_allow_html=True)

    # ── 1. Arbitrage Table ──
    with arbitrage_ph.container():
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Live Arbitrage Opportunities")
        if not arbitrage_df.empty:
            df = arbitrage_df.copy()
            profit_col = "Profit (after fees)"
            if profit_col in df.columns:
                df[profit_col] = pd.to_numeric(df[profit_col].astype(str).str.replace("%","").str.strip(), errors="coerce")
            if "Spread" in df.columns:
                df["Spread"] = pd.to_numeric(df["Spread"].astype(str).str.replace("%",""), errors="coerce")

            def highlight_profit(df_in):
                return pd.DataFrame(
                    ['background-color: rgba(0,255,157,0.15); border-left: 5px solid #00ff9d;' 
                     if pd.notna(v) and v > 0 else '' for v in df_in[profit_col]],
                    index=df_in.index, columns=[profit_col]
                ).reindex(columns=df_in.columns, fill_value='')

            styled = df.style.apply(highlight_profit, axis=None).format({"Spread": "{:.2f}%", profit_col: "{:.2f}%"}, na_rep="—")
            st.dataframe(styled, width='stretch')
            st.success(f"{len(df)} profitable arbitrage(s) right now")
        else:
            st.info("No profitable arbitrage – scanning continues…")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 2. Price Matrix ──
    with price_ph.container():
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Live Price Matrix")
        if not price_matrix_df.empty:
            def highlight_extremes(styler):
                df = styler.data
                numeric_cols = df.select_dtypes('number').columns
                styled = styler
                for col in numeric_cols:
                    max_v = df[col].max()
                    min_v = df[col].min()
                    styled = styled.map(
                        lambda x: "color: #00ff9d; font-weight: bold;" if pd.notna(x) and x == max_v else
                                  "color: #ff3b5c; font-weight: bold;" if pd.notna(x) and x == min_v else "",
                        subset=(slice(None), col)
                    )
                return styled.format({c: "${:,.2f}" for c in numeric_cols}, na_rep="—")
            st.dataframe(highlight_extremes(price_matrix_df.style), width='stretch')
        else:
            st.info("Loading prices…")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Countdown (now 100% visible) ──
    for secs in range(REFRESH_SEC, 0, -1):
        time.sleep(1)

    st.rerun()