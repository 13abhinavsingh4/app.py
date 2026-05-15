import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="NSE Option Dynamics", layout="wide")

st.sidebar.header("📥 1. NSE Data Upload")
file_p = st.sidebar.file_uploader("Upload Previous Day NSE CSV", type=["csv"])
file_c = st.sidebar.file_uploader("Upload Current Day NSE CSV", type=["csv"])

# ---------------------------------------------------------
# 2. NSE-SPECIFIC LOADING ENGINE
# ---------------------------------------------------------
def load_nse_csv(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        # Clean column names to handle NSE export quirks
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # KEY RECTIFICATION: NSE specific mapping based on your screenshot
        # We find columns by checking common NSE keywords
        mapped_df = pd.DataFrame()
        
        # 1. Strike Price
        strike_col = next((c for c in df.columns if 'STRIKE' in c), None)
        # 2. Price (NSE uses LTP - Last Traded Price)
        price_col = next((c for c in df.columns if 'LTP' in c or 'CLOSE' in c), None)
        # 3. Open Interest
        oi_col = next((c for c in df.columns if 'OPEN INT' in c or 'OI' in c), None)

        if not all([strike_col, price_col, oi_col]):
            st.error(f"Missing essential NSE columns in {file.name}. Found: {list(df.columns)}")
            return None

        mapped_df['STRIKE'] = pd.to_numeric(df[strike_col], errors='coerce')
        mapped_df['PRICE'] = pd.to_numeric(df[price_col], errors='coerce')
        mapped_df['OI'] = pd.to_numeric(df[oi_col], errors='coerce')
        
        # Determine if this file is CE or PE data (usually in filename or OPTION TYPE column)
        opt_type = ""
        if 'OPTION TYPE' in df.columns:
            opt_type = str(df['OPTION TYPE'].iloc[0]).upper()
        
        # Return structured data + the detected type
        return mapped_df.dropna(subset=['STRIKE']), opt_type
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")
        return None

# ---------------------------------------------------------
# 3. MAIN DASHBOARD
# ---------------------------------------------------------
st.title("📊 NSE Option Chain Analysis")

if file_p and file_c:
    # Load data and detect if it's CE or PE
    df_p, type_p = load_nse_csv(file_p)
    df_c, type_c = load_nse_csv(file_c)

    if df_p is not None and df_c is not None:
        # Match Strikes
        common_strikes = sorted(list(set(df_p['STRIKE']).intersection(set(df_c['STRIKE']))))
        
        if not common_strikes:
            st.warning("Strike Price mismatch. Ensure both files belong to the same expiry/symbol.")
        else:
            strike = st.sidebar.selectbox("🎯 2. Select Strike Price", common_strikes)
            
            # Extract row data
            row_p = df_p[df_p['STRIKE'] == strike].iloc[0]
            row_c = df_c[df_c['STRIKE'] == strike].iloc[0]

            # Calculations
            oi_change = row_c['OI'] - row_p['OI']
            price_change_pct = ((row_c['PRICE'] - row_p['PRICE']) / row_p['PRICE'] * 100) if row_p['PRICE'] != 0 else 0

            # UI Display
            st.info(f"Analyzing **{type_c}** data for Strike **{strike}**")
            
            col1, col2 = st.columns(2)
            col1.metric("LTP (Current)", f"₹{row_c['PRICE']}", f"{price_change_pct:.2f}%")
            col2.metric("OI Delta", f"{int(row_c['OI']):,}", f"{int(oi_change):+,}")

            # Fibonacci Levels based on Price range
            st.subheader("🌀 Fibonacci Retracement (LTP)")
            hi, lo = float(max(row_c['PRICE'], row_p['PRICE'])), float(min(row_c['PRICE'], row_p['PRICE']))
            diff = hi - lo if hi != lo else 1.0
            fib_levels = {
                "100% (High)": hi,
                "61.8%": lo + (diff * 0.618),
                "50.0%": lo + (diff * 0.5),
                "38.2%": lo + (diff * 0.382),
                "0% (Low)": lo
            }

            fig = go.Figure()
            for label, val in fib_levels.items():
                fig.add_hline(y=val, line_dash="dash", annotation_text=label)
            fig.update_layout(template="plotly_dark", title=f"Premium Fibonacci Grid: {strike}")
            st.plotly_chart(fig, use_container_width=True)

            # Strategy Logic
            st.subheader("🎯 Tactical View")
            if oi_change > 0 and price_change_pct < 0:
                st.error("🚨 SHORT BUILD-UP: Institutional writing/selling detected.")
            elif oi_change < 0 and price_change_pct > 0:
                st.success("🚀 SHORT COVERING: Sellers exiting, potential bullish move.")
            elif oi_change > 0 and price_change_pct > 0:
                st.info("📈 LONG BUILD-UP: Aggressive buying detected.")
            else:
                st.write("Neutral momentum or distribution phase.")

else:
    st.info("👈 Upload NSE CSV files in the sidebar. The app will automatically detect Strike, LTP, and OI.")

# ---------------------------------------------------------
# 4. DEBUG SECTION (Hidden by default)
# ---------------------------------------------------------
with st.expander("🛠️ CSV Debugger (Click if data doesn't load)"):
    if file_p: st.write("Prev File Columns:", list(pd.read_csv(file_p).columns))
    if file_c: st.write("Curr File Columns:", list(pd.read_csv(file_c).columns))
