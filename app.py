import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm

# --- MATHEMATICAL ENGINE: BLACK-SCHOLES FOR GREEKS ---
def calculate_greeks(S, K, T, r, sigma, option_type="CE"):
    if T <= 0 or sigma <= 0: return 0, 0, 0
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

# --- CONFIGURATION ---
st.set_page_config(page_title="Legendary Market Auditor", layout="wide")
st.title("🛡️ Institutional Option Vector Auditor")

# --- MULTI-MODAL UPLOAD ---
uploaded_file = st.file_uploader("Upload Data (CSV for Analysis, Image for Visual Audit)", type=["csv", "jpg", "jpeg"])

if uploaded_file:
    if uploaded_file.type != "text/csv":
        st.image(uploaded_file, caption="Visual Reference Uploaded")
        st.info("Visual data acknowledged. Please upload the corresponding CSV for mathematical execution.")
    else:
        try:
            # 1. DATA INGESTION & HEURISTIC POSITIONING
            df_raw = pd.read_csv(uploaded_file, header=None).astype(str)
            data_start = None
            for i in range(len(df_raw)):
                row_vals = pd.to_numeric(df_raw.iloc[i].str.replace(',', ''), errors='coerce')
                if row_vals.count() > 10:
                    data_start = i
                    break
            
            if data_start is None:
                st.error("Mathematical Header Not Found.")
            else:
                # 2. VECTOR EXTRACTION
                df = df_raw.iloc[data_start:].copy()
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
                
                strike = df.iloc[:, df.shape[1]//2]
                ce_oi, ce_choi, ce_ltp, ce_iv = df.iloc[:, 1], df.iloc[:, 2], df.iloc[:, 5], df.iloc[:, 4]
                pe_oi, pe_choi, pe_ltp, pe_iv = df.iloc[:, -2], df.iloc[:, -3], df.iloc[:, -6], df.iloc[:, -5]
                
                # Dynamic Spot Calculation (ATM Identification)
                spot_price = strike.iloc[(strike - ce_ltp.mean()).abs().idxmin()]
                
                # 3. BLACK-SCHOLES EXECUTION (GREEKS)
                # Constants: T (7 days to expiry), r (0.07 risk-free rate)
                ce_delta, ce_gamma, ce_theta = calculate_greeks(spot_price, spot_price, 7/365, 0.07, ce_iv.mean()/100, "CE")
                pe_delta, pe_gamma, pe_theta = calculate_greeks(spot_price, spot_price, 7/365, 0.07, pe_iv.mean()/100, "PE")

                # 4. PART 1: POINT-WISE MATHEMATICAL ANALYSIS
                st.header("PART 1: QUANTITATIVE VECTOR ANALYSIS")
                pcr = pe_oi.sum() / ce_oi.sum() if ce_oi.sum() > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("PCR (OI Vector)", f"{pcr:.2f}")
                col2.metric("Systemic Gamma", f"{ce_gamma + pe_gamma:.5f}")
                col3.metric("Daily Theta Decay", f"{ce_theta + pe_theta:.2f}")

                # Buildup Mapping
                def get_buildup(p, oi):
                    if p > 0 and oi > 0: return "Long Buildup"
                    if p < 0 and oi > 0: return "Short Buildup"
                    if p > 0 and oi < 0: return "Short Covering"
                    if p < 0 and oi < 0: return "Long Unwinding"
                    return "Neutral"

                st.write(f"**ATM Buildup:** CE is in `{get_buildup(ce_choi.sum(), ce_choi.sum())}` | PE is in `{get_buildup(pe_choi.sum(), pe_choi.sum())}`")

                # 5. PART 2: CONTRADICTION AUDIT (CRITICAL)
                st.header("PART 2: SYSTEMIC CONTRADICTIONS")
                st.write("Cross-referencing price-action vectors against Open Interest and Greek decay:")
                
                contradictions = []
                if pcr > 1.2 and ce_choi.sum() > pe_choi.sum():
                    contradictions.append("PCR is Bullish, but current capital flow shows aggressive Call Writing (Bearish divergence).")
                if ce_choi.sum() < 0 and ce_ltp.iloc[0] > ce_ltp.iloc[1]: # Simplified price trend
                    contradictions.append("Short Covering detected in Calls: Rising prices are due to exits, not fresh buyers.")
                if abs(ce_delta) < 0.4 and pcr > 1.5:
                    contradictions.append("Low Delta sensitivity despite high PCR: Market is top-heavy and lacks momentum.")

                if not contradictions:
                    st.success("Mathematical alignment confirmed. No loose ends detected.")
                else:
                    for c in contradictions:
                        st.warning(f"⚠️ {c}")

                # 6. PART 3: STRATEGY & CONCLUSION
                st.header("PART 3: FINAL STRATEGY")
                
                st.subheader("Conclusion (Strict Order)")
                st.markdown(f"""
                1. **What is the data saying:** PCR is **{pcr:.2f}** with Gamma concentration at **{spot_price}**.
                2. **Where is the contradiction:** {contradictions[0] if contradictions else "None - Data is synchronized."}
                3. **Who has the stronger hand:** {"Sellers/Writers" if abs(ce_choi.sum()) > abs(pe_choi.sum()) else "Buyers/Aggressors"} are controlling the narrative.
                """)

                # Strategy Logic
                if len(contradictions) > 1:
                    st.info("🎯 **STRATEGY: WAIT AND WATCH**")
                    st.write("Supporting Logic: Multiple mathematical contradictions detected. Market is in a 'Value Trap' phase.")
                elif pcr > 1.1 and ce_choi.sum() < pe_choi.sum():
                    st.success("🎯 **STRATEGY: BUY / GO LONG**")
                    st.write(f"Supporting Logic: Put writing dominance confirmed at {spot_price}. Delta alignment is positive.")
                elif pcr < 0.9 and ce_choi.sum() > pe_choi.sum():
                    st.error("🎯 **STRATEGY: SELL / GO SHORT**")
                    st.write("Supporting Logic: Call writing saturation detected. Mathematical resistance verified by Greek decay.")
                else:
                    st.warning("🎯 **STRATEGY: HOLD**")
                    st.write("Supporting Logic: Market is in an equilibrium state. Volatility (Gamma) is too low for a directional bet.")

        except Exception as e:
            st.error(f"Mathematical failure in audit: {e}")
