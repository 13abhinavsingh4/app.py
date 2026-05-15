import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. CORE CONFIG & SIDEBAR UPLOAD
# ---------------------------------------------------------
st.set_page_config(page_title="Option Dynamics Pro", layout="wide")

st.sidebar.header("📥 1. Upload Data")
file_p = st.sidebar.file_uploader("Previous Day CSV", type=["csv"])
file_c = st.sidebar.file_uploader("Current Day CSV", type=["csv"])

# ---------------------------------------------------------
# 2. ROBUST DATA LOADING ENGINE
# ---------------------------------------------------------
def smart_load(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        # Clean column names: uppercase and remove spaces/special chars
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Mapping logic: Find best fit for required data
        mapping = {}
        cols = df.columns.tolist()
        
        def find_col(keywords, default):
            for k in keywords:
                for c in cols:
                    if k in c: return c
            return default

        mapping['STRIKE'] = find_col(['STRIKE', 'PRICE'], 'STRIKE PRICE')
        mapping['CE_P'] = find_col(['CE PRICE', 'CE_P', 'CALL PRICE'], 'CE PRICE')
        mapping['CE_OI'] = find_col(['CE OI', 'CALL OI', 'CE_OI'], 'CE OI')
        mapping['PE_P'] = find_col(['PE PRICE', 'PE_P', 'PUT PRICE'], 'PE PRICE')
        mapping['PE_OI'] = find_col(['PE OI', 'PUT OI', 'PE_OI'], 'PE OI')

        # Check if mapped columns actually exist in DF
        for key, col_name in mapping.items():
            if col_name not in df.columns:
                st.error(f"Could not find column for **{key}** in {file.name}. Found columns: {cols}")
                return None

        # Create standardized dataframe
        new_df = pd.DataFrame()
        new_df['STRIKE'] = pd.to_numeric(df[mapping['STRIKE']], errors='coerce')
        new_df['CE_P'] = pd.to_numeric(df[mapping['CE_P']], errors='coerce')
        new_df['CE_OI'] = pd.to_numeric(df[mapping['CE_OI']], errors='coerce')
        new_df['PE_P'] = pd.to_numeric(df[mapping['PE_P']], errors='coerce')
        new_df['PE_OI'] = pd.to_numeric(df[mapping['PE_OI']], errors='coerce')
        
        return new_df.dropna(subset=['STRIKE'])
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")
        return None

# ---------------------------------------------------------
# 3. ANALYSIS INTERFACE
# ---------------------------------------------------------
st.title("🛡️ Institutional Option Dynamics")

if file_p and file_c:
    df_prev = smart_load(file_p)
    df_curr = smart_load(file_c)

    if df_prev is not None and df_curr is not None:
        # Get matching strikes
        common = sorted(list(set(df_prev['STRIKE']).intersection(set(df_curr['STRIKE']))))
        
        if not common:
            st.warning("No matching Strike Prices found between files. Check your CSV data.")
        else:
            strike = st.sidebar.selectbox("🎯 2. Select Strike", common)
            
            # Extract specific strike data
            rp = df_prev[df_prev['STRIKE'] == strike].iloc[0]
            rc = df_curr[df_curr['STRIKE'] == strike].iloc[0]

            # Calculations
            ce_oi_delta = rc['CE_OI'] - rp['CE_OI']
            pe_oi_delta = rc['PE_OI'] - rp['PE_OI']
            
            def get_pct(c, p):
                return ((c - p) / p * 100) if p and p != 0 else 0

            ce_pct = get_pct(rc['CE_P'], rp['CE_P'])
            pe_pct = get_pct(rc['PE_P'], rp['PE_P'])

            # Dashboard UI
            t1, t2, t3 = st.tabs(["📊 Comparison", "🌀 Fibonacci", "🎯 Strategy"])

            with t1:
                st.subheader(f"Data for Strike: {strike}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("CE Price", f"{rc['CE_P']}", f"{ce_pct:.2f}%")
                c2.metric("CE OI Change", f"{int(rc['CE_OI']):,}", f"{int(ce_oi_delta):+,}")
                c3.metric("PE Price", f"{rc['PE_P']}", f"{pe_pct:.2f}%")
                c4.metric("PE OI Change", f"{int(rc['PE_OI']):,}", f"{int(pe_oi_delta):+,}")

                fig = go.Figure(data=[
                    go.Bar(name='Call OI Change', x=['CE'], y=[ce_oi_delta], marker_color='red'),
                    go.Bar(name='Put OI Change', x=['PE'], y=[pe_oi_delta], marker_color='green')
                ])
                fig.update_layout(template="plotly_dark", title="Net Open Interest Shift")
                st.plotly_chart(fig, use_container_width=True)

            with t2:
                # Fibonacci Calc
                hi = float(max(rc['CE_P'], rc['PE_P'], 1.0))
                lo = float(min(rc['CE_P'], rc['PE_P'], 0.5))
                diff = hi - lo
                levels = {
                    "161.8%": lo + (diff * 1.618),
                    "100.0%": hi,
                    "61.8%": lo + (diff * 0.618),
                    "50.0%": lo + (diff * 0.5),
                    "38.2%": lo + (diff * 0.382),
                    "0.0%": lo
                }
                
                fig_f = go.Figure()
                for k, v in levels.items():
                    fig_f.add_hline(y=v, line_dash="dash", annotation_text=k)
                fig_f.update_layout(template="plotly_dark", title="Fibonacci Premium Levels")
                st.plotly_chart(fig_f, use_container_width=True)

            with t3:
                st.subheader("Logic & Strategy")
                # Contradiction Logic
                if ce_oi_delta > 0 and ce_pct < 0:
                    st.error("⚠️ CE SHORT BUILD-UP (Selling Resistance)")
                if pe_oi_delta > 0 and pe_pct < 0:
                    st.success("⚠️ PE SHORT BUILD-UP (Support Buying)")
                
                ce_s = "BUY" if (ce_oi_delta < 0 and ce_pct > 0) else "SELL" if ce_oi_delta > 0 else "HOLD"
                pe_s = "BUY" if (pe_oi_delta < 0 and pe_pct > 0) else "SELL" if pe_oi_delta > 0 else "HOLD"
                
                st.info(f"**Final View:** CE Action: {ce_s} | PE Action: {pe_s}")

else:
    st.info("👈 Upload your Previous and Current day CSV files in the sidebar to start.")
