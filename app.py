import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm

# --- BLACK-SCHOLES ENGINE ---
def calculate_greeks(S, K, T, r, sigma, option_type="CE"):
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0: return 0, 0, 0
    try:
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if option_type == "CE":
            delta = norm.cdf(d1)
            theta = -(S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))) - r * K * np.exp(-r * T) * norm.cdf(d2)
        else:
            delta = -norm.cdf(-d1)
            theta = -(S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))) + r * K * np.exp(-r * T) * norm.cdf(-d2)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        return round(delta, 3), round(gamma, 4), round(theta / 365, 2)
    except:
        return 0, 0, 0

st.set_page_config(page_title="Institutional Auditor", layout="wide")
st.title("🛡️ Institutional Option Vector Auditor")

# Multi-format uploader
uploaded_file = st.file_uploader("Upload Data (CSV for Analysis, JPG/JPEG for Visual Audit)", type=["csv", "jpg", "jpeg"])

if not uploaded_file:
    st.warning("Awaiting Data. Please upload a CSV file from NSE to trigger the mathematical analysis.")

if uploaded_file:
    if uploaded_file.type != "text/csv":
        st.image(uploaded_file, caption="Visual Reference Uploaded")
        st.info("Visual data acknowledged. Please upload the CSV to run the mathematical audit.")
    else:
        try:
            # 1. DATA EXTRACTION
            df_raw = pd.read_csv(uploaded_file, header=None).astype(str)
            data_start = None
            for i in range(len(df_raw)):
                row_vals = pd.to_numeric(df_raw.iloc[i].str.replace(',', ''), errors='coerce')
                if row_vals.count() > 10:
                    data_start = i
                    break
            
            if data_start is None:
                st.error("Mathematical Header Not Found. Please use a raw NSE CSV file.")
            else:
                # Process Data
                df = df_raw.iloc[data_start:].copy()
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
                
                # Column Mapping
                strike = df.iloc[:, df.shape[1]//2]
                ce_oi, ce_choi, ce_ltp, ce_iv, ce_nc = df.iloc[:, 1], df.iloc[:, 2], df.iloc[:, 5], df.iloc[:, 4], df.iloc[:, 6]
                pe_oi, pe_choi, pe_ltp, pe_iv, pe_nc = df.iloc[:, -2], df.iloc[:, -3], df.iloc[:, -6], df.iloc[:, -5], df.iloc[:, -7]
                
                spot_price = strike.iloc[(strike - ce_ltp.mean()).abs().idxmin()]
                pcr = pe_oi.sum() / ce_oi.sum() if ce_oi.sum() > 0 else 0
                
                # Greeks Execution
                c_delta, c_gamma, c_theta = calculate_greeks(spot_price, spot_price, 7/365, 0.07, ce_iv.mean()/100, "CE")
                p_delta, p_gamma, p_theta = calculate_greeks(spot_price, spot_price, 7/365, 0.07, pe_iv.mean()/100, "PE")

                # --- SEGMENTED OUTPUT START ---

                # PART 1: CONTRADICTIONS
                st.header("PART 1: SYSTEMIC CONTRADICTIONS")
                contradictions = []
                if pcr > 1.2 and ce_choi.sum() > pe_choi.sum():
                    contradictions.append("PCR is Bullish, but current capital flow shows aggressive Call Writing (Bearish Divergence).")
                if ce_nc.sum() > 0 and ce_choi.sum() < 0:
                    contradictions.append("Short Covering in Calls: Price rise is due to seller exits, not buyer strength.")
                if pe_nc.sum() < 0 and pe_choi.sum() < 0:
                    contradictions.append("Long Unwinding in Puts: Bullish support is liquidating positions.")

                if not contradictions:
                    st.success("Mathematical alignment confirmed. No loose ends detected.")
                else:
                    for c in contradictions:
                        st.warning(f"⚠️ {c}")

                # PART 2: ANALYSIS
                st.header("PART 2: MULTI-PART QUANTITATIVE ANALYSIS")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Price-OI & Greeks")
                    st.write(f"**PCR:** {pcr:.2f}")
                    st.write(f"**Combined Gamma:** {c_gamma + p_gamma:.5f}")
                    st.write(f"**Daily Theta Decay:** {c_theta + p_theta:.2f}")
                
                with col2:
                    st.subheader("Accumulation Logic")
                    strong_hand = "Sellers (Writers)" if abs(ce_choi.sum()) > abs(ce_nc.sum()*10) else "Buyers"
                    st.write(f"**Stronger Hand:** {strong_hand}")
                    st.write(f"**Position Squares:** {abs(ce_choi[ce_choi<0].sum()) + abs(pe_choi[pe_choi<0].sum()):,.0f} contracts squared off.")

                # PART 3: STRATEGY
                st.header("PART 3: FINAL STRATEGY & CONCLUSION")
                st.markdown(f"""
                1. **What is the data saying:** PCR at {pcr:.2f} with Spot at {spot_price}.
                2. **Where is the contradiction:** {contradictions[0] if contradictions else "None."}
                3. **Who has the stronger hand:** {strong_hand}.
                """)

                # Strategy Finalization
                if len(contradictions) > 1:
                    st.error("🎯 **STRATEGY: WAIT AND WATCH** (High Contradiction)")
                elif pcr > 1.1 and ce_choi.sum() < pe_choi.sum():
                    st.success("🎯 **STRATEGY: BUY / LONG**")
                elif pcr < 0.8 and ce_choi.sum() > pe_choi.sum():
                    st.error("🎯 **STRATEGY: SELL / SHORT**")
                else:
                    st.warning("🎯 **STRATEGY: HOLD / NEUTRAL**")

        except Exception as e:
            st.error(f"Mathematical Error: {e}. Ensure you are uploading a raw NSE CSV.")
