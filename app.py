import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. Page Configuration (Strictly Native)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Institutional Option Analyzer",
    page_icon="📊",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. Logic Functions
# -----------------------------------------------------------------------------
def clean_and_load(file):
    """Parses and validates the CSV data types and columns."""
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        # Remove any leading/trailing spaces from column names
        df.columns = [str(c).strip() for c in df.columns]
        
        required_columns = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        
        # Check if columns exist
        if not all(col in df.columns for col in required_columns):
            st.sidebar.error(f"Error: {file.name} is missing columns {required_columns}")
            return None
            
        # Convert to numeric, turning errors into NaN, then dropping rows with no Strike Price
        for col in required_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna(subset=['Strike Price'])
    except Exception as e:
        st.sidebar.error(f"Critical Load Error on {file.name}: {e}")
        return None

def calc_fibs(high, low):
    """Calculates Fibonacci levels based on premium price range."""
    diff = high - low
    if diff == 0:
        diff = 1.0 # Prevent division by zero
    
    return {
        "161.8% (Golden Extension)": low + (diff * 1.618),
        "100.0% (High)": high,
        "61.8% (Golden Ratio)": low + (diff * 0.618),
        "50.0% (Midpoint)": low + (diff * 0.5),
        "38.2% (Retracement)": low + (diff * 0.382),
        "23.6% (Retracement)": low + (diff * 0.236),
        "0.0% (Low)": low
    }

# -----------------------------------------------------------------------------
# 3. Main UI Sidebar (FILE UPLOADERS LOCATED HERE)
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Data Input Section")

# The uploaders are explicitly placed in the sidebar
file_prev = st.sidebar.file_uploader("1. Upload Previous Day CSV", type=["csv"])
file_curr = st.sidebar.file_uploader("2. Upload Current Day CSV", type=["csv"])

# -----------------------------------------------------------------------------
# 4. Main Dashboard Logic
# -----------------------------------------------------------------------------
st.title("🛡️ Institutional Option Dynamics & Fibonacci Strategy")
st.divider()

