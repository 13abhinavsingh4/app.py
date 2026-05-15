import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. SIDEBAR SETUP (UPLOADER FIRST)
# -----------------------------------------------------------------------------
st.sidebar.title("📁 Data Upload Center")
# These must be at the top level to ensure they appear even if other logic fails
uploaded_prev = st.sidebar.file_uploader("1. Previous Day CSV", type=["csv"])
uploaded_curr = st.sidebar.file_uploader("2. Current Day CSV", type=["csv"])

# -----------------------------------------------------------------------------
# 2. APP CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Option Dynamics Pro",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def load_and_validate(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        # Standardize column names
        df.columns = [str(c).strip() for c in df.columns]
        
        required = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        if not all(col in df.columns for col in required):
            st.sidebar.error(f"Error: {file.name} missing required columns.")
            return None
            
        # Convert to numeric
        for col in required:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna(subset=['Strike Price'])
    except Exception as e:
        st.sidebar.error(f"Load Error: {e}")
        return None

def get_fib_grid(high, low):
    diff = high - low
    if diff == 0: diff = 1.0
    # Explicit dictionary build
    levels = {}
    levels["161.8% Extension"] = low + (diff * 1.618)
    levels["100.0% High"] = high
    levels["61.8% Golden Ratio"] = low + (diff * 0.618)
    levels["50.0% Midpoint"] = low + (diff * 0.5)
    levels["38.2% Retracement"] = low + (diff * 0.382)
    levels["23.6% Retracement"] = low + (diff * 0.236)
    levels["0.0% Low"] = low
    return levels

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD LOGIC
# -----------------------------------------------------------------------------
st.title("🛡️ Institutional Option Dynamics & Strategy")

if uploaded_prev and uploaded_curr:
    data_prev = load_and_validate(uploaded_prev)
    data_curr = load_and_validate(uploaded_curr)

    if data_prev is not None and data_curr is not None:
        # Match Strike Prices
        strikes = sorted(list(set(data_prev['Strike Price']).intersection(set(data_curr['Strike Price']))))

        if not strikes:
            st.error("No overlapping strike prices found between CSVs.")
        else:
            # Selection UI
            st.sidebar.markdown("---")
            target_strike = st.sidebar.selectbox("🎯 Select Strike Price", strikes)

            # Extract data
            row_p = data_prev[data_prev['Strike Price'] == target_strike].iloc[0]
            row_c = data_curr[data_curr['Strike Price'] == target_strike].iloc[0]

            # Calculations
            ce_oi_delta = row_c['CE OI'] - row_p['CE OI']
            pe_oi_delta = row_c['PE OI'] - row_p['PE OI']
            
            def safe_pct(curr, prev):
                return ((curr - prev) / prev * 100) if prev != 0 else 0

            ce_price_chg = safe_pct(row_c['CE Price'], row_p['CE Price'])
            pe_price_chg = safe_pct(row_c['PE Price'], row_p['PE Price'])

            # Dashboard Tabs
            tab1, tab2, tab3 = st.tabs(["📊 Performance", "🌀 Fibonacci Grid", "🎯 Strategy & Contradictions"])

            with tab1:
                st.subheader(f"Strike {target_strike} Comparative Metrics")
                c1, c2, c3, c4 = st.columns(4)
                
                # Using native st.metric - avoids HTML parsing errors
                c1.metric("CE Price", f"{row_c['CE Price']}", f"{ce_price_chg:.2f}%")
                c2.metric("CE OI Change", f"{int(row_c['CE OI']):,}", f"{int(ce_oi_delta):+,}")
                c3.metric("PE Price", f"{row_c['PE Price']}", f"{pe_price_chg:.2f}%")
                c4.metric("PE OI Change", f"{int(row_c['PE OI']):,}", f"{int(pe_oi_delta):+,}")

                st.write("### Open Interest (OI) Structural Delta")
                fig_oi = go.Figure(data=[
                    go.Bar(name='Call OI Change', x=['Calls'], y=[ce_oi_delta], marker_color='red'),
                    go.Bar(name='Put OI Change', x=['Puts'], y=[pe_oi_delta], marker_color='green')
                ])
                fig_oi.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_oi, use_container_width=True)

            with tab2:
                st.subheader("Fibonacci Retracement (Option Premium Scale)")
                # Find range
                hi = float(max(row_c['CE Price'], row_c['PE Price'], row_p['CE Price'], row_p['PE Price']))
                lo = float(min(row_c['CE Price'], row_c['PE Price'], row_p['CE Price'], row_p['PE Price']))
                
                fibs = get_fib_grid(hi, lo)
                fig_f = go.Figure()
                for label, val in fibs.items():
                    fig_f.add_hline(y=val, line_dash="dash", annotation_text=f"{label}: {val:.2f}")
                
                fig_f.update_layout(template="plotly_dark", yaxis_title="Premium Value")
                st.plotly_chart(fig_f, use_container_width=True)

            with tab3:
                st.subheader("Market Sentiment & Strategy")
                
                # 1. Contradiction Logic
                st.markdown("### 🔍 Logical Analysis")
                has_contradiction = False
                
                if ce_oi_delta > 0 and ce_price_chg < 0:
                    st.error("⚠️ CE SHORT BUILD-UP: OI Rising while Price falls. Strong resistance/selling detected.")
                    has_contradiction = True
                
                if pe_oi_delta > 0 and pe_price_chg < 0:
                    st.success("⚠️ PE SHORT BUILD-UP: OI Rising while Price falls. Strong support floor detected.")
                    has_contradiction = True
                    
                if not has_contradiction:
                    st.info("No structural contradictions found. Data reflects standard directional momentum.")

                # 2. Strategy Matrix
                st.divider()
                st.markdown("### 🎯 Strategic Execution")
                ce_s = "BUY/LONG" if (ce_oi_delta < 0 and ce_price_chg > 0) else "SELL/WRITE" if (ce_oi_delta > 0) else "HOLD"
                pe_s = "BUY/LONG" if (pe_oi_delta < 0 and pe_price_chg > 0) else "SELL/WRITE" if (pe_oi_delta > 0) else "HOLD"
                
                s1, s2 = st.columns(2)
                s1.info(f"**Call Strategy:** {ce_s}")
                s2.warning(f"**Put Strategy:** {pe_s}")

else:
    st.warning("👈 Please upload both CSV files in the sidebar to activate the dashboard.")
    st.info("Ensure CSV files have columns: Strike Price, CE Price, CE OI, PE Price, PE OI")
