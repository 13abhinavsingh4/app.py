# ⚡ Advanced Option Chain & Fibonacci Dynamics Analyzer

An institutional-grade, highly visual Option Chain parsing and analytical engine engineered inside **Streamlit**. This workspace specializes in tracking macro Open Interest shifts, extracting hidden architectural contradictions across options data matrices, and visualizing key structural price ranges via Fibonacci Golden Ratio layers.

---

## 🛠️ Key Architectural Implementations

1. **Two-Frame Delta Auditing**: Compares an asset's structural shifts by comparing a previous frame sheet directly to a current asset matrix sheet.
2. **Dynamic Strike Isolation**: Instantly isolates a user-selected target strike from the data pool to recalculate specific premiums, delta velocity, and Put-Call Ratio (PCR).
3. **Fibonacci & Golden Extension Layouts**: Auto-calculates key algorithmic retracements ($23.6\%$, $38.2\%$, $50.0\%$, $61.8\%$, and $161.8\%$) dynamically based on real-time option premium ranges.
4. **Contradictions-First Strategy Engine**: Scans data for anomalies (e.g., Short-Covering vs Long Liquidations) before producing an execution strategy.

---

## 📂 Expected Input CSV Format

Both uploaded data files (Previous Day and Current Day) **MUST** match or contain the following column arrays exactly:

| Strike Price | CE Price | CE OI | PE Price | PE OI |
|---|---|---|---|---|
| 18000 | 150.0 | 12500 | 35.0 | 45000 |
| 18100 | 95.5  | 22000 | 72.0 | 19500 |
| 18200 | 42.0  | 51000 | 120.5| 6200  |

> *Note: Column naming validations are auto-stripped of blank structural spaces inside the software parser.*

---

## 🚀 Setting Up Locally

Ensure you have Python 3.9+ environments available locally on your hardware.

### 1. Clone this project repository
```bash
git clone <your-github-repo-link>
cd <project-directory-name>