if file_prev and file_curr:
    df_prev = clean_and_load(file_prev)
    df_curr = clean_and_load(file_curr)

    if df_prev is not None and df_curr is not None:
        # Step 1: Match Strike Prices
        common_strikes = sorted(list(set(df_prev['Strike Price']).intersection(set(df_curr['Strike Price']))))

        if not common_strikes:
            st.error("No overlapping Strike Prices found between the two files. Please check your data.")
            st.stop()

        # Step 2: User Selection
        selected_strike = st.sidebar.selectbox("🎯 Select Target Strike", common_strikes)
        st.sidebar.success(f"Analysis Active: {selected_strike}")

        # Step 3: Data Extraction
        p_data = df_prev[df_prev['Strike Price'] == selected_strike].iloc[0]
        c_data = df_curr[df_curr['Strike Price'] == selected_strike].iloc[0]

        # Step 4: Metrics Calculation
        ce_oi_change = c_data['CE OI'] - p_data['CE OI']
        pe_oi_change = c_data['PE OI'] - p_data['PE OI']
        
        def get_pct(current, previous):
            return ((current - previous) / previous * 100) if previous != 0 else 0

        ce_price_pct = get_pct(c_data['CE Price'], p_data['CE Price'])
        pe_price_pct = get_pct(c_data['PE Price'], p_data['PE Price'])
        pcr = c_data['PE OI'] / c_data['CE OI'] if c_data['CE OI'] != 0 else 0

        # Step 5: Tabs for Systematic Organization
        tab1, tab2, tab3 = st.tabs(["📊 Comparison Dashboard", "🌀 Fibonacci Analysis", "🎯 Strategy & Contradictions"])

        with tab1:
            st.subheader(f"Strike {selected_strike} Performance Metrics")
            
            # Use Native Streamlit Metrics (No HTML/CSS to avoid TypeErrors)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("CE Price", f"{c_data['CE Price']}", f"{ce_price_pct:.2f}%")
            col2.metric("CE OI Delta", f"{int(c_data['CE OI']):,}", f"{int(ce_oi_change):+,}")
            col3.metric("PE Price", f"{c_data['PE Price']}", f"{pe_price_pct:.2f}%")
            col4.metric("PE OI Delta", f"{int(c_data['PE OI']):,}", f"{int(pe_oi_change):+,}")

            st.write("### Open Interest (OI) Volume Shift")
            fig_oi = go.Figure(data=[
                go.Bar(name='CE OI Delta', x=['Call Options'], y=[ce_oi_change], marker_color='red'),
                go.Bar(name='PE OI Delta', x=['Put Options'], y=[pe_oi_change], marker_color='green')
            ])
            fig_oi.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_oi, use_container_width=True)

        with tab2:
            st.subheader("Fibonacci Retracement Grid (Option Premiums)")
            
            # Calculate range based on highest and lowest premium prices seen
            high_premium = float(max(c_data['CE Price'], c_data['PE Price'], p_data['CE Price'], p_data['PE Price']))
            low_premium = float(min(c_data['CE Price'], c_data['PE Price'], p_data['CE Price'], p_data['PE Price']))
            
            fib_map = calc_fibs(high_premium, low_premium)
            
            fig_f = go.Figure()
            for label, value in fib_map.items():
                fig_f.add_hline(y=value, line_dash="dash", annotation_text=f"{label}: {value:.2f}")
            
            fig_f.update_layout(template="plotly_dark", yaxis_title="Premium Price", height=500)
            st.plotly_chart(fig_f, use_container_width=True)

        with tab3:
            st.subheader("Contradiction & Tactical Execution")

            # 1. Contradiction Logic (Priority)
            st.markdown("#### 🔍 Step 1: Structural Contradiction Analysis")
            contradiction_found = False
            
            if ce_oi_change > 0 and ce_price_pct < 0:
                st.error("**CONTRADICTION DETECTED:** CE OI is rising while Prices are falling. This indicates institutional **Short Build-up (Call Writing)**. Strong resistance expected.")
                contradiction_found = True
            
            if pe_oi_change > 0 and pe_price_pct < 0:
                st.success("**CONTRADICTION DETECTED:** PE OI is rising while Prices are falling. This indicates institutional **Short Build-up (Put Writing)**. Strong floor support expected.")
                contradiction_found = True
            
            if not contradiction_found:
                st.info("No logical contradictions found. Premiums and OI are moving in standard momentum.")

            # 2. Final Strategy Formulation
            st.markdown("---")
            st.markdown("#### 🎯 Step 2: Formulation of Strategy")
            
            # Basic Logic for Strategy
            ce_action = "BUY/LONG" if (ce_oi_change < 0 and ce_price_pct > 0) else "SELL/WRITE" if (ce_oi_change > 0 and ce_price_pct < 0) else "NEUTRAL/HOLD"
            pe_action = "BUY/LONG" if (pe_oi_change < 0 and pe_price_pct > 0) else "SELL/WRITE" if (pe_oi_change > 0 and pe_price_pct < 0) else "NEUTRAL/HOLD"
            
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.info(f"**Call Option Strategy:** {ce_action}")
                st.write(f"Current PCR context: {pcr:.2f}")
            with s_col2:
                st.warning(f"**Put Option Strategy:** {pe_action}")
                st.write("Base this action on Fibonacci levels in Tab 2.")

else:
    # This shows before files are uploaded
    st.info("👈 Please use the sidebar to upload both Previous Day and Current Day CSV files to begin the analysis.")
    st.image("https://img.icons8.com/clouds/200/csv.png")
    st.markdown("""
    **Expected CSV Header Format:**
    `Strike Price, CE Price, CE OI, PE Price, PE OI`
    """)
