import streamlit as st
from PIL import Image
import math

# ---------------------------------------------------------
# 1. PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Gann Institutional Analyst", layout="wide")

st.title("📐 Gann Price-Time Strategy Engine")
st.markdown("---")

# ---------------------------------------------------------
# 2. SIDEBAR - UPLOADS & PRICE INPUTS
# ---------------------------------------------------------
st.sidebar.header("📥 1. Chart Uploads")
uploaded_files = st.sidebar.file_uploader(
    "Upload up to 5 screenshots", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

st.sidebar.header("💰 2. Price Data")
cmp = st.sidebar.number_input("Current Market Price (CMP)", value=0.0, step=0.1)
volatility = st.sidebar.slider("Volatility Factor (Gann Increment)", 0.1, 1.0, 0.5)

# ---------------------------------------------------------
# 3. GANN MATHEMATICAL ENGINE
# ---------------------------------------------------------
def calculate_gann_targets(price):
    """
    Calculates Square of 9 targets based on the square root of the price.
    Formula: (sqrt(price) + factor)^2
    """
    if price <= 0:
        return 0, 0, 0
    root = math.sqrt(price)
    # Gann Degrees converted to factors
    target_90 = (root + 0.5)**2    # 90 degrees
    target_180 = (root + 1.0)**2   # 180 degrees
    support_90 = (root - 0.5)**2   # -90 degrees
    return round(target_90, 2), round(target_180, 2), round(support_90, 2)

# ---------------------------------------------------------
# 4. MAIN EXECUTION
# ---------------------------------------------------------
if uploaded_files:
    # Display Uploaded Images
    st.subheader("🖼️ Timeframe Analysis")
    cols = st.columns(len(uploaded_files[:5]))
    for i, file in enumerate(uploaded_files[:5]):
        img = Image.open(file)
        with cols[i]:
            st.image(img, caption=f"TF Screenshot {i+1}", use_container_width=True)

    if cmp > 0:
        t90, t180, s90 = calculate_gann_targets(cmp)
        
        st.divider()

        # SECTION 1: CONTRADICTIONS
        st.subheader("🚨 Institutional Contradictions")
        
        # Structural Logic for Contradictions
        # We manually list them as per Gann's laws of Price-Time imbalance
        contradictions = []
        if cmp > t90:
            contradictions.append(f"Price is trading at {cmp}, which is above the 90° Square of 9 target ({t90}). This creates a 'Price-ahead-of-Time' imbalance.")
        if s90 > (cmp * 0.95):
             contradictions.append(f"Primary Support ({s90}) is too close to CMP. High probability of a 'Vibration Trap'.")
        
        if contradictions:
            for c in contradictions:
                st.error(f"**CONTRADICTION:** {c}")
        else:
            st.info("No immediate geometric contradictions. Price and Time are in relative balance.")

        st.divider()

        # SECTION 2: PRICE-BASED STRATEGY
        st.subheader("🎯 Tactical Strategy (Price Terms)")
        
        col_strat, col_targets = st.columns(2)
        
        with col_strat:
            st.markdown("### **Execution Plan**")
            if cmp < t90:
                st.success(f"**MODE: BULLISH ACCUMULATION**")
                st.write(f"**Entry Range:** {cmp} - {round(cmp * 1.005, 2)}")
                st.write(f"**Trigger:** Breakout above {t90} (Gann 90° level)")
            else:
                st.warning(f"**MODE: BEARISH / DISTRIBUTION**")
                st.write(f"**Entry Range:** {cmp} - {round(cmp * 0.995, 2)}")
                st.write(f"**Trigger:** Breakdown below {s90} (Gann Support)")

        with col_targets:
            st.markdown("### **Exit & Risk Management**")
            st.write(f"**Primary Target (T1):** {t90} (90° Resistance)")
            st.write(f"**Secondary Target (T2):** {t180} (180° Major Target)")
            st.error(f"**Hard Stop Loss:** {s90} (Square of 9 Floor)")

    else:
        st.warning("Please enter the Current Market Price (CMP) in the sidebar to generate Price Targets.")

else:
    st.info("👈 Please upload screenshots in the sidebar to begin.")

# ---------------------------------------------------------
# 5. TECHNICAL DOCUMENTATION
# ---------------------------------------------------------
with st.expander("📖 Methodology: How these prices are calculated"):
    st.write("""
    The system uses the **Gann Square of 9** mathematical formula:
    * **Square Root of Price:** We convert the current price to its mathematical root.
    * **Degrees to Factor:** Gann's circle (360°) is mapped where 180° = +1.0 and 90° = +0.5.
    * **Target Calculation:** We add the degree factor to the root and re-square it to find the future price resistance.
    * **Example:** If CMP is 100 (Root = 10), the 180° Target is (10 + 1)² = 121.
    """)
