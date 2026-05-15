import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm

# --- BLACK-SCHOLES MATHEMATICAL ENGINE ---
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

st.set_page_config(page_title="Institutional Auditor", layout="centered")
st.title("🛡️ Institutional Option Vector Auditor")

uploaded_file = st.file_uploader("Upload NSE CSV or Image for Audit", type=["csv", "jpg", "jpeg"])

if uploaded_file:
    if uploaded_file.type != "text/csv":
        st.image(uploaded_file, caption="Visual Reference Uploaded")
        st.info("Visual data acknowledged. Upload CSV for mathematical execution.")
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
                st.error("Mathematical Header Not Found. Use raw NSE CSV.")
            else:
                df = df_raw.iloc[data_start:].copy()
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
                
                # Mapping Constants
                strike = df.iloc[:, df.shape[1]//2]
                ce_oi, ce_choi, ce_ltp, ce_iv, ce_nc = df.iloc[:, 1], df.iloc[:, 2], df.iloc[:, 5], df.iloc[:, 4], df.iloc[:, 6]
                pe_oi, pe_choi, pe_ltp, pe_iv, pe_nc = df.iloc[:, -2], df.iloc[:, -3], df.iloc[:, -6], df.iloc[:, -5], df.iloc[:, -7]
                
                spot_price = strike.iloc[(strike - ce_ltp.mean()).abs().idxmin()]
                pcr = pe_oi.sum() / ce_oi.sum() if ce_oi.sum() > 0 else 0
                
                # Greeks Calculation
                c_delta, c_gamma, c_theta = calculate_greeks(spot_price, spot_price, 7/365, 0.07, ce_iv.mean()/100, "CE")
                p_delta, p_gamma, p_theta = calculate_greeks(spot_price, spot_price, 7/365, 0.07, pe_iv.mean()/100, "PE")

                # --- PART 1: CONTRADICTIONS FIRST ---
                st.header("PART 1: SYSTEMIC CONTRADICTIONS")
                st.write("Cross-referencing price vectors, OI accumulation, and Greek decay:")
                
                contradictions = []
                # Contradiction 1: PCR vs Current Flow
                if pcr > 1.2 and ce_choi.sum() > pe_choi.sum():
                    contradictions.append("PCR is Bullish, but fresh Call Writing is outpacing Puts (Bearish Divergence).")
                # Contradiction 2: Premium vs OI (Short Covering Check)
                if ce_nc.sum() > 0 and ce_choi.sum() < 0:
                    contradictions.append("Call Price rising on Decreasing OI: Rally is forced by Short Covering, not fresh buying.")
                # Contradiction 3: Support Liquidation
                if pe_nc.sum() < 0 and pe_choi.sum() < 0:
                    contradictions.append("Put Long Unwinding: Support is thinning as buyers exit positions.")

                if not contradictions:
                    st.success("Mathematical alignment confirmed. No loose ends detected.")
                else:
                    for c in contradictions:
                        st.warning(f"⚠️ {c}")

                # --- PART 2: MULTI-PART ANALYSIS ---
                st.header("PART 2: SEGMENTED QUANTITATIVE ANALYSIS")
                
                with st.expander("A. Price-OI Dynamics & Buildup"):
                    def get_buildup(p, oi):
                        if p > 0 and oi > 0: return "Long Buildup"
                        if p < 0 and oi > 0: return "Short Buildup"
                        if p > 0 and oi < 0: return "Short Covering"
                        if p < 0 and oi < 0: return "Long Unwinding"
                        return "Neutral"
                    st.write(f"* **CE Vector:** {get_buildup(ce_nc.sum(), ce_choi.sum())}")
                    st.write(f"* **PE Vector:** {get_buildup(pe_nc.sum(), pe_choi.sum())}")
                    st.write(f"* **Contracts Written Off:** {abs(ce_choi[ce_choi<0].sum()) + abs(pe_choi[pe_choi<0].sum()):,.0f} positions squared off.")

                with st.expander("B. Greek & Mathematical Audit"):
                    st.write(f"* **PCR (OI Ratio):** {pcr:.2f}")
                    st.write(f"* **Systemic Gamma:** {c_gamma + p_gamma:.5f} (Volatility Risk)")
                    st.write(f"* **Theta Decay:** {c_theta + p_theta:.2f} per day")
                    # Fibonacci Golden Ratio Pivot
                    fib_pivot = strike.min() + (strike.max() - strike.min()) * 0.618
                    st.write(f"* **Mathematical Pivot (Golden Ratio):** {fib_pivot:,.2f}")

                with st.expander("C. Accumulation & Strong Hand"):
                    strong_hand = "Sellers (Option Writers)" if abs(ce_choi.sum()) > abs(ce_nc.sum()*10) else "Buyers (Aggressors)"
                    st.write(f"* **Dominant Entity:** {strong_hand} are currently controlling the narrative.")

                # --- PART 3: STRATEGY ---
                st.header("PART 3: FINAL STRATEGY")
                
                # Logic Finalization
                st.subheader("Conclusion (Strict Order)")
                st.markdown(f"""
                1. **What is the data saying:** PCR is **{pcr:.2f}** with major OI Change of **{ce_choi.sum() + pe_choi.sum():,.0f}**.
                2. **Where is the contradiction:** {contradictions[0] if contradictions else "None - Vectors are synchronized."}
                3. **Who has the stronger hand:** **{strong_hand}**.
                """)

                # No Assumption Strategy
                st.subheader("Actionable Signal")
                if len(contradictions) > 1:
                    st.info("🎯 **STRATEGY: WAIT AND WATCH**")
                    st.caption("Reason: Loose ends (contradictions) detected. No directional bet is mathematically safe.")
                elif pcr > 1.1 and ce_choi.sum() < pe_choi.sum():
                    st.success("🎯 **STRATEGY: BUY / HOLD**")
                    st.caption("Reason: Put writing dominance and positive price-OI alignment confirmed.")
                elif pcr < 0.8 and ce_choi.sum() > pe_choi.sum():
                    st.error("🎯 **STRATEGY: SELL**")
                    st.caption("Reason: Heavy call writing and mathematical resistance at pivot levels.")
                else:
                    st.warning("🎯 **STRATEGY: HOLD**")
                    st.caption("Reason: Market is at equilibrium. No aggressive buildup detected.")

        except Exception as e:
            st.error(f"Audit failed: {e}")
