import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------------------------------------------------------
# Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Advanced Option Chain Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern, sleek aesthetic
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3b82f6;
    }
    .metric-card.bullish { border-left-color: #10b981; }
    .metric-card.bearish { border-left-color: #ef4444; }
    .contradiction-box {
        background-color: #450a0a;
        border: 1px solid #f87171;
        border-radius: 8px;
        padding: 15px;
        color: #fca5a5;
    }
    .strategy-box {
        background-color: #064e3b;
        border: 1px solid #34d399;
        border-radius: 8px;
        padding: 15px;
        color: #a7f3d0;
    }
</style>
""", unsafe_with_html=True)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def validate_and_parse(file):
    try:
        df = pd.read_csv(file)
        required_cols = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        
        # Clean column names (strip whitespace)
        df.columns = [col.strip() for col in df.columns]
        
        if not all(col in df.columns for col in required_cols):
            st.error(f"Missing required columns in {file.name}. Required: {required_cols}")
            return None
            
        # Ensure correct data types
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna(subset=['Strike Price'])
    except Exception as e:
        st.error(f"Error parsing file {file.name}: {e}")
        return None

def calc_fibonacci_levels(high, low):
    diff = high - low
    levels = {
        '0% (Low)': low,
        '23.6%': low + 0.236 * diff,
        '38.2%': low + 0.382 * diff,
        '50.0%': low + 0.5 * diff,
        '61.8% (Golden Ratio)': low + 0.618 * diff,
        '100% (High)': high,
        '161.8% (Golden Extension)': low + 1.618 * diff
    }
    return levels

# -----------------------------------------------------------------------------
# Sidebar & Data Upload Section
# -----------------------------------------------------------------------------
st.sidebar.title("📊 Options Analytics Control Panel")
st.sidebar.markdown("---")

st.sidebar.subheader("1. Upload Datasets")
prev_file = st.sidebar.file_uploader("Previous Day CSV", type=["csv"], key="prev")
curr_file = st.sidebar.file_uploader("Current Day CSV", type=["csv"], key="curr")

# Main Page Header
st.title("⚡ Advanced Option Chain & Fibonacci Dynamics Analyzer")
st.markdown("Analyze micro-level option contract shifts, extract strategic contradictions, and map Fibonacci structures seamlessly.")

if not prev_file or not curr_file:
    st.info("💡 Please upload both Previous Day and Current Day CSV files in the sidebar to initiate analysis.")
    
    # Showcase expected format to the user
    with st.expander("📋 View Expected CSV Structure Example"):
        sample_data = pd.DataFrame({
            'Strike Price': [18000, 18100, 18200],
            'CE Price': [150, 90, 45],
            'CE OI': [12000, 25000, 40000],
            'PE Price': [35, 75, 130],
            'PE OI': [35000, 20000, 8000]
        })
        st.dataframe(sample_data, use_container_width=True)
    st.stop()

# Load and validate files
df_prev = validate_and_parse(prev_file)
df_curr = validate_and_parse(curr_file)

if df_prev is None or df_curr is None:
    st.stop()

# -----------------------------------------------------------------------------
# Data Alignment & Strike Selection
# -----------------------------------------------------------------------------
# Find common strikes available in both datasets
common_strikes = sorted(list(set(df_prev['Strike Price']).intersection(set(df_curr['Strike Price']))))

if not common_strikes:
    st.error("❌ Crucial Error: No matching Strike Prices found between the two uploaded CSV datasets.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("2. Target Strike Configuration")
selected_strike = st.sidebar.selectbox("Select Target Strike Price", common_strikes)

# Extract specific row data for calculations
row_p = df_prev[df_prev['Strike Price'] == selected_strike].iloc[0]
row_c = df_curr[df_curr['Strike Price'] == selected_strike].iloc[0]

# -----------------------------------------------------------------------------
# Core Metrics Processing
# -----------------------------------------------------------------------------
# CE Metrics
ce_p_chg_pct = ((row_c['CE Price'] - row_p['CE Price']) / row_p['CE Price']) * 100 if row_p['CE Price'] != 0 else 0
ce_oi_chg_pct = ((row_c['CE OI'] - row_p['CE OI']) / row_p['CE OI']) * 100 if row_p['CE OI'] != 0 else 0
ce_oi_net = row_c['CE OI'] - row_p['CE OI']

# PE Metrics
pe_p_chg_pct = ((row_c['PE Price'] - row_p['PE Price']) / row_p['PE Price']) * 100 if row_p['PE Price'] != 0 else 0
pe_oi_chg_pct = ((row_c['PE OI'] - row_p['PE OI']) / row_p['PE OI']) * 100 if row_p['PE OI'] != 0 else 0
pe_oi_net = row_c['PE OI'] - row_p['PE OI']

# PCR Metrics
pcr_prev = row_p['PE OI'] / row_p['CE OI'] if row_p['CE OI'] != 0 else 0
pcr_curr = row_c['PE OI'] / row_c['CE OI'] if row_c['CE OI'] != 0 else 0
pcr_change = pcr_curr - pcr_prev

# -----------------------------------------------------------------------------
# UI Layout (Tabs Setup)
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Dashboard Summary & Comparison", 
    "📊 OI & Price Visualizations", 
    "🌀 Fibonacci & Golden Ratio Levels", 
    "🎯 Contradiction Matrix & Strategy"
])

# -----------------------------------------------------------------------------
# TAB 1: Comparison Dashboard Summary
# -----------------------------------------------------------------------------
with tab1:
    st.subheader(f"🔍 Selected Strike Target: {selected_strike}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        color_class = "bullish" if ce_p_chg_pct >= 0 else "bearish"
        st.markdown(f"""
        <div class="metric-card {color_class}">
            <p style='margin:0; font-size:0.9rem; color:#94a3b8;'>CE Price Change</p>
            <h2 style='margin:5px 0;'>{ce_p_chg_pct:+.2f}%</h2>
            <p style='margin:0; font-size:0.8rem;'>Prev: {row_p['CE Price']} → Curr: {row_c['CE Price']}</p>
        </div>
        """, unsafe_with_html=True)
        
    with col2:
        color_class = "bullish" if ce_oi_net >= 0 else "bearish"
        st.markdown(f"""
        <div class="metric-card {color_class}">
            <p style='margin:0; font-size:0.9rem; color:#94a3b8;'>CE OI Change</p>
            <h2 style='margin:5px 0;'>{ce_oi_chg_pct:+.2f}%</h2>
            <p style='margin:0; font-size:0.8rem;'>Net Added: {ce_oi_net:+,}</p>
        </div>
        """, unsafe_with_html=True)

    with col3:
        color_class = "bullish" if pe_p_chg_pct >= 0 else "bearish"
        st.markdown(f"""
        <div class="metric-card {color_class}">
            <p style='margin:0; font-size:0.9rem; color:#94a3b8;'>PE Price Change</p>
            <h2 style='margin:5px 0;'>{pe_p_chg_pct:+.2f}%</h2>
            <p style='margin:0; font-size:0.8rem;'>Prev: {row_p['PE Price']} → Curr: {row_c['PE Price']}</p>
        </div>
        """, unsafe_with_html=True)
        
    with col4:
        color_class = "bullish" if pe_oi_net >= 0 else "bearish"
        st.markdown(f"""
        <div class="metric-card {color_class}">
            <p style='margin:0; font-size:0.9rem; color:#94a3b8;'>PE OI Change</p>
            <h2 style='margin:5px 0;'>{pe_oi_chg_pct:+.2f}%</h2>
            <p style='margin:0; font-size:0.8rem;'>Net Added: {pe_oi_net:+,}</p>
        </div>
        """, unsafe_with_html=True)

    st.markdown("### 📋 Comparative Raw Context Table")
    summary_df = pd.DataFrame({
        'Metric Type': ['CE Price', 'CE Open Interest (OI)', 'PE Price', 'PE Open Interest (OI)', 'Put-Call Ratio (PCR)'],
        'Previous Frame': [row_p['CE Price'], row_p['CE OI'], row_p['PE Price'], row_p['PE OI'], f"{pcr_prev:.3f}"],
        'Current Frame': [row_c['CE Price'], row_c['CE OI'], row_c['PE Price'], row_c['PE OI'], f"{pcr_curr:.3f}"],
        'Absolute Delta': [row_c['CE Price']-row_p['CE Price'], ce_oi_net, row_c['PE Price']-row_p['PE Price'], pe_oi_net, f"{pcr_change:+.3f}"]
    })
    st.table(summary_df)

# -----------------------------------------------------------------------------
# TAB 2: Charts and Graphical Insights
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("📊 Dynamic Visual Interpretations")
    
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        # 1. Open Interest Structural Deltas Chart
        oi_fig = go.Figure(data=[
            go.Bar(name='CE OI Change', x=['Call Options (CE)'], y=[ce_oi_net], marker_color='#ef4444' if ce_oi_net < 0 else '#10b981'),
            go.Bar(name='PE OI Change', x=['Put Options (PE)'], y=[pe_oi_net], marker_color='#ef4444' if pe_oi_net < 0 else '#10b981')
        ])
        oi_fig.update_layout(title="Net Open Interest (OI) Volume Shift", template="plotly_dark")
        st.plotly_chart(oi_fig, use_container_width=True)
        
    with g_col2:
        # 2. PCR Gauge Chart
        pcr_fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = pcr_curr,
            delta = {'reference': pcr_prev, 'position': "top"},
            title = {'text': "Put-Call Ratio (PCR) Velocity"},
            gauge = {
                'axis': {'range': [None, 2]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, 0.7], 'color': "#450a0a"},
                    {'range': [0.7, 1.3], 'color': "#1e293b"},
                    {'range': [1.3, 2], 'color': "#064e3b"}
                ],
                'threshold': {
                    'line': {'color': "yellow", 'width': 4},
                    'thickness': 0.75,
                    'value': pcr_curr}
            }
        ))
        pcr_fig.update_layout(template="plotly_dark")
        st.plotly_chart(pcr_fig, use_container_width=True)

    # 3. Micro Price Action Shifts Chart
    price_fig = go.Figure()
    price_fig.add_trace(go.Scatter(x=['Previous', 'Current'], y=[row_p['CE Price'], row_c['CE Price']], mode='lines+markers', name='CE Premium Matrix', line=dict(color='#3b82f6', width=3)))
    price_fig.add_trace(go.Scatter(x=['Previous', 'Current'], y=[row_p['PE Price'], row_c['PE Price']], mode='lines+markers', name='PE Premium Matrix', line=dict(color='#f59e0b', width=3)))
    price_fig.add_trace(go.Scatter(x=['Previous', 'Current'], y=[selected_strike, selected_strike], mode='lines', name='Strike Level Reference', line=dict(dash='dash', color='gray')))
    price_fig.update_layout(title="Premium Trajectory (Tracking Historical Value Shift)", template="plotly_dark", yaxis_title="Premium Unit Value")
    st.plotly_chart(price_fig, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: Fibonacci & Golden Ratio Structuring
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("🌀 Mathematical Levels Mapping")
    
    # Calculate unified ranges over prices for the options
    all_prices = [row_c['CE Price'], row_c['PE Price'], row_p['CE Price'], row_p['PE Price']]
    high_watermark = max(all_prices)
    low_watermark = min(all_prices)
    
    if high_watermark == low_watermark:
        high_watermark += 10 # Prevent computational divide by zero or straight line anomalies
        
    fib_levels = calc_fibonacci_levels(high_watermark, low_watermark)
    
    f_col1, f_col2 = st.columns([1, 2])
    
    with f_col1:
        st.markdown("**Computed Retracement Structural Array**")
        for key, value in fib_levels.items():
            st.markdown(f"**{key}**: `{value:.2f}`")
            
    with f_col2:
        # Plotly mapping of Fibonacci Array
        fib_fig = go.Figure()
        colors = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#6366f1']
        
        for (lvl_name, lvl_val), color in zip(fib_levels.items(), colors):
            fib_fig.add_trace(go.Scatter(
                x=[0, 1], y=[lvl_val, lvl_val],
                mode="lines+text",
                name=lvl_name,
                text=["", lvl_name],
                textposition="top left",
                line=dict(color=color, dash="dash")
            ))
            
        # Add marks for Current State Premiums
        fib_fig.add_trace(go.Scatter(x=[0.5], y=[row_c['CE Price']], mode="markers+text", text=["Current CE Value"], marker=dict(size=12, color="#3b82f6"), name="Current CE Value"))
        fib_fig.add_trace(go.Scatter(x=[0.5], y=[row_c['PE Price']], mode="markers+text", text=["Current PE Value"], marker=dict(size=12, color="#f59e0b"), name="Current PE Value"))
        
        fib_fig.update_layout(title="Fibonacci Grid Retracement Map", template="plotly_dark", xaxis_visible=False, showlegend=True)
        st.plotly_chart(fib_fig, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: Contradiction Engine & Strategy Core
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("🎯 System Dynamic Synthesis Engine")
    
    # 1. Evaluate Contradictions First
    contradictions = []
    
    # CE Contradictions
    if ce_oi_net > 0 and ce_p_chg_pct < 0:
        contradictions.append("⚠️ **Call Options Structural Contradiction**: CE Open Interest is growing while Premium Prices are sliding. This points explicitly towards heavy institutional Short Selling / Call Writing (Bearish Signal).")
    elif ce_oi_net < 0 and ce_p_chg_pct > 0:
        contradictions.append("⚠️ **Call Options Structural Contradiction**: CE Open Interest is decreasing while Prices are increasing. This indicates an explosive Short Covering rally (Bullish Momentum Shift).")
        
    # PE Contradictions
    if pe_oi_net > 0 and pe_p_chg_pct < 0:
        contradictions.append("⚠️ **Put Options Structural Contradiction**: PE Open Interest is expanding while Premium Prices are decaying. This confirms institutional Short Selling / Put Writing (Bullish Cushion Floor).")
    elif pe_oi_net < 0 and pe_p_chg_pct > 0:
        contradictions.append("⚠️ **Put Options Structural Contradiction**: PE Open Interest is collapsing while Prices are ascending. This signals urgent Put Seller liquidation / Long unwinding (Bearish Pressure Spike).")
        
    # Macro Sentiment Divergences
    if pcr_curr < 0.7 and (ce_p_chg_pct > 0 or pe_p_chg_pct < 0):
        contradictions.append("⚠️ **Macro Structural Disconnection**: Overall Put-Call Ratio (PCR) is highlighting deeply oversold/bearish ranges, yet immediate short-term premium shifts suggest structural buyer support.")
    elif pcr_curr > 1.3 and (pe_p_chg_pct > 0 or ce_p_chg_pct < 0):
        contradictions.append("⚠️ **Macro Structural Disconnection**: Overall Put-Call Ratio (PCR) flags highly bullish over-extension, yet modern option board premium shifts show immediate underlying selling force.")

    st.markdown("### Step 1: Structural Contradiction Inspection Engine")
    if contradictions:
        for con in contradictions:
            st.markdown(f"<div class='contradiction-box' style='margin-bottom:10px;'>{con}</div>", unsafe_with_html=True)
    else:
        st.success("✅ Clean Structural Matrix: No deep mathematical divergence patterns noticed. Standard indicator configurations align normally.")

    # 2. Formulate Strategy Matrix
    st.markdown("---")
    st.markdown("### Step 2: Algorithmic Strategy Formulations")
    
    # Process Strategy Variables
    ce_strat, ce_reason = "HOLD / NEUTRAL", "Indeterminate balance conditions exist on the board."
    pe_strat, pe_reason = "HOLD / NEUTRAL", "Indeterminate balance conditions exist on the board."
    
    # Simplified Logic Trees incorporating structural cues
    # Call Option Framework
    if ce_oi_net > 0 and ce_p_chg_pct < 0:
        ce_strat = "SELL / WRITE"
        ce_reason = "Aggressive institutional Call Selling taking place. Heavy overhead barrier expected near Fibonacci levels."
    elif ce_oi_net < 0 and ce_p_chg_pct > 0:
        ce_strat = "BUY / LONG"
        ce_reason = "Short covering rally active. Upper limits likely expanding beyond local retracements."
    elif ce_oi_net > 0 and ce_p_chg_pct > 0:
        ce_strat = "BUY / LONG"
        ce_reason = "Aggressive Long Build Up identified. Buyers paying higher premiums willingly."

    # Put Option Framework
    if pe_oi_net > 0 and pe_p_chg_pct < 0:
        pe_strat = "SELL / WRITE"
        pe_reason = "Strong floor construction via Put Writing. Premium bleeding favors sellers near support grids."
    elif pe_oi_net < 0 and pe_p_chg_pct > 0:
        pe_strat = "BUY / LONG"
        pe_reason = "Put Short Covering and panic liquidations. Downside acceleration risks are compounding."
    elif pe_oi_net > 0 and pe_p_chg_pct > 0:
        pe_strat = "BUY / LONG"
        pe_reason = "Aggressive Long Build Up on Put premiums. Market hedging or targeting lower price tiers."

    s_col1, s_col2 = st.columns(2)
    
    with s_col1:
        st.markdown(f"""
        <div class="strategy-box">
            <h4>🔵 CALL OPTION (CE) ACTION: {ce_strat}</h4>
            <p><strong>Strategic Rationalization:</strong> {ce_reason}</p>
            <p style='font-size:0.85rem; opacity:0.85;'>Current Premium: {row_c['CE Price']} | PCR Context: {pcr_curr:.2f}</p>
        </div>
        """, unsafe_with_html=True)
        
    with s_col2:
        st.markdown(f"""
        <div class="strategy-box" style="background-color: #1e1b4b; border-color: #6366f1; color: #e0e7ff;">
            <h4>🟡 PUT OPTION (PE) ACTION: {pe_strat}</h4>
            <p><strong>Strategic Rationalization:</strong> {pe_reason}</p>
            <p style='font-size:0.85rem; opacity:0.85;'>Current Premium: {row_c['PE Price']} | PCR Context: {pcr_curr:.2f}</p>
        </div>
        """, unsafe_with_html=True)

    st.sidebar.markdown("---")
    st.sidebar.success("📊 Dashboard Compute Pipeline Complete.")
