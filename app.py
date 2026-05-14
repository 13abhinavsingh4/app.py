import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NSE Option Analyzer", layout="centered")
st.title("📈 NSE Option Chain Analyzer")

uploaded_file = st.file_uploader("Choose NSE CSV file", type="csv")

if uploaded_file:
    try:
        # Step 1: Find the header row
        df_raw = pd.read_csv(uploaded_file, nrows=25, header=None)
        header_row = None
        for i, row in df_raw.iterrows():
            row_vals = [str(x).upper() for x in row.tolist()]
            if any("STRIKE" in s for s in row_vals) and any("OI" in s or "OPEN" in s for s in row_vals):
                header_row = i
                break
        
        if header_row is None:
            st.error("Header not found. Please ensure this is a raw NSE Option Chain CSV.")
        else:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, skiprows=header_row)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Identify the Strike column
            strike_col = [c for c in df.columns if "STRIKE" in c][0]
            
            # Clean numeric data for the whole dataframe
            def clean_num(val):
                return pd.to_numeric(str(val).replace(',', ''), errors='coerce')

            df[strike_col] = df[strike_col].apply(clean_num)
            df = df.dropna(subset=[strike_col]) # Removes 'Total' and junk rows

            # Step 2: Robust OI Column Detection
            all_cols = list(df.columns)
            strike_idx = all_cols.index(strike_col)
            
            # Find all columns that look like Open Interest
            potential_oi_cols = [c for c in all_cols if ("OI" in c or "OPEN" in c) and "CHNG" not in c and "NET" not in c]
            
            # Separate them based on side of the Strike Price
            ce_oi_options = [c for c in potential_oi_cols if all_cols.index(c) < strike_idx]
            pe_oi_options = [c for c in potential_oi_cols if all_cols.index(c) > strike_idx]

            if ce_oi_options and pe_oi_options:
                ce_oi_col = ce_oi_options[0]
                pe_oi_col = pe_oi_options[0]

                df[ce_oi_col] = df[ce_oi_col].apply(clean_num).fillna(0)
                df[pe_oi_col] = df[pe_oi_col].apply(clean_num).fillna(0)

                # Calculations
                total_ce = df[ce_oi_col].sum()
                total_pe = df[pe_oi_col].sum()
                pcr = round(total_pe / total_ce, 2) if total_ce > 0 else 0

                # UI Layout
                c1, c2 = st.columns(2)
                c1.metric("PCR (OI)", pcr)
                sentiment = "Bullish" if pcr > 1.0 else "Bearish" if pcr < 0.7 else "Neutral"
                c2.metric("Sentiment", sentiment)

                # Chart
                df_sorted = df.sort_values(by=strike_col)
                # Show 15 strikes above/below center
                mid = len(df_sorted) // 2
                df_zoom = df_sorted.iloc[max(0, mid-15) : min(len(df_sorted), mid+15)]

                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_zoom[strike_col], y=df_zoom[ce_oi_col], name='Call OI', marker_color='#FF4B4B'))
                fig.add_trace(go.Bar(x=df_zoom[strike_col], y=df_zoom[pe_oi_col], name='Put OI', marker_color='#00CC96'))
                
                fig.update_layout(barmode='group', title="OI near ATM Strikes", xaxis_title="Strike Price", 
                                  legend=dict(orientation="h", y=1.1), margin=dict(l=0, r=0, t=50, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Found Strike Price, but Call/Put OI columns are missing or incorrectly named.")

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Upload the CSV file downloaded from the NSE Option Chain page.")
