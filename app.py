import streamlit as st
import pandas as pd
import time
import plotly.express as px
from src.arbitrage_scanner import find_arbitrage, exchanges, SYMBOLS

st.set_page_config(page_title="Crypto Arbitrage Dashboard", layout="wide", initial_sidebar_state="collapsed")
# --- Modern styling ---
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
    .header {
      display:flex; align-items:center; gap:12px; margin-bottom:18px;
    }
    .brand {
      font-weight:800; font-size:20px; color:var(--accent);
      background: linear-gradient(90deg, rgba(0,212,255,0.12), rgba(0,122,255,0.06));
      padding:8px 12px; border-radius:10px;
    }
    .subtitle { color:var(--muted); font-size:13px; margin-bottom:6px }
    .card {
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border: 1px solid rgba(255,255,255,0.03);
      padding:14px; border-radius:10px;
    }
    .small { font-size:12px; color:var(--muted) }
    .highlight { background: linear-gradient(90deg, rgba(22,199,132,0.08), rgba(0,212,255,0.04)); }
    .profit-positive { color: var(--success); font-weight:700; }
    .profit-negative { color: var(--danger); font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div class="header">
      <div class="brand">Crypto Arbitrage • Neon</div>
      <div style="flex:1"></div>
      <div class="small">Live multi-exchange price scanner</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Fetch data once per run ---
arbitrage_df = find_arbitrage()  # expected to return pd.DataFrame or empty df

# --- Prepare "best per pair" table (always show one row per symbol) ---
def best_per_pair(df, symbols):
    if df is None or df.empty:
        # create placeholder rows with basic columns if needed
        rows = []
        for s in symbols:
            rows.append({"Pair": s, "Buy @": "-", "Sell @": "-", "Buy exchange": "-", "Sell exchange": "-", "Profit (after fees)": "0.00%"})
        return pd.DataFrame(rows)
    # Ensure consistent column names
    cols = df.columns
    # if profit column exists as string with %, normalize
    prof_col = None
    for c in cols:
        if 'profit' in c.lower():
            prof_col = c
            break
    if prof_col is None:
        df['Profit (after fees)'] = "0.00%"
        prof_col = 'Profit (after fees)'
    # normalize numeric profit for sorting
    df['_profit_val'] = df[prof_col].astype(str).str.rstrip('%').replace('', '0').astype(float)
    best = df.sort_values('_profit_val', ascending=False).groupby('Pair', as_index=False).first()
    best = best.drop(columns=['_profit_val'])
    # ensure all symbols present
    missing = set(symbols) - set(best['Pair'].tolist())
    for s in missing:
        best = pd.concat([best, pd.DataFrame([{"Pair": s, "Profit (after fees)": "0.00%"}])], ignore_index=True, sort=False)
    # final ordering same as SYMBOLS
    best['Pair'] = best['Pair'].astype(str)
    best = best.set_index('Pair').reindex(symbols).reset_index()
    return best

best_df = best_per_pair(arbitrage_df, list(SYMBOLS))

# --- Prices table (all recent prices) ---
def get_all_prices():
    rows = []
    for symbol in SYMBOLS:
        row = {"Pair": symbol}
        for ex_name, ex in exchanges.items():
            try:
                # normalized lookup is handled by exchange wrapper; try symbol first, fallback to symbol.replace
                sym_try = symbol
                try:
                    ticker = ex.fetch_ticker(sym_try)
                except Exception:
                    try:
                        sym_try = symbol.replace('/', '')  # common fallback
                        ticker = ex.fetch_ticker(sym_try)
                    except Exception:
                        ticker = None
                if ticker and ticker.get('bid') and ticker.get('ask'):
                    price = (ticker['bid'] + ticker['ask']) / 2
                    row[ex_name] = price
                else:
                    row[ex_name] = None
            except Exception:
                row[ex_name] = None
        rows.append(row)
    return pd.DataFrame(rows)

prices_df = get_all_prices()

# --- Top summary metrics ---
total_pairs = len(SYMBOLS)
# extract numeric profit values from best_df if present
profit_vals = []
if 'Profit (after fees)' in best_df.columns:
    try:
        profit_vals = best_df['Profit (after fees)'].astype(str).str.rstrip('%').astype(float).tolist()
    except Exception:
        profit_vals = []
best_positive = max(profit_vals) if profit_vals else 0.0
opportunities = sum(1 for v in profit_vals if v > 0)

# layout: left cards + right quick stats
left, right = st.columns([3,1])
with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric(label="Scanned pairs", value=f"{total_pairs}")
    st.metric(label="Positive arb", value=f"{opportunities}")
    st.metric(label="Best profit", value=f"{best_positive:.2f}%")
    st.markdown('</div>', unsafe_allow_html=True)

with left:
    # Arbitrage card (top)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🏆 Most Profitable Trades")
    # styling profits: green for >0, red for <=0
    def style_arbs(df):
        if df.empty:
            return df
        styled = df.copy()
        if 'Profit (after fees)' in styled.columns:
            styled['Profit (after fees)'] = styled['Profit (after fees)'].astype(str)
        return styled

    display_df = style_arbs(best_df)
    # Use plotly table for nicer look if small, else st.dataframe
    try:
        # color rows by profit
        def row_colors(row):
            if 'Profit (after fees)' in row.index:
                try:
                    val = float(str(row['Profit (after fees)']).rstrip('%'))
                    return ['background-color: rgba(22,199,132,0.08);' if val>0 else 'background-color: rgba(255,77,109,0.06);']*len(row)
                except Exception:
                    return ['']*len(row)
            return ['']*len(row)
        st.dataframe(display_df, width='stretch', hide_index=True)
    except Exception:
        st.dataframe(display_df, width='stretch', hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Prices section with last scan + countdown placed between heading and table ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 💹 Recent Prices Across Exchanges")
# Place last scan and next refresh here
last_scan = pd.Timestamp.now().strftime('%b %d, %Y %H:%M:%S')
col1, col2 = st.columns([2, 1])
with col1:
    st.write(f"**Last scan:** {last_scan} UTC")
with col2:
    # create a placeholder in the right column so the countdown appears on the same line
    countdown_placeholder = col2.empty()

st.dataframe(prices_df, width='stretch', hide_index=True)

# --- Disclaimer at the bottom ---
with st.expander("Important Disclaimer", expanded=False):
    st.markdown("""
    - This is **not financial advice**.
    - Arbitrage opportunities may **disappear in seconds**.
    - Fees, slippage & latency are **estimates**.
    - Use at your own risk.
    """)

# --- Countdown (big number and label on same line) ---
for i in range(30, 0, -1):
    html = f"""
    <div style="display:flex;align-items:center;justify-content:flex-end;gap:8px">
      <span style="font-size:28px;font-weight:800;color:#00aaff">{i}s</span>
      <span style="font-size:14px;color:#6b7280;font-weight:600">Next refresh</span>
    </div>
    """
    countdown_placeholder.markdown(html, unsafe_allow_html=True)
    time.sleep(1)

st.rerun()