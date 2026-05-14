import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NSE Option Analyzer", layout="centered")
st.title("📈 NSE Option Chain Analyzer")

uploaded_file = st.file_uploader("Choose NSE CSV file", type="csv")

if uploaded_file:
    try:
        # Step 1: Read everything as strings to avoid errors
        df_raw = pd.read_csv(uploaded_file, header=None).astype(str)
        
        # Step 2: Find the real data start
        # We look for the first row where a column has a number (the Strike Price)
        data_start_row = None
        strike_col_idx = None
        
        for i in range(len(df_raw)):
            row = df_raw.iloc[i].str.replace(',', '').str.strip()
            # Convert row to numeric, errors become NaN
            numeric_row = pd.to_numeric(row, errors='coerce')
            # The Strike Price is usually in the middle (index 10-12)
            # We look for a row that has at least 5 numeric values
            if numeric_row.count() > 5:
                data_start_row = i
                # Strike price is usually the most consistent large number in the middle
                strike_col_idx = numeric_row.idxmax() 
                break

        if data_start_row is None:
            st.error("Could not find trading data. Please ensure this is the 'Option Chain' CSV from NSE.")
        else:
            # Step 3: Extract the data table
            df_final = df_raw.iloc[data_start_row:].copy()
            
            # Clean commas and convert to numbers
            for col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col].str.replace(',', ''), errors='coerce').fillna(0)

            # In NSE CSV: Call OI is index 1, Put OI is index -2 (usually)
            # But let's be safer: OI columns are the ones with the highest values after Strike
            ce_oi = df_final.iloc[:, 1] # Calls are always near the left
            pe_oi = df_final.iloc[:, -2] # Puts are always near the right
            strikes = df_final[strike_col_idx]

            # Calculations
            total_ce = ce_oi.sum()
            total_pe = pe_oi.sum()
            pcr = round(total_pe / total_ce, 2) if total_ce > 0 else 0

            # UI
            c1, c2 = st.columns(2)
            c1.metric("PCR (OI)", pcr)
            sentiment = "Bullish" if pcr > 1.0 else "Bearish" if pcr < 0.7 else "Neutral"
            c2.metric("Sentiment", sentiment)

            # Chart - Zooming in on the active strikes
            # We filter out very small strikes to find the current market price
            active_strikes = df_final[df_final[strike_col_idx] > 0]
            mid_idx = len(active_strikes) // 2
            df_zoom = active_strikes.iloc[max(0, mid_idx-15) : min(len(active_strikes), mid_idx+15)]

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_zoom[strike_col_idx], y=df_zoom.iloc[:, 1], name='Call OI', marker_color='#FF4B4B'))
            fig.add_trace(go.Bar(x=df_zoom[strike_col_idx], y=df_zoom.iloc[:, -2], name='Put OI', marker_color='#00CC96'))
            
            fig.update_layout(barmode='group', title="OI Distribution", xaxis_title="Strike Price",
                              legend=dict(orientation="h", y=1.1), margin=dict(l=0, r=0, t=50, b=0))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Something went wrong: {e}")
