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
# 2. Logic Functions
# -----------------------------------------------------------------------------
def clean_and_load(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        req = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        
        if not all(col in df.columns for col in req):
            st.error(f"Required columns missing in {file.name}")
            return None
            
        for col in req:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna(subset=['Strike Price'])
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return None

def calc_fibs(high, low):
    span = high - low
    levels = {
        "161.8% Ext": low + (span * 1.618),
        "100% High": high,
        "61.8% Golden": low + (span * 0.618),
        "50.0% Mid": low + (span * 0.5),
        "38.2%": low + (span * 0.382),
        "23.6%": low + (span * 0.236),
        "0% Low": low
    }
    return levels

# -----------------------------------------------------------------------------
# 3. Application UI
# -----------------------------------------------------------------------------
st.title("🛡️ Institutional Option Dynamics")

with st.sidebar:
    st.header("Data Upload")
    prev_csv = st.file_uploader("Upload Previous Day", type="csv")
    curr_csv = st.file_uploader("Upload Current Day", type="csv")

if prev_csv and curr_csv:
    df_p = clean_and_load(prev_csv)
    df_c = clean_and_load(curr_csv)

    if df_p is not None and df_c is not None:
        common_strikes = sorted(list(set(df_p['Strike Price']).intersection(set(df_c['Strike Price']))))

        if not common_strikes:
            st.error("No overlapping strike prices found.")
            st.stop()

        target = st.sidebar.selectbox("Select Strike Price", common_strikes)

        p_row = df_p[df_p['Strike Price'] == target].iloc[0]
        c_row = df_c[df_c['Strike Price'] == target].iloc[0]

        # Calculations
        ce_oi_delta = c_row['CE OI'] - p_row['CE OI']
        pe_oi_delta = c_row['PE OI'] - p_row['PE OI']
        
        def safe_pct(c, p):
            return ((c - p) / p * 100) if p and p != 0 else 0

        ce_p_chg = safe_pct(c_row['CE Price'], p_row['CE Price'])
        pe_p_chg = safe_pct(c_row['PE Price'], p_row['PE Price'])

        tab1, tab2, tab3 = st.tabs(["Dashboard", "Fibonacci Matrix", "Strategy Engine"])

        with tab1:
            st.subheader(f"Strike {target} Dynamics")
            # Using native st.metric which is much safer across Python versions
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("CE Price", f"{c_row['CE Price']}", f"{ce_p_chg:.2f}%")
            m_col2.metric("CE OI Delta", f"{c_row['CE OI']:,}", f"{ce_oi_delta:+,}")
            m_col3.metric("PE Price", f"{c_row['PE Price']}", f"{pe_p_chg:.2f}%")
            m_col4.metric("PE OI Delta", f"{c_row['PE OI']:,}", f"{pe_oi_delta:+,}")

            fig = go.Figure(data=[
                go.Bar(name='CE Delta', x=['Calls'], y=[ce_oi_delta], marker_color='#ef4444'),
                go.Bar(name='PE Delta', x=['Puts'], y=[pe_oi_delta], marker_color='#22c55e')
            ])
            fig.update_layout(template="plotly_dark", title="Net OI Shift")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Fibonacci Retracement Grid")
            h = float(max(c_row['CE Price'], c_row['PE Price']))
            l = float(min(c_row['CE Price'], c_row['PE Price']))
            if h == l: h += 1.0
            
            fibs = calc_fibs(h, l)
            fig_f = go.Figure()
            for lab, val in fibs.items():
                fig_f.add_hline(y=val, line_dash="dash", annotation_text=lab)
            fig_f.update_layout(template="plotly_dark", yaxis_title="Premium Value")
            st.plotly_chart(fig_f, use_container_width=True)

        with tab3:
            st.subheader("Tactical Logic")
            
            # Contradictions
            with st.expander("Structural Contradictions", expanded=True):
                if ce_oi_delta > 0 and ce_p_chg < 0:
                    st.error("🚨 CE SHORT BUILDUP: Professional writers dominating resistance.")
                if pe_oi_delta > 0 and pe_p_chg < 0:
                    st.success("🚨 PE SHORT BUILDUP: Support floor being cemented by writers.")
                if not (ce_oi_delta > 0 and ce_p_chg < 0) and not (pe_oi_delta > 0 and pe_p_chg < 0):
                    st.info("No logical contradictions found.")

            # Strategy
            ce_s = "BUY" if (ce_oi_delta < 0 and ce_p_chg > 0) else "SELL" if ce_oi_delta > 0 else "HOLD"
            pe_s = "BUY" if (pe_oi_delta < 0 and pe_p_chg > 0) else "SELL" if pe_oi_delta > 0 else "HOLD"
            
            s_c1, s_c2 = st.columns(2)
            s_c1.info(f"**Call Strategy:** {ce_s}")
            s_c2.warning(f"**Put Strategy:** {pe_s}")

else:
    st.info("Upload CSV files to begin.")
