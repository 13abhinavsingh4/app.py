import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set mobile-friendly page config
st.set_page_config(page_title="NSE Option Analyzer", layout="centered")

st.title("📈 NSE Option Chain Analyzer")
st.write("Upload your NSE CSV file below to start analysis.")

uploaded_file = st.file_uploader("Choose NSE CSV file", type="csv")

if uploaded_file:
    try:
        # NSE CSVs usually have 2 rows of headers we don't need
        df = pd.read_csv(uploaded_file, skiprows=2)
        
        # Clean up column names (removes extra spaces)
        df.columns = [c.strip() for c in df.columns]
        
        # Filter out the 'Total' row if it exists
        df = df[df['STRIKE PRICE'] != 'Total']
        
        # Convert numeric columns and handle commas
        cols_to_fix = ['OI', 'CHNG IN OI', 'LTP', 'IV', 'VOLUME']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # Basic Metrics Calculation
        total_call_oi = df['OI'].iloc[0:len(df)//2].sum() # Simplified split for demo
        # In real NSE CSV, CE and PE are side by side. 
        # For this tool, we assume standard NSE format:
        ce_oi = df.filter(like='CALLS').filter(like='OI').sum().values[0]
        pe_oi = df.filter(like='PUTS').filter(like='OI').sum().values[0]
        
        pcr = round(pe_oi / ce_oi, 2) if ce_oi > 0 else 0

        # UI Layout for Mobile
        col1, col2 = st.columns(2)
        with col1:
            st.metric("PCR (OI)", pcr)
        with col2:
            sentiment = "Bullish" if pcr > 1 else "Bearish" if pcr < 0.7 else "Neutral"
            st.metric("Sentiment", sentiment)

        # Support and Resistance
        # Finding strike with max OI in Calls (Resistance) and Puts (Support)
        # Note: This logic assumes column naming conventions in NSE CSV
        st.subheader("Key Levels")
        st.info(f"📍 **Support:** Look for high Put OI strikes.")
        st.error(f"📍 **Resistance:** Look for high Call OI strikes.")

        # OI Visualization
        st.subheader("OI Distribution")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['STRIKE PRICE'], y=df.filter(like='CALLS').filter(like='OI').iloc[:,0], name='Call OI', marker_color='red'))
        fig.add_trace(go.Bar(x=df['STRIKE PRICE'], y=df.filter(like='PUTS').filter(like='OI').iloc[:,0], name='Put OI', marker_color='green'))
        
        fig.update_layout(barmode='group', xaxis_title="Strike Price", yaxis_title="Open Interest", 
                          margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}. Please ensure you are uploading a valid NSE Option Chain CSV.")
else:
    st.info("Awaiting CSV upload. Download the 'Option Chain (CSV)' from the NSE website.")