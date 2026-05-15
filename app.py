import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. CORE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Option Analytics Pro",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. ROBUST DATA PROCESSING
# -----------------------------------------------------------------------------
def process_upload(file):
    if file is None:
        return None
    try:
        # Load and clean column names
        data = pd.read_csv(file)
        data.columns = [str(c).strip() for c in data.columns]
        
        # Verify columns
        required = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        if not all(col in data.columns for col in required):
            st.error(f"Missing columns in {file.name}. Expected: {required}")
            return None
            
        # Convert to numeric
        for col in required:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            
        return data.dropna(subset=['Strike Price'])
    except Exception as e:
        st.error(f"File Error: {e}")
        return None

def get_fibonacci_grid(h, l):
    rng = h - l
    if rng == 0: rng = 1.0
    # Explicitly defined to prevent dict parser errors
    f = {}
    f["161.8% (Golden Extension)"] = l + (rng * 1.618)
    f["100.0% (High)"] = h
    f["61.8% (Golden Ratio)"] = l + (rng * 0.618)
    f["50.0% (Midpoint)"] = l + (rng * 0.5)
    f["38.2%"] = l + (rng * 0.382)
    f["23.6%"] = l + (rng * 0.236)
    f["0.0% (Low)"] = l
    return f

# -----------------------------------------------------------------------------
# 3. SIDEBAR (FILE UPLOADERS)
# -----------------------------------------------------------------------------
st.sidebar.title("📁 Data Source")
uploaded_prev = st.sidebar.file_uploader("Upload Previous Day CSV", type=["csv"])
uploaded_curr = st.sidebar.file_uploader("Upload Current Day CSV", type=["csv"])

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD LOGIC
# -----------------------------------------------------------------------------
st.title("🛡️ Option Chain Dynamics & Strategy")

if uploaded_prev and uploaded_curr:
    df_p = process_upload(uploaded_prev)
    df_c = process_upload(uploaded_curr)

    if df_p is not None and df_c is not None:
        # Match strikes
        common = sorted(list(set(df_p['Strike Price']).intersection(set(df_c['Strike Price']))))
        
        if not common:
            st.error("Strike Price mismatch between files.")
            st.stop()

        # Selection
        strike = st.sidebar.selectbox("Select Target Strike Price", common)
        
        # Extract rows
        r_p = df_p[df_p['Strike Price'] == strike].iloc[0]
        r_c = df_c[df_c['Strike Price'] == strike].iloc[0]

        # Calculations
        ce_oi_delta = r_c['CE OI'] - r_p['CE OI']
        pe_oi_delta = r_c['PE OI'] - r_p['PE OI']
        
        def calc_pct(c, p):
            return ((c - p) / p * 100) if p != 0 else 0

        ce_pr_chg = calc_pct(r_c['CE Price'], r_p['CE Price'])
        pe_pr_chg = calc_pct(r_c['PE Price'], r_p['PE Price'])

        # Organized Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Performance", "🌀 Fibonacci Grid", "🎯 Strategy Engine"])

        with tab1:
            st.subheader(f"Intraday Comparison: Strike {strike}")
            col1, col2, col3, col4 = st.columns(4)
            
            # Use native st.metric (Safe and reliable)
            col1.metric("CE Price", f"{r_c['CE Price']}", f"{ce_pr_chg:.2f}%")
            col2.metric("CE OI Delta", f"{int(r_c['CE OI']):,}", f"{int(ce_oi_delta):+,}")
            col3.metric("PE Price", f"{r_c['PE Price']}", f"{pe_pr_chg:.2f}%")
            col4.metric("PE OI Delta", f"{int(r_c['PE OI']):,}", f"{int(pe_oi_delta):+,}")

            # Plotly Chart
            fig_oi = go.Figure(data=[
                go.Bar(name='CE OI Shift', x=['Calls'], y=[ce_oi_delta], marker_color='red'),
                go.Bar(name='PE OI Shift', x=['Puts'], y=[pe_oi_delta], marker_color='green')
            ])
            fig_oi.update_layout(template="plotly_dark", height=400, title="Net OI Delta Shift")
            st.plotly_chart(fig_oi, use_container_width=True)

        with tab2:
            st.subheader("Premium Fibonacci Retracement")
            high_val = float(max(r_c['CE Price'], r_c['PE Price'], r_p['CE Price'], r_p['PE Price']))
            low_val = float(min(r_c['CE Price'], r_c['PE Price'], r_p['CE Price'], r_p['PE Price']))
            
            fib_map = get_fibonacci_grid(high_val, low_val)
            
            fig_f = go.Figure()
            for label, value in fib_map.items():
                fig_f.add_hline(y=value, line_dash="dash", annotation_text=label)
            
            fig_f.update_layout(template="plotly_dark", yaxis_title="Premium Value", height=500)
            st.plotly_chart(fig_f, use_container_width=True)

        with tab3:
            st.subheader("Contradictions & Strategy formulation")
            
            # 1. Contradictions
            st.info("**Step 1: Analyzing Market Contradictions**")
            found = False
            if ce_oi_delta > 0 and ce_pr_chg < 0:
                st.warning("⚠️ CONTRADICTION: CE OI rising with falling price. Strong Writing (Selling) detected.")
                found = True
            if pe_oi_delta > 0 and pe_pr_chg < 0:
                st.warning("⚠️ CONTRADICTION: PE OI rising with falling price. Strong Support writing detected.")
                found = True
            if not found:
                st.write("No major structural contradictions found.")

            # 2. Strategy
            st.success("**Step 2: Strategy formulation**")
            c_strat = "BUY/LONG" if (ce_oi_delta < 0 and ce_pr_chg > 0) else "SELL/WRITE" if (ce_oi_delta > 0) else "NEUTRAL"
            p_strat = "BUY/LONG" if (pe_oi_delta < 0 and pe_pr_chg > 0) else "SELL/WRITE" if (pe_oi_delta > 0) else "NEUTRAL"
            
            s1, s2 = st.columns(2)
            s1.write(f"**Call Option View:** {c_strat}")
            s2.write(f"**Put Option View:** {p_strat}")
else:
    st.info("Waiting for Previous and Current CSV files to be uploaded via the sidebar.")
