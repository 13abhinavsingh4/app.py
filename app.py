import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NSE Option Analyzer", layout="centered")
st.title("📈 NSE Option Chain Analyzer")

uploaded_file = st.file_uploader("Choose NSE CSV file", type="csv")

if uploaded_file:
    try:
        # Step 1: Read the raw file to find where the actual data starts
        raw_data = pd.read_csv(uploaded_file)
        
        # Look for the row that contains 'Strike Price' or 'STRIKE PRICE'
        header_row = 0
        for i, row in raw_data.iterrows():
            row_str = row.astype(str).str.upper().tolist()
            if any("STRIKE" in s for s in row_str):
                header_row = i + 1
                break
        
        # Step 2: Re-read the file from that correct row
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, skiprows=header_row)
        df.columns = [c.strip().upper() for c in df.columns] # Normalize names
        
        # Step 3: Find the Strike Price column even if name varies
        strike_col = [c for c in df.columns if "STRIKE" in c][0]
        df = df[df[strike_col].notna()]
        df = df[df[strike_col].astype(str).str.upper() != 'TOTAL']

        # Step 4: Numeric cleaning
        for col in df.columns:
            if any(x in col for x in ['OI', 'CHNG', 'LTP', 'IV', 'VOLUME']):
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # Step 5: Logic for Calls and Puts based on column position
        # Standard NSE: Calls on left, Strike in middle, Puts on right
        mid_idx = df.columns.get_loc(strike_col)
        ce_df = df.iloc[:, :mid_idx]
        pe_df = df.iloc[:, mid_idx+1:]
        
        ce_oi_total = ce_df.filter(like='OI').iloc[:, 0].sum()
        pe_oi_total = pe_df.filter(like='OI').iloc[:, 0].sum()
        pcr = round(pe_oi_total / ce_oi_total, 2) if ce_oi_total > 0 else 0

        # UI
        c1, c2 = st.columns(2)
        c1.metric("PCR (OI)", pcr)
        c2.metric("Sentiment", "Bullish" if pcr > 1.1 else "Bearish" if pcr < 0.7 else "Neutral")

        # OI Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df[strike_col], y=ce_df.filter(like='OI').iloc[:,0], name='Call OI', marker_color='red'))
        fig.add_trace(go.Bar(x=df[strike_col], y=pe_df.filter(like='OI').iloc[:,0], name='Put OI', marker_color='green'))
        fig.update_layout(barmode='group', title="Open Interest Distribution", xaxis_title="Strike Price", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
        st.write("Tip: Download the CSV fresh from the NSE 'Option Chain' page.")