import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any

import streamlit as st
import pandas as pd

# existing imports from your package
from src.arbitrage_scanner import find_arbitrage, exchanges, SYMBOLS
from src.config import REFRESH_SEC

# optional plotly
try:
    import plotly.express as px
except Exception:
    px = None

st.set_page_config(page_title="Crypto Arbitrage Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- Styles (kept from previous design) ---
st.markdown(
    """
    <style>
    :root {
      --bg:#0b1020;
      --card:#0f1724;
      --muted:#9aa4b2;
      --accent:#00d4ff;
      --success:#16c784;
      --danger:#ff4d6d;
    }
    .stApp { background: linear-gradient(180deg, #071020 0%, #081426 60%); color: #e6eef6; }
    .header { display:flex; align-items:center; gap:12px; margin-bottom:18px; }
    .brand { font-weight:800; font-size:20px; color:var(--accent); padding:8px 12px; border-radius:10px; }
    .small { font-size:12px; color:var(--muted) }
    .card { background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.03); padding:14px; border-radius:10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="header">
      <div class="brand">Crypto Arbitrage Scanner</div>
      <div style="flex:1"></div>
      <div class="small">Live multi-exchange price scanner</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Helper: build best-per-pair table ---
def best_per_pair(df, symbols):
    if df is None or df.empty:
        rows = []
        for s in symbols:
            rows.append({"Pair": s, "Buy": "-", "Sell": "-", "Spread": "-", "Profit (after fees)": "0.00%", "Time": "-"})
        return pd.DataFrame(rows)
    df = df.copy()
    # find profit column (flexible naming)
    prof_col = next((c for c in df.columns if 'profit' in c.lower()), None)
    if prof_col is None:
        df['Profit (after fees)'] = "0.00%"
        prof_col = 'Profit (after fees)'
    # numeric profit for sorting
    df['_profit_val'] = df[prof_col].astype(str).str.rstrip('%').replace('', '0').astype(float)
    best = df.sort_values('_profit_val', ascending=False).groupby('Pair', as_index=False).first().drop(columns=['_profit_val'])
    missing = set(symbols) - set(best['Pair'].tolist())
    for s in missing:
        best = pd.concat([best, pd.DataFrame([{"Pair": s, "Buy": "-", "Sell": "-", "Spread": "-", "Profit (after fees)": "0.00%", "Time": "-"}])], ignore_index=True, sort=False)
    best = best.set_index('Pair').reindex(symbols).reset_index()
    return best

# --- Helper: fetch prices across exchanges (used by worker) ---
def get_all_prices():
    rows = []
    for symbol in SYMBOLS:
        row = {"Pair": symbol}
        for ex_name, ex in exchanges.items():
            try:
                # try common variants; fetch_ticker in exchange handles many cases
                ticker = None
                try:
                    ticker = ex.fetch_ticker(symbol)
                except Exception:
                    try:
                        ticker = ex.fetch_ticker(symbol.replace('/', ''))
                    except Exception:
                        try:
                            ticker = ex.fetch_ticker(symbol.replace('/', '-'))
                        except Exception:
                            ticker = None
                if ticker and ticker.get('bid') and ticker.get('ask'):
                    price = (ticker['bid'] + ticker['ask']) / 2
                    row[ex_name.upper()] = price
                else:
                    row[ex_name.upper()] = None
            except Exception:
                row[ex_name.upper()] = None
        rows.append(row)
    return pd.DataFrame(rows)

# --- Background worker that periodically refreshes cached data ---
CACHE: Dict[str, Any] = {
    "arbs": pd.DataFrame(),
    "prices": pd.DataFrame(),
    "last_fetch": datetime.now(timezone.utc),
}
cache_lock = threading.Lock()

def background_fetch_loop():
    while True:
        try:
            arbs = find_arbitrage()
        except Exception:
            arbs = pd.DataFrame()
        try:
            prices = get_all_prices()
        except Exception:
            prices = pd.DataFrame()
        # update shared cache (do NOT call streamlit APIs from background thread)
        with cache_lock:
            CACHE['arbs'] = arbs
            CACHE['prices'] = prices
            CACHE['last_fetch'] = datetime.now(timezone.utc)
        time.sleep(max(1, int(REFRESH_SEC)))

# --- Start background worker once per session ---
if 'worker_started' not in st.session_state:
    # perform an initial synchronous fetch so UI has something immediately (main thread)
    try:
        initial_arbs = find_arbitrage()
    except Exception:
        initial_arbs = pd.DataFrame()
    try:
        initial_prices = get_all_prices()
    except Exception:
        initial_prices = pd.DataFrame()
    with cache_lock:
        CACHE['arbs'] = initial_arbs
        CACHE['prices'] = initial_prices
        CACHE['last_fetch'] = datetime.now(timezone.utc)
    # start background worker (worker updates CACHE only)
    t = threading.Thread(target=background_fetch_loop, daemon=True, name="bg_fetcher")
    t.start()
    st.session_state['worker_started'] = True

# --- Read cached values for display (read from thread-safe CACHE) ---
with cache_lock:
    cached_arbs = CACHE.get('arbs', pd.DataFrame()).copy()
    cached_prices = CACHE.get('prices', pd.DataFrame()).copy()
    last_fetch = CACHE.get('last_fetch', datetime.now(timezone.utc))

# --- Build display data ---
best_df = best_per_pair(cached_arbs, list(SYMBOLS))

# Top-right quick stats
total_pairs = len(SYMBOLS)
profit_vals = []
if 'Profit (after fees)' in best_df.columns:
    try:
        profit_vals = best_df['Profit (after fees)'].astype(str).str.rstrip('%').astype(float).tolist()
    except Exception:
        profit_vals = []
best_positive = max(profit_vals) if profit_vals else 0.0
opportunities = sum(1 for v in profit_vals if v > 0)

left, right = st.columns([3, 1])
with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric(label="Scanned pairs", value=f"{total_pairs}")
    st.metric(label="Positive arb", value=f"{opportunities}")
    st.metric(label="Best profit", value=f"{best_positive:.2f}%")
    st.markdown('</div>', unsafe_allow_html=True)

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🏆 Most Profitable Trades")
    # Format numeric columns with 4 decimal places for better readability
    def _format_num(v):
        try:
            if v is None:
                return "-"

            # keep existing '-' strings
            if isinstance(v, str) and v.strip() == "-":
                return v

            f = float(v)
            return f"{f:,.4f}"
        except Exception:
            return v

    display_best = best_df.copy()
    for col in ("Buy", "Sell", "Spread"):
        if col in display_best.columns:
            display_best[col] = display_best[col].apply(_format_num)

    # Ensure profit column stays formatted as percentage (if present)
    if "Profit (after fees)" in display_best.columns:
        display_best["Profit (after fees)"] = display_best["Profit (after fees)"].astype(str)

    st.dataframe(display_best, width='stretch', hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Prices section with Last scan + Next refresh on same line ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 💹 Recent Prices Across Exchanges")

# compute seconds until next background update (based on last_fetch, timezone-aware)
elapsed = (datetime.now(timezone.utc) - last_fetch).total_seconds()
secs_left = max(0, int(REFRESH_SEC - elapsed))

col_l, col_r = st.columns([3, 1])
with col_l:
    st.markdown(f"<div class='small'>Last scan: <strong style='color:var(--accent)'>{last_fetch.strftime('%b %d, %Y %H:%M:%S')} UTC</strong></div>", unsafe_allow_html=True)
with col_r:
    countdown_placeholder = col_r.empty()

# format prices table
prices_display = cached_prices.copy()
for c in prices_display.columns:
    if c == 'Pair':
        continue
    prices_display[c] = prices_display[c].apply(lambda v: f"${v:,.4f}" if pd.notnull(v) else "-")

st.dataframe(prices_display, width='stretch', hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)

# small profit chart (fallback if plotly unavailable)
try:
    if 'Profit (after fees)' in best_df.columns and px is not None:
        chart_df = best_df.copy()
        chart_df['ProfitNum'] = chart_df['Profit (after fees)'].astype(str).str.rstrip('%').astype(float)
        fig = px.bar(chart_df, x='Pair', y='ProfitNum', color='ProfitNum',
                     color_continuous_scale=['#ff4d6d', '#16c784'],
                     labels={'ProfitNum': 'Profit %'},
                     height=220)
        st.plotly_chart(fig, width='stretch')
    elif 'Profit (after fees)' in best_df.columns:
        chart_df = best_df.copy()
        chart_df['ProfitNum'] = chart_df['Profit (after fees)'].astype(str).str.rstrip('%').astype(float)
        st.bar_chart(chart_df.set_index('Pair')['ProfitNum'])
except Exception:
    pass

# --- Disclaimer at bottom ---
st.markdown("<hr style='opacity:0.08'>", unsafe_allow_html=True)
with st.expander("Important Disclaimer", expanded=False):
    st.markdown("""
    - This is **not financial advice**.
    - Arbitrage opportunities may **disappear in seconds**.
    - Fees, slippage & latency are **estimates**.
    - Use at your own risk.
    """)

# --- Countdown UI: big number + label on same line. When reaches zero, rerun to show latest cached data ---
for i in range(secs_left, -1, -1):
    html = f"""
    <div style="display:flex;align-items:center;justify-content:flex-end;gap:8px">
      <span style="font-size:28px;font-weight:800;color:#00aaff">{i}s</span>
      <span style="font-size:14px;color:#9aa4b2;font-weight:600">Next refresh</span>
    </div>
    """
    countdown_placeholder.markdown(html, unsafe_allow_html=True)
    time.sleep(1)

# page rerun so UI picks up the newest cached values
st.rerun()