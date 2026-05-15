import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. Configuration & Global Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Option Dynamics Pro",
    page_icon="📈",
    layout="wide"
)

# Safer CSS Injection
st.markdown("""
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
""", unsafe_with_html=True)

# -----------------------------------------------------------------------------
# 2. Logic Functions (Simplified for Stability)
# -----------------------------------------------------------------------------
def load_data(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        req = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        if not all(col in df.columns for col in req):
            st.error(f"Missing columns in {file.name}")
            return None
        df = df.apply(pd.to_numeric, errors='coerce')
        return df.dropna(subset=['Strike Price'])
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def calculate_fibs(h, l):
    d = h - l
    # Explicit dictionary creation to avoid SyntaxErrors
    levels = {}
    levels["161.8% Ext"] = l + (1.618 * d)
    levels["100% High"] = h
    levels["61.8% Ratio"] = l + (0.618 * d)
    levels["50.0% Mid"] = l + (0.5 * d)
    levels["38.2%"] = l + (0.382 * d)
    levels["23.6%"] = l + (0.236 * d)
    levels["0% Low"] = l
    return levels

# -----------------------------------------------------------------------------
# 3. Main Application Flow
# -----------------------------------------------------------------------------
st.title("📊 Option Chain & Fibonacci Dynamics")

# Sidebar
st.sidebar.header("Data Upload")
f_prev = st.sidebar.file_uploader("Previous Day CSV", type="csv")
f_curr = st.sidebar.file_uploader("Current Day CSV", type="csv")

if f_prev and f_curr:
    df_p = load_data(f_prev)
    df_c = load_data(f_curr)

    if df_p is not None and df_c is not None:
        # Find common strikes
        strikes = sorted(list(set(df_p['Strike Price']).intersection(set(df_c['Strike Price']))))
        
        if not strikes:
            st.warning("No matching Strike Prices found.")
            st.stop()
            
        sel_strike = st.sidebar.selectbox("Select Strike Price", strikes)

        # Extraction
        d_p = df_p[df_p['Strike Price'] == sel_strike].iloc[0]
        d_c = df_c[df_c['Strike Price'] == sel_strike].iloc[0]

        # Deltas
        ce_oi_delta = d_c['CE OI'] - d_p['CE OI']
        pe_oi_delta = d_c['PE OI'] - d_p['PE OI']
        
        def pct(c, p):
            return ((c - p) / p * 100) if p != 0 else 0

        ce_p_chg = pct(d_c['CE Price'], d_p['CE Price'])
        pe_p_chg = pct(d_c['PE Price'], d_p['PE Price'])

        # Tabs
        t1, t2, t3, t4 = st.tabs(["Dashboard", "Charts", "Fibonacci", "Strategy"])

        with t1:
            st.subheader(f"Analysis for {sel_strike}")
            c1, c2, c3, c4 = st.columns(4)
            
            c1.markdown(f"<div class='metric-card {'bullish' if ce_p_chg > 0 else 'bearish'}'>CE Price Chg<br><h2>{ce_p_chg:+.2f}%</h2></div>", unsafe_with_html=True)
            c2.markdown(f"<div class='metric-card {'bearish' if ce_oi_delta > 0 else 'bullish'}'>CE OI Delta<br><h2>{ce_oi_delta:+,}</h2></div>", unsafe_with_html=True)
            c3.markdown(f"<div class='metric-card {'bullish' if pe_p_chg > 0 else 'bearish'}'>PE Price Chg<br><h2>{pe_p_chg:+.2f}%</h2></div>", unsafe_with_html=True)
            c4.markdown(f"<div class='metric-card {'bearish' if pe_oi_delta > 0 else 'bullish'}'>PE OI Delta<br><h2>{pe_oi_delta:+,}</h2></div>", unsafe_with_html=True)

        with t2:
            fig_oi = go.Figure(data=[
                go.Bar(name='CE OI', x=['CE'], y=[ce_oi_delta], marker_color='red'),
                go.Bar(name='PE OI', x=['PE'], y=[pe_oi_delta], marker_color='green')
            ])
            fig_oi.update_layout(template="plotly_dark", title="OI Change")
            st.plotly_chart(fig_oi, use_container_width=True)

        with t3:
            h_val = float(max(d_c['CE Price'], d_c['PE Price']))
            l_val = float(min(d_c['CE Price'], d_c['PE Price']))
            if h_val == l_val: h_val += 1.0
            
            fib_map = calculate_fibs(h_val, l_val)
            fig_f = go.Figure()
            for k, v in fib_map.items():
                fig_f.add_hline(y=v, line_dash="dash", annotation_text=f"{k}: {v:.2f}")
            fig_f.update_layout(template="plotly_dark", title="Fibonacci Retracement")
            st.plotly_chart(fig_f, use_container_width=True)

        with t4:
            st.subheader("Market Logic")
            # Contradictions
            msg_list = []
            if ce_oi_delta > 0 and ce_p_chg < 0:
                msg_list.append("🚨 CE Shorting: OI Up, Price Down. Resistance Heavy.")
            if pe_oi_delta > 0 and pe_p_chg < 0:
                msg_list.append("🚨 PE Shorting: OI Up, Price Down. Floor Supporting.")
            
            if msg_list:
                for m in msg_list:
                    st.markdown(f"<div class='contradiction-box'>{m}</div>", unsafe_with_html=True)
            else:
                st.info("No major logical contradictions detected.")

            # Strategy
            s1, s2 = st.columns(2)
            ce_s = "BUY" if (ce_oi_delta < 0 and ce_p_chg > 0) else "SELL" if ce_oi_delta > 0 else "HOLD"
            pe_s = "BUY" if (pe_oi_delta < 0 and pe_p_chg > 0) else "SELL" if pe_oi_delta > 0 else "HOLD"
            
            s1.markdown(f"<div class='strategy-box'><b>CE: {ce_s}</b></div>", unsafe_with_html=True)
            s2.markdown(f"<div class='strategy-box' style='background:#1e1b4b;'><b>PE: {pe_s}</b></div>", unsafe_with_html=True)
else:
    st.info("Please upload CSV files in the sidebar to begin.")
