import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NSE Option Analyzer", layout="centered")
st.title("📈 NSE Option Chain Analyzer")

uploaded_file = st.file_uploader("Choose NSE CSV file", type="csv")

if uploaded_file:
    try:
        # Step 1: Read the raw file
        df_raw = pd.read_csv(uploaded_file)
        
        # Step 2: Find the row where the actual table headers start
        # We look for the row containing 'Strike Price'
        header_row_index = None
        for i in range(len(df_raw)):
            row_values = df_raw.iloc[i].astype(str).str.upper().tolist()
            if any("STRIKE" in s for s in row_values):
                header_row_index = i
                break
        
        if header_row_index is None:
            st.error("Could not find 'Strike Price' in this file. Please use a standard NSE CSV.")
        else:
            # Re-read the dataframe correctly
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, skiprows=header_row_index + 1)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Clean 'TOTAL' row and empty strikes
            strike_col = [c for c in df.columns if "STRIKE" in c][0]
            df = df[df[strike_col].notna()]
            df = df[df[strike_col].astype(str).str.upper().str.contains("TOTAL") == False]

            # Step 3: Identify CE and PE OI columns
            # NSE format: CALLS are usually on the left of Strike, PUTS on the right
            cols = list(df.columns)
            strike_idx = cols.index(strike_col)
            
            # CE OI is the 'OI' column found BEFORE the strike price
            ce_oi_col = [c for c in cols[:strike_idx] if "OI" in c and "CHNG" not in c][0]
            # PE OI is the 'OI' column found AFTER the strike price
            pe_oi_col = [c for c in cols[strike_idx:] if "OI" in c and "CHNG" not in c][0]

            # Convert to numbers
            df[ce_oi_col] = pd.to_numeric(df[ce_oi_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df[pe_oi_col] = pd.to_numeric(df[pe_oi_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df[strike_col] = pd.to_numeric(df[strike_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

            # Metrics
            total_ce_oi = df[ce_oi_col].sum()
            total_pe_oi = df[pe_oi_col].sum()
            pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0

            c1, c2 = st.columns(2)
            c1.metric("PCR (OI)", pcr)
            c2.metric("Sentiment", "Bullish" if pcr > 1.0 else "Bearish" if pcr < 0.7 else "Neutral")

            # Chart
            # Focus on strikes around the middle (ATM) for better visibility on mobile
            df_chart = df.sort_values(by=strike_col)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_chart[strike_col], y=df_chart[ce_oi_col], name='Call OI', marker_color='#EF553B'))
            fig.add_trace(go.Bar(x=df_chart[strike_col], y=df_chart[pe_oi_col], name='Put OI', marker_color='#00CC96'))
            
            fig.update_layout(
                barmode='group',
                title="Open Interest by Strike",
                xaxis_title="Strike Price",
                yaxis_title="OI Contracts",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=50, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Analysis Error: {e}")
        st.info("Check: Are you uploading the full Option Chain CSV from the NSE 'Download' button?")

else:
    st.info("Please upload an NSE Index or Stock Option Chain CSV file.")
