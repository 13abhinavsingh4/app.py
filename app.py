import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NSE Option Analyzer", layout="centered")
st.title("📈 NSE Option Chain Analyzer")

uploaded_file = st.file_uploader("Choose NSE CSV file", type="csv")

if uploaded_file:
    try:
        # Step 1: Find the header row by looking for "Strike Price"
        df_raw = pd.read_csv(uploaded_file, header=None, nrows=30)
        header_idx = None
        for i, row in df_raw.iterrows():
            if any("STRIKE" in str(x).upper() for x in row.values):
                header_idx = i
                break
        
        if header_idx is None:
            st.error("Could not find the data table in this CSV. Please use a raw NSE file.")
        else:
            # Step 2: Read data starting from the identified header
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, skiprows=header_idx)
            
            # Clean column names and handle cases where headers might be duplicated
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Identify the Strike column index
            strike_col_name = [c for c in df.columns if "STRIKE" in c][0]
            strike_idx = list(df.columns).index(strike_col_name)

            # Step 3: Identify OI columns by position
            # In NSE CSV: 
            # CALL OI is usually the 2nd column (index 1)
            # PUT OI is usually the 2nd-to-last or 3rd-to-last
            # We will grab 'OI' columns specifically
            oi_indices = [i for i, col in enumerate(df.columns) if "OI" in col and "CHNG" not in col]
            
            ce_oi_idx = [i for i in oi_indices if i < strike_idx]
            pe_oi_idx = [i for i in oi_indices if i > strike_idx]

            if ce_oi_idx and pe_oi_idx:
                # Use the first 'OI' column found on each side
                c_oi_col = df.columns[ce_oi_idx[0]]
                p_oi_col = df.columns[pe_oi_idx[0]]

                # Clean numeric values
                def to_num(val):
                    return pd.to_numeric(str(val).replace(',', ''), errors='coerce')

                df[strike_col_name] = df[strike_col_name].apply(to_num)
                df[c_oi_col] = df[c_oi_col].apply(to_num).fillna(0)
                df[p_oi_col] = df[p_oi_col].apply(to_num).fillna(0)

                # Remove non-numeric rows (like 'Total' or empty rows)
                df = df.dropna(subset=[strike_col_name])

                # Calculations
                total_ce = df[c_oi_col].sum()
                total_pe = df[p_oi_col].sum()
                pcr = round(total_pe / total_ce, 2) if total_ce > 0 else 0

                # UI Display
                c1, c2 = st.columns(2)
                c1.metric("PCR (OI)", pcr)
                sentiment = "Bullish" if pcr > 1.0 else "Bearish" if pcr < 0.7 else "Neutral"
                c2.metric("Sentiment", sentiment)

                # Charting (Near-the-money)
                df_sorted = df.sort_values(by=strike_col_name)
                mid = len(df_sorted) // 2
                df_zoom = df_sorted.iloc[max(0, mid-15) : min(len(df_sorted), mid+15)]

                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_zoom[strike_col_name], y=df_zoom[c_oi_col], name='Call OI', marker_color='#FF4B4B'))
                fig.add_trace(go.Bar(x=df_zoom[strike_col_name], y=df_zoom[p_oi_col], name='Put OI', marker_color='#00CC96'))
                
                fig.update_layout(barmode='group', title="OI near ATM", xaxis_title="Strike Price", 
                                  legend=dict(orientation="h", y=1.1), margin=dict(l=0, r=0, t=50, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Found Strike Price, but could not map Call/Put OI positions. Try downloading the CSV again.")

    except Exception as e:
        st.error(f"Error analyzing file: {e}")
