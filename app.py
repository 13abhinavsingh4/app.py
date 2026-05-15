import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Institutional Option Analyzer",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. Static Assets (Defining CSS outside of st.markdown calls to prevent TypeErrors)
# -----------------------------------------------------------------------------
CSS_CODE = """
<style>
    .metric-card {
        background-color: #0f172a;
        border-radius: 10px;
        padding: 20px;
        border-left: 6px solid #3b82f6;
        margin-bottom: 20px;
    }
    .bullish { border-left-color: #22c55e !important; }
    .bearish { border-left-color: #ef4444 !important; }
    .st-contradiction {
        background-color: #450a0a;
        padding: 15px;
        border-radius: 8px;
        color: #fecaca;
        border: 1px solid #7f1d1d;
        margin: 10px 0;
    }
    .st-strategy {
        background-color: #064e3b;
        padding: 15px;
        border-radius: 8px;
        color: #d1fae5;
        border: 1px solid #065f46;
        margin: 10px 0;
    }
</style>
"""
st.markdown(CSS_CODE, unsafe_with_html=True)

# -----------------------------------------------------------------------------
# 3. Functional Logic
# -----------------------------------------------------------------------------
def clean_and_load(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        df.columns = [str(c).strip() for c in df.columns]
        req = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        
        # Validate existence
        if not all(col in df.columns for col in req):
            st.error(f"Required columns missing in {file.name}")
            return None
            
        # Ensure numeric conversion
        for col in req:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna(subset=['Strike Price'])
    except Exception as e:
        st.error(f"Critical Data Error: {e}")
        return None

def calc_fibs(high, low):
    # Flattened logic to prevent syntax nesting errors
    span = high - low
    levels = {
        "161.8%": low + (span * 1.618),
        "100% (High)": high,
        "61.8% (Golden)": low + (span * 0.618),
        "50.0% (Mid)": low + (span * 0.5),
        "38.2%": low + (span * 0.382),
        "23.6%": low + (span * 0.236),
        "0% (Low)": low
    }
    return levels

# -----------------------------------------------------------------------------
# 4. Main App Interface
# -----------------------------------------------------------------------------
st.title("🛡️ Institutional Option Dynamics & Fibonacci Grid")

# Sidebar Uploads
with st.sidebar:
    st.header("Control Center")
    prev_csv = st.file_uploader("Upload Previous Day", type="csv")
    curr_csv = st.file_uploader("Upload Current Day", type="csv")

if prev_csv and curr_csv:
    df_p = clean_and_load(prev_csv)
    df_c = clean_and_load(curr_csv)

    if df_p is not None and df_c is not None:
        # Match strikes
        p_strikes = set(df_p['Strike Price'])
        c_strikes = set(df_c['Strike Price'])
        available_strikes = sorted(list(p_strikes.intersection(c_strikes)))

        if not available_strikes:
            st.error("No overlapping strike prices found in files.")
            st.stop()

        target = st.sidebar.selectbox("Target Strike Price", available_strikes)

        # Extraction
        prev_row = df_p[df_p['Strike Price'] == target].iloc[0]
        curr_row = df_c[df_c['Strike Price'] == target].iloc[0]

        # Delta Calculations
        ce_oi_delta = curr_row['CE OI'] - prev_row['CE OI']
        pe_oi_delta = curr_row['PE OI'] - prev_row['PE OI']
        
        def safe_pct(c, p):
            return ((c - p) / p * 100) if p and p != 0 else 0

        ce_p_change = safe_pct(curr_row['CE Price'], prev_row['CE Price'])
        pe_p_change = safe_pct(curr_row['PE Price'], prev_row['PE Price'])

        # Display Tiers
        tab1, tab2, tab3 = st.tabs(["Dashboard", "Fibonacci Matrix", "Strategy Engine"])

        with tab1:
            st.subheader(f"Intraday Delta: Strike {target}")
            col1, col2, col3, col4 = st.columns(4)
            
            # CE Metrics
            c1_cls = "bullish" if ce_p_change > 0 else "bearish"
            col1.markdown(f"<div class='metric-card {c1_cls}'>CE Price Chg<br><h2>{ce_p_change:+.2f}%</h2></div>", unsafe_with_html=True)
            
            c2_cls = "bearish" if ce_oi_delta > 0 else "bullish"
            col2.markdown(f"<div class='metric-card {c2_cls}'>CE OI Change<br><h2>{ce_oi_delta:+,}</h2></div>", unsafe_with_html=True)
            
            # PE Metrics
            c3_cls = "bullish" if pe_p_change > 0 else "bearish"
            col3.markdown(f"<div class='metric-card {c3_cls}'>PE Price Chg<br><h2>{pe_p_change:+.2f}%</h2></div>", unsafe_with_html=True)
            
            c4_cls = "bearish" if pe_oi_delta > 0 else "bullish"
            col4.markdown(f"<div class='metric-card {c4_cls}'>PE OI Change<br><h2>{pe_oi_delta:+,}</h2></div>", unsafe_with_html=True)

            # Chart
            fig = go.Figure(data=[
                go.Bar(name='CE OI Delta', x=['Calls'], y=[ce_oi_delta], marker_color='#ef4444'),
                go.Bar(name='PE OI Delta', x=['Puts'], y=[pe_oi_delta], marker_color='#22c55e')
            ])
            fig.update_layout(template="plotly_dark", title="Net Open Interest Shift", barmode='group')
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Fibonacci Premium Retracement")
            high_val = float(max(curr_row['CE Price'], curr_row['PE Price']))
            low_val = float(min(curr_row['CE Price'], curr_row['PE Price']))
            if high_val == low_val: high_val += 1.0
            
            fib_levels = calc_fibs(high_val, low_val)
            
            fig_fib = go.Figure()
            for label, val in fib_levels.items():
                fig_fib.add_hline(y=val, line_dash="dot", annotation_text=f"{label}: {val:.2f}")
            
            fig_fib.update_layout(template="plotly_dark", yaxis_title="Option Premium")
            st.plotly_chart(fig_fib, use_container_width=True)

        with tab3:
            st.subheader("Systematic Intelligence")
            
            # 1. Contradictions (Logical Divergence)
            st.markdown("#### Structural Contradictions")
            found_contradiction = False
            
            if ce_oi_delta > 0 and ce_p_change < 0:
                st.markdown("<div class='st-contradiction'><b>CE SHORT BUILDUP:</b> OI is rising while premiums fall. Professional writing detected at resistance.</div>", unsafe_with_html=True)
                found_contradiction = True
            
            if pe_oi_delta > 0 and pe_p_change < 0:
                st.markdown("<div class='st-contradiction'><b>PE SHORT BUILDUP:</b> OI rising while premiums fall. Support floor being cemented by writers.</div>", unsafe_with_html=True)
                found_contradiction = True
                
            if not found_contradiction:
                st.info("No logical contradictions found. Market following standard momentum.")

            # 2. Strategy Matrix
            st.markdown("#### Tactical Strategy")
            s_col1, s_col2 = st.columns(2)
            
            ce_strat = "BUY / LONG" if (ce_oi_delta < 0 and ce_p_change > 0) else "SELL / WRITE" if ce_oi_delta > 0 else "NEUTRAL"
            pe_strat = "BUY / LONG" if (pe_oi_delta < 0 and pe_p_change > 0) else "SELL / WRITE" if pe_oi_delta > 0 else "NEUTRAL"
            
            s_col1.markdown(f"<div class='st-strategy'><b>CE Position:</b> {ce_strat}</div>", unsafe_with_html=True)
            s_col2.markdown(f"<div class='st-strategy' style='background-color:#1e1b4b'><b>PE Position:</b> {pe_strat}</div>", unsafe_with_html=True)

else:
    st.info("Awaiting CSV data upload to initialize Institutional Analysis.")
