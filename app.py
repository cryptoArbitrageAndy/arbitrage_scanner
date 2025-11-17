# app.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.arbitrage_scanner import find_arbitrage, get_all_prices_df
from src.config import REFRESH_SEC

# ────────────────────────────── STUDIO-GRADE DESIGN (FIXED) ──────────────────────────────
st.set_page_config(page_title="Arbitrage Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* Background & Font */
    .stApp {background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #e0e0ff; font-family: 'Inter', sans-serif;}
    
    /* Hero Title */
    .hero-title {
        font-size: 4.5rem; font-weight: 800; background: linear-gradient(90deg, #6c5ce7, #00cec9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center;
        margin-bottom: 0; text-shadow: 0 0 30px rgba(108,92,231,0.5);
    }
    .hero-subtitle {font-size: 1.6rem; text-align: center; opacity: 0.9; margin-top: 10px;}
    
    /* Floating Top Bar */
    .top-bar {
        position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
        background: rgba(15,12,41,0.8); backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(108,92,231,0.3);
        padding: 12px 20px; text-align: center; font-size: 1rem;
    }
    
    /* Cards */
    .glass-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid rgba(108,92,231,0.2);
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        margin-bottom: 24px;
    }
    
    /* Countdown Orb */
    .countdown-orb {
        width: 90px; height: 90px; border-radius: 50%;
        background: radial-gradient(circle, #6c5ce7, #0984e3);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem; font-weight: bold; color: white;
        box-shadow: 0 0 40px rgba(108,92,231,0.7);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {0%,100%{box-shadow:0 0 40px rgba(108,92,231,0.7)} 50%{box-shadow:0 0 60px rgba(108,92,231,1)}}
    
    /* Table glow */
    .best-price {color: #00ff9d !important; font-weight: bold;}
    .worst-price {color: #ff3b5c !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────── Floating Top Bar ──────────────────────────────
st.markdown(f"""
<div class="top-bar">
    Live Arbitrage Scanner • Binance / Kraken / Coinbase Pro • 
    Last update: <strong>{datetime.now().strftime('%H:%M:%S')}</strong> UTC
</div>
<br><br>
""", unsafe_allow_html=True)

# ────────────────────────────── Hero Section ──────────────────────────────
st.markdown("<h1 class='hero-title'>Arbitrage Pro</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>Real-time crypto arbitrage across top exchanges • Zero downtime • Studio-grade</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,1,1])
with col2:
    st.markdown("<div class='countdown-orb' id='orb'></div>", unsafe_allow_html=True)

# Placeholders
arbitrage_ph = st.empty()
price_ph = st.empty()

# ────────────────────────────── Main Loop ──────────────────────────────
while True:
    price_matrix_df = get_all_prices_df()
    arbitrage_df = find_arbitrage()

    # ── 1. ARBITRAGE TABLE (FIRST & GLOWING) ──
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
                # Return full CSS rules for row highlighting
                return pd.DataFrame(
                    ['background-color: rgba(0,255,157,0.15);' if v > 0 else '' for v in df_in[profit_col]],
                    index=df_in.index, columns=[profit_col]
                ).reindex(columns=df_in.columns, fill_value='')

            format_dict = {}
            if "Spread" in df.columns and pd.api.types.is_numeric_dtype(df["Spread"]):
                format_dict["Spread"] = "{:.2f}%"
            if profit_col in df.columns and pd.api.types.is_numeric_dtype(df[profit_col]):
                format_dict[profit_col] = "{:.2f}%"

            styled = df.style.apply(highlight_profit, axis=None).format(format_dict, na_rep="—")
            st.dataframe(styled, use_container_width=True)
            st.success(f"{len(df)} profitable arbitrage(s) detected right now")
        else:
            st.info("No profitable arbitrage at the moment – scanning continues…")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 2. PRICE MATRIX ──
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
                        lambda x: "best-price" if pd.notna(x) and x == max_v else
                                  "worst-price" if pd.notna(x) and x == min_v else "",
                        subset=(slice(None), col)
                    )
                return styled.format({c: "${:,.2f}" for c in numeric_cols}, na_rep="—")
            
            st.dataframe(highlight_extremes(price_matrix_df.style), use_container_width=True)
        else:
            st.info("Loading price data…")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Countdown Orb Update ──
    for secs in range(REFRESH_SEC, 0, -1):
        st.markdown(f"""
        <script>
            document.getElementById('orb').innerHTML = '<div style="font-size:1.4rem">{secs}<br><small>sec</small></div>';
        </script>
        """, unsafe_allow_html=True)
        time.sleep(1)

    st.rerun()