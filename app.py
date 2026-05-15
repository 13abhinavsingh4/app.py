import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# Configuration & Global Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Option Dynamics Pro",
    page_icon="📈",
    layout="wide"
)

# Robust CSS injection to avoid TypeError in st.markdown
CSS_TEMPLATE = """
<style>
    .metric-card {
        background-color: #111827;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 15px;
    }
    .metric-card.bullish { border-left-color: #10b981; }
    .metric-card.bearish { border-left-color: #ef4444; }
    
    .contradiction-box {
        background-color: #450a0a;
        border: 1px solid #f87171;
        border-radius: 10px;
        padding: 15px;
        color: #fca5a5;
        margin: 10px 0px;
    }
    
    .strategy-box {
        background-color: #064e3b;
        border: 1px solid #34d399;
        border-radius: 10px;
        padding: 15px;
        color: #a7f3d0;
        margin: 10px 0px;
    }
</style>
"""
st.markdown(CSS_TEMPLATE, unsafe_with_html=True)

# -----------------------------------------------------------------------------
# Business Logic Functions
# -----------------------------------------------------------------------------
def load_data(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        req = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        if not all(col in df.columns for col in req):
            st.error(f"File {file.name} is missing columns. Expected: {req}")
            return None
        return df.apply(pd.to_numeric, errors='coerce').dropna(subset=['Strike Price'])
    except Exception as e:
        st.error(f"Read Error: {e}")
        return None

def get_fib_levels(high, low):
    diff = high - low
    return {
        "100% (High)": high,
        "161.8% (Golden Extension)": low + 1.618 * diff,
        "61.8% (Golden Ratio)": low + 0.618 * diff,
        "50.0% (Mid)": low + 0.5 * diff,
        "38.2%": low + 0.382 * diff,
        "23.6%": low + 0.236 * diff,
        "0% (Low)": low
    }

# -----------------------------------------------------------------------------
# App Layout
# -----------------------------------------------------------------------------
st.title("📊 Option Chain & Fibonacci Dynamics")

with st.sidebar:
    st.header("Settings")
    file_p = st.file_uploader("Upload Previous Day CSV", type="csv")
    file_c = st.file_uploader("Upload Current Day CSV", type="csv")

if file_p and file_c:
    df_p = load_data(file_p)
    df_c = load_data(file_c)

    if df_p is not None and df_c is not None:
        common_strikes = sorted(list(set(df_p['Strike Price']).intersection(set(df_c['Strike Price']))))
        target_strike = st.sidebar.selectbox("Target Strike Price", common_strikes)

        # Data Slicing
        row_p = df_p[df_p['Strike Price'] == target_strike].iloc[0]
        row_c = df_c[df_c['Strike Price'] == target_strike].iloc[0]

        # Calculation Engine
        ce_oi_delta = row_c['CE OI'] - row_p['CE OI']
        pe_oi_delta = row_c['PE OI'] - row_p['PE OI']
        ce_pr_chg = ((row_c['CE Price'] - row_p['CE Price']) / row_p['CE Price'] * 100) if row_p['CE Price'] != 0 else 0
        pe_pr_chg = ((row_c['PE Price'] - row_p['PE Price']) / row_p['PE Price'] * 100) if row_p['PE Price'] != 0 else 0
        pcr = row_c['PE OI'] / row_c['CE OI'] if row_c['CE OI'] != 0 else 0

        # UI: Dashboard Tabs
        t1, t2, t3, t4 = st.tabs(["Dashboard", "Visuals", "Fibonacci", "Strategy"])

        with t1:
            st.subheader(f"Strike {target_strike} Summary")
            cols = st.columns(4)
            metrics = [
                ("CE Price Chg", f"{ce_pr_chg:+.2f}%", ce_pr_chg > 0),
                ("CE OI Delta", f"{ce_oi_delta:+,}", ce_oi_delta < 0), # OI reduction usually bullish for CE
                ("PE Price Chg", f"{pe_pr_chg:+.2f}%", pe_pr_chg > 0),
                ("PE OI Delta", f"{pe_oi_delta:+,}", pe_oi_delta < 0)
            ]
            for i, (label, val, is_bull) in enumerate(metrics):
                cls = "bullish" if is_bull else "bearish"
                cols[i].markdown(f"<div class='metric-card {cls}'><b>{label}</b><h2>{val}</h2></div>", unsafe_with_html=True)

        with t2:
            fig = go.Figure(data=[
                go.Bar(name='CE OI Change', x=['CE Delta'], y=[ce_oi_delta], marker_color='#ef4444'),
                go.Bar(name='PE OI Change', x=['PE Delta'], y=[pe_oi_delta], marker_color='#10b981')
            ])
            fig.update_layout(template
