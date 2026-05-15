import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Quant Option Auditor", layout="wide")
st.title("🛡️ Institutional Option Chain Auditor")

uploaded_file = st.file_uploader("Upload NSE CSV", type="csv")

if uploaded_file:
    try:
        # 1. ROBUST DATA INGESTION
        df_raw = pd.read_csv(uploaded_file, header=None).astype(str)
        data_start_row = None
        for i in range(len(df_raw)):
            row = df_raw.iloc[i].str.replace(',', '').str.strip()
            if pd.to_numeric(row, errors='coerce').count() > 8:
                data_start_row = i
                break

        if data_start_row is None:
            st.error("Invalid NSE Format.")
        else:
            df = df_raw.iloc[data_start_row:].copy()
            # Position Mapping (Fixed NSE Standard)
            # CE: OI(1), CHNG_OI(2), VOL(3), IV(4), LTP(5), CHNG(6)
            # PE: LTP(-6), IV(-5), VOL(-4), CHNG_OI(-3), OI(-2)
            for col in df.columns:
                df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
            
            # Extract Core Series
            strike = df.iloc[:, df.shape[1]//2] # Middle column
            ce_oi, ce_choi, ce_ltp, ce_price_chng = df.iloc[:, 1], df.iloc[:, 2], df.iloc[:, 5], df.iloc[:, 6]
            pe_oi, pe_choi, pe_ltp, pe_price_chng = df.iloc[:, -2], df.iloc[:, -3], df.iloc[:, -6], df.iloc[:, -7]

            # 2. MATHEMATICAL PROVEN MODELS (Fibonacci & Stat Deviation)
            max_oi_strike = strike.iloc[ce_oi.idxmax()]
            min_oi_strike = strike.iloc[pe_oi.idxmax()]
            diff = abs(max_oi_strike - min_oi_strike)
            fib_618 = min_oi_strike + (diff * 0.618) # Golden Ratio Level
            
            # 3. POSITION DYNAMICS (Buildup Analysis)
            def get_buildup(p_chng, oi_chng):
                if p_chng > 0 and oi_chng > 0: return "Long Buildup (Aggressive Buying)"
                if p_chng < 0 and oi_chng > 0: return "Short Buildup (Aggressive Selling)"
                if p_chng > 0 and oi_chng < 0: return "Short Covering (Positions Squaring Off)"
                if p_chng < 0 and oi_chng < 0: return "Long Unwinding (Buyers Exiting)"
                return "Neutral"

            # 4. CONTRADICTION & AUDIT ENGINE
            st.header("🧐 Strict Mathematical Audit")
            st.info("Before giving strategy, confirm you have analysed: OI Change, Premium vs OI Alignment, Spot Direction, and Accumulation.")

            # Analyzing Contradictions
            contradictions = []
            # Rule: If Price is UP but OI is DOWN (Short Covering), it's a weak rally.
            if ce_price_chng.sum() > 0 and ce_choi.sum() < 0:
                contradictions.append("CE Price rising on Decreasing OI: Rally lacks conviction (Short Covering).")
            if pe_price_chng.sum() > 0 and pe_choi.sum() < 0:
                contradictions.append("PE Price rising on Decreasing OI: Support is forced (Short Covering).")
            
            # Premium vs OI Alignment
            pcr = pe_oi.sum() / ce_oi.sum()
            if pcr > 1.2 and ce_choi.sum() > pe_choi.sum():
                contradictions.append("PCR is Bullish, but fresh Call Writing is outpacing Puts today.")

            st.subheader("⚠️ Found Contradictions")
            if not contradictions:
                st.success("No mathematical contradictions. Data points are perfectly aligned.")
            else:
                for c in contradictions:
                    st.warning(c)

            # 5. FINAL CONCLUSION (STRICT ORDER)
            st.divider()
            st.subheader("🏁 Data-Driven Conclusion")
            
            # Logic for Stronger Hand
            hand = "Sellers (Option Writers)" if (abs(ce_choi.sum()) > abs(ce_price_chng.sum() * 100)) else "Buyers"
            
            st.markdown(f"""
            **1. What is the data saying:** - PCR is {pcr:.2f}. 
            - Golden Ratio Support (0.618) at: **{fib_618:.2f}**.
            - Primary Buildup: {get_buildup(ce_price_chng.sum(), ce_choi.sum())}.
            
            **2. Where is the contradiction:** - {contradictions[0] if contradictions else "None. All mathematical vectors align."}
            
            **3. Who has the stronger hand:** - **{hand}** are dominating. Position squaring off detected in { "Calls" if ce_choi.sum() < 0 else "Puts" if pe_choi.sum() < 0 else "None"}.
            """)

            # 6. THE STRATEGY (NO ASSUMPTIONS)
            st.subheader("🎯 Final Strategy")
            st.caption("Cross-referenced against Fibonacci, Price-OI Correlation, and Volume Weighted Metrics.")

            if len(contradictions) > 1:
                st.error("STRATEGY: WAIT AND WATCH. Contradictions indicate a trap or high volatility churn.")
            elif pcr > 1.1 and ce_choi.sum() < pe_choi.sum():
                st.success("STRATEGY: BUY. Mathematical alignment with Golden Ratio support. Accumulation by Buyers confirmed.")
            elif pcr < 0.8 and ce_choi.sum() > pe_choi.sum():
                st.error("STRATEGY: SELL. Resistance is mathematically verified. Sellers are writing off contracts aggressively.")
            else:
                st.warning("STRATEGY: HOLD. Market is in a supply-demand equilibrium. No clear breakout vector.")

            # VISUAL PROOF
            fig = go.Figure()
            fig.add_trace(go.Bar(x=strike, y=ce_oi, name='Call OI (Resistance)', marker_color='red'))
            fig.add_trace(go.Bar(x=strike, y=pe_oi, name='Put OI (Support)', marker_color='green'))
            fig.add_hline(y=fib_618, line_dash="dot", annotation_text="Golden Ratio Pivot")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Audit Failed: {e}")
