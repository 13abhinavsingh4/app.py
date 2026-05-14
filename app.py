import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NSE Option Analyzer", layout="centered")
st.title("📈 NSE Option Chain Analyzer")

uploaded_file = st.file_uploader("Choose NSE CSV file", type="csv")

if uploaded_file:
    try:
        # Step 1: Read the raw file to find the header row
        # We read first 20 rows to find where the data actually starts
        df_check = pd.read_csv(uploaded_file, nrows=20, header=None)
        
        header_row = None
        for i, row in df_check.iterrows():
            row_list = [str(x).upper() for x in row.tolist()]
            # A valid header row will contain BOTH 'STRIKE' and 'OI'
            if any("STRIKE" in s for s in row_list) and any("OI" in s for s in row_list):
                header_row = i
                break
        
        if header_row is None:
            st.error("Header not found. Please ensure this is a raw NSE Option Chain CSV.")
        else:
            # Step 2: Read correctly starting from the found header
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, skiprows=header_row)
            
            # Clean column names
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Find the Strike Price column (it might have spaces or dots)
            strike_col = [c for c in df.columns if "STRIKE" in c][0]
            
            # Remove the 'Total' row and empty rows
            df = df[df[strike_col].notna()]
            df = df.dropna(subset=[strike_col])
            # Filter out non-numeric strikes (like 'Total')
            df[strike_col] = pd.to_numeric(df[strike_col].astype(str).str.replace(',', ''), errors='coerce')
            df = df.dropna(subset=[strike_col])

            # Step 3: Identify CE and PE OI columns by position relative to Strike
            all_cols = list(df.columns)
            strike_idx = all_cols.index(strike_col)
            
            # Find ALL columns that contain 'OI'
            oi_cols = [c for c in all_cols if "OI" in c and "CHNG" not in c]
            
            if len(oi_cols) >= 2:
                # Typically, Call OI is the first OI column, Put OI is the last
                ce_oi_col = oi_cols[0]
                pe_oi_col = oi_cols[-1]

                # Convert to numeric
                for col in [ce_oi_col, pe_oi_col]:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

                # Calculations
                total_ce = df[ce_oi_col].sum()
                total_pe = df[pe_oi_col].sum()
                pcr = round(total_pe / total_ce, 2) if total_ce > 0 else 0

                # Mobile UI
                c1, c2 = st.columns(2)
                c1.metric("PCR (OI)", pcr)
                sentiment = "Bullish" if pcr > 1.0 else "Bearish" if pcr < 0.7 else "Neutral"
                c2.metric("Sentiment", sentiment)

                # Chart
                df_sorted = df.sort_values(by=strike_col)
                # Show only 10 strikes above and below the middle for better mobile view
                mid_point = len(df_sorted) // 2
                df_small = df_sorted.iloc[max(0, mid_point-15) : min(len(df_sorted), mid_point+15)]

                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_small[strike_col], y=df_small[ce_oi_col], name='Call OI', marker_color='#FF4B4B'))
                fig.add_trace(go.Bar(x=df_small[strike_col], y=df_small[pe_oi_col], name='Put OI', marker_color='#00CC96'))
                
                fig.update_layout(
                    barmode='group',
                    title="OI Distribution (Near ATM)",
                    xaxis_title="Strike Price",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=0, r=0, t=50, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not distinguish between Call and Put OI columns.")

    except Exception as e:
        st.error(f"Analysis failed: {e}")
