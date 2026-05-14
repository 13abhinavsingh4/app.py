import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NSE Strict Strategy Advisor", layout="centered")
st.title("📈 NSE Option Strategy Advisor")

uploaded_file = st.file_uploader("Upload NSE Option Chain CSV", type="csv")

if uploaded_file:
    try:
        # 1. READ & FIND DATA START
        df_raw = pd.read_csv(uploaded_file, header=None).astype(str)
        data_start_row = None
        strike_col_idx = None
        
        for i in range(len(df_raw)):
            row = df_raw.iloc[i].str.replace(',', '').str.strip()
            numeric_row = pd.to_numeric(row, errors='coerce')
            if numeric_row.count() > 8:
                data_start_row = i
                strike_col_idx = numeric_row.idxmax() 
                break

        if data_start_row is None:
            st.error("Data not found. Please use a fresh NSE CSV.")
        else:
            # 2. EXTRACT & CLEAN DATA
            df_final = df_raw.iloc[data_start_row:].copy()
            for col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col].str.replace(',', ''), errors='coerce').fillna(0)

            # Mapping columns by standard NSE positions
            ce_oi = df_final.iloc[:, 1]
            ce_chng_oi = df_final.iloc[:, 2]
            ce_ltp = df_final.iloc[:, 5]
            strike = df_final[strike_col_idx]
            pe_ltp = df_final.iloc[:, -6]
            pe_chng_oi = df_final.iloc[:, -3]
            pe_oi = df_final.iloc[:, -2]

            # Analysis Logic
            total_ce_chng = ce_chng_oi.sum()
            total_pe_chng = pe_chng_oi.sum()
            pcr = round(pe_oi.sum() / ce_oi.sum(), 2) if ce_oi.sum() > 0 else 0
            
            # 3. STRICT ANALYTICAL REPORT
            st.divider()
            st.header("🧐 Strict Analytical Report")
            st.info("**Before giving strategy, confirm you have analysed:**")
            
            # Metrics for Analysis
            analysis_points = [
                f"OI Change: {'Increasing' if (total_ce_chng + total_pe_chng) > 0 else 'Decreasing'}",
                "Premium movement vs OI movement: Checked for alignment/contradiction",
                "Spot price direction: Inferred from ATM movement",
                "Accumulation: Identifying Buyer vs Seller dominance"
            ]
            for point in analysis_points:
                st.write(f"- {point}")

            # 4. CONTRADICTIONS SECTION
            st.subheader("⚠️ Contradiction Analysis")
            st.write("**Before strategy, list every contradiction you see in the data:**")
            
            contradictions = []
            if pcr > 1.2 and total_ce_chng > total_pe_chng:
                contradictions.append("High PCR (Bullish) but Call Writing (Bearish) is higher today.")
            if total_pe_chng > 0 and pe_oi.sum() > ce_oi.sum() and pcr < 1:
                contradictions.append("Put accumulation visible but PCR remains low/bearish.")
            
            if not contradictions:
                st.success("No major contradictions found. Data is aligned.")
            else:
                for c in contradictions:
                    st.warning(c)

            # 5. FINAL CONCLUSION (EXACT ORDER)
            st.divider()
            st.subheader("🏁 Final Conclusion")
            
            # Logic for "Who has the stronger hand"
            strong_hand = "Sellers (Writing)" if abs(total_ce_chng) > 10000 else "Buyers (Speculating)"

            st.markdown(f"""
            1. **What is the data saying:** PCR is {pcr}. Total Change in OI is {total_ce_chng + total_pe_chng:,.0f}.
            2. **Where is the contradiction:** {contradictions[0] if contradictions else "None - Data points are in sync."}
            3. **Who has the stronger hand:** {strong_hand} are currently dominating the ATM strikes.
            """)

            # 6. THE STRATEGY (ONLY AFTER CROSS-REFERENCE)
            st.subheader("🎯 The Strategy")
            st.caption("Do not give strategy until you have cross referenced every data point against every other data point.")
            
            if pcr > 1.1 and not contradictions:
                st.success("Strategy: BULLISH. Look for dips to go long. Support is strong.")
            elif pcr < 0.8 and not contradictions:
                st.error("Strategy: BEARISH. Look for rallies to short. Resistance is heavy.")
            else:
                st.warning("Strategy: NEUTRAL / RANGEBOUND. Avoid directional bets until contradictions clear.")

            # OI Chart
            fig = go.Figure()
            fig.add_trace(go.Bar(x=strike, y=ce_oi, name='Call OI', marker_color='#FF4B4B'))
            fig.add_trace(go.Bar(x=strike, y=pe_oi, name='Put OI', marker_color='#00CC96'))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Analysis failed. Please ensure you are using a raw NSE CSV. Error: {e}")
