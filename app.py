import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# Configuration & Global Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Option Dynamics Pro",
    page_icon="📈",
    layout="wide"
)

# Robust CSS variable definition
CSS_STYLE = """
<style>
    .metric-card {
        background-color: #111827;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 15px;
    }
    .metric-card.bullish { border-left-color: #10b981; }
    .metric-card.bearish { border-left-color: #ef4444; }
    
    .contradiction-box {
        background-color: #450a0a;
        border: 1px solid #f87171;
        border-radius: 10px;
        padding: 15px;
        color: #fca5a5;
        margin: 10px 0px;
    }
    
    .strategy-box {
        background-color: #064e3b;
        border: 1px solid #34d399;
        border-radius: 10px;
        padding: 15px;
        color: #a7f3d0;
        margin: 10px 0px;
    }
</style>
"""
st.markdown(CSS_STYLE, unsafe_with_html=True)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def load_data(file):
    if file is None:
        return None
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        req = ['Strike Price', 'CE Price', 'CE OI', 'PE Price', 'PE OI']
        if not all(col in df.columns for col in req):
            st.error(f"File {file.name} is missing columns: {req}")
            return None
        df = df.apply(pd.to_numeric, errors='coerce')
        return df.dropna(subset=['Strike Price'])
    except Exception as e:
        st.error(f"Error loading {file.name}: {e}")
        return None

def get_fib_levels(high, low):
    diff = high - low
    return {
        "161.8% (Ext)": low + 1.618 * diff,
        "100% (High)": high,
        "61.8% (Ratio)": low + 0.618 * diff,
        "50.0% (Mid)": low + 0.5 * diff,
        "38.2%": low + 0.382 * diff,
        "23.6%": low + 0.236 * diff,
