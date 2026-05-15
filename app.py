import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. SIDEBAR - FILE UPLOADERS (TOP PRIORITY)
# ---------------------------------------------------------
st.sidebar.header("Step 1: Upload Data")
file_p = st.sidebar.file_uploader("Upload Previous Day CSV", type=["csv"])
file_c = st.sidebar.file_uploader("Upload Current Day CSV", type=["csv"])

# ---------------------------------------------------------
# 2. CORE LOGIC FUNCTIONS
# ---------------------------------------------------------
def get_data(file):
    if file is None:
        return None
    df = pd.read_csv(file)
    df.columns = [str(c).strip() for c in df.columns]
    cols = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.dropna(subset=['Strike Price'])

def get_fibs(hi, lo):
    d = hi - lo
    if d == 0: d = 1.0
    return {
        "161.8%": lo + (d * 1.618),
        "100.0%": hi,
        "61.8%": lo + (d * 0.618),
        "50.0%": lo + (d * 0.5),
        "38.2%": lo + (d * 0.382),
        "23.6%": lo + (d * 0.236),
        "0.0%": lo
    }

# ---------------------------------------------------------
# 3. MAIN INTERFACE
# ---------------------------------------------------------
st.title("📊 Option Dynamics Analyzer")

if file_p and file_c:
    df_prev = get_data(file_p)
    df_curr = get_data(file_c)

    if df_prev is not None and df_curr is not None:
        # Match Strikes
        common = sorted(list(set(df_prev['Strike Price']).intersection(set(df_curr['Strike Price']))))
        
        if not common:
            st.error("Strikes do not match between files.")
        else:
            strike = st.sidebar.selectbox("Step 2: Select Strike", common)
            
            # Get Rows
            rp = df_prev[df_prev['Strike Price'] == strike].iloc[0]
            rc = df_curr[df_curr['Strike Price'] == strike].iloc[0]

            # Delta Calcs
            ce_oi_d = rc['CE OI'] - rp['CE OI']
            pe_oi_d = rc['PE OI'] - rp['PE OI']
            
            ce_pct = ((rc['CE Price'] - rp['CE Price']) / rp['CE Price'] * 100) if rp['CE Price'] != 0 else 0
            pe_pct = ((rc['PE Price'] - rp['PE Price']) / rp['PE Price'] * 100) if rp['PE Price'] != 0 else 0

            # Tabs
            t1, t2, t3 = st.tabs(["Dashboard", "Fibonacci", "Strategy"])

            with t1:
                st.subheader(f"Metrics for Strike {strike}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("CE Price", f"{rc['CE Price']}", f"{ce_pct:.2f}%")
                c2.metric("CE OI Change", f"{int(rc['CE OI']):,}", f"{int(ce_oi_d):+,}")
                c3.metric("PE Price", f"{rc['PE Price']}", f"{pe_pct:.2f}%")
                c4.metric("PE OI Change", f"{int(rc['PE OI']):,}", f"{int(pe_oi_d):+,}")

                fig = go.Figure(data=[
                    go.Bar(name='CE OI Delta', x=['CE'], y=[ce_oi_d], marker_color='red'),
                    go.Bar(name='PE OI Delta', x=['PE'], y=[pe_oi_d], marker_color='green')
                ])
                fig.update_layout(template="plotly_dark", title="OI Shift")
                st.plotly_chart(fig, use_container_width=True)

            with t2:
                h = float(max(rc['CE Price'], rc['PE Price']))
                l = float(min(rc['CE Price'], rc['PE Price']))
                levels = get_fibs(h, l)
                
                fig_f = go.Figure()
                for k, v in levels.items():
                    fig_f.add_hline(y=v, line_dash="dash", annotation_text=k)
                fig_f.update_layout(template="plotly_dark", title="Fibonacci Premium Levels")
                st.plotly_chart(fig_f, use_container_width=True)

            with t3:
                st.subheader("Strategy Formulation")
                if ce_oi_d > 0 and ce_pct < 0:
                    st.error("CE SHORT BUILD-UP: Institutional Selling/Resistance.")
                if pe_oi_d > 0 and pe_pct < 0:
                    st.success("PE SHORT BUILD-UP: Institutional Support/Buying.")
                
                ce_s = "BUY" if (ce_oi_d < 0 and ce_pct > 0) else "SELL" if ce_oi_d > 0 else "HOLD"
                pe_s = "BUY" if (pe_oi_d < 0 and pe_pct > 0) else "SELL" if pe_oi_d > 0 else "HOLD"
                st.write(f"**Action CE:** {ce_s} | **Action PE:** {pe_s}")

else:
    st.info("👈 Please use the sidebar on the left to upload your CSV files.")
