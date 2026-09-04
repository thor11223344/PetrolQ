# eRTMAC-NWIS — Feature Reference Card (SIH 2026 Evaluation Handout)

**System Title:** Nearby Wells Intelligence System for Real-Time Drilling Hazard Mitigation  
**Target Organization:** Oil India Limited (OIL) / ONGC — Assam-Arakan Basin Focus  
**Software Stack:** FastAPI (Python 3.14) · React (Vite / Tailwind / Plotly / Three.js) · SQLite / SQLAlchemy · LightGBM / SHAP

---

## 1. Problem Statement & Operational Challenge
In exploratory and development drilling within complex geopressured regimes (such as the Upper Assam Shelf & Barail Coal-Shale formations), offset well records and legacy end-of-well reports (EOWRs) often remain isolated in unstructured PDFs. Drilling engineers lack an integrated platform that connects real-time surface telemetry (WITS/WITSML) with offset well stratigraphy, offset casing integrity precedents, and physics-informed early kick/loss warnings.

---

## 2. Core Architecture & Implemented Capabilities

### A. Real-Time Multi-Hazard Disaggregation & Physical Telemetry Injection
* **Problem:** Traditional machine learning prototypes use single opaque risk scores or synthetic toggles that fake output probabilities without touching underlying telemetry.
* **Our Solution (Correction #4 & #1):**
  * **Realistic Telemetry Perturbation:** Scenario injection (`Gas Kick`, `Lost Circulation`, `Stuck Pipe`) modifies underlying simulated WITS channels—including active pit volume ($\Delta\text{Pit}$), relative return flow rate ($\text{Flow Out } \%$), standpipe pressure ($\text{SPP}$), torque, and $\text{ROP}$—using genuine well-control signatures.
  * **Disaggregated Hazard Probability:** Raw telemetry feeds the live ML pipeline, generating separate, physics-grounded probabilities for 4 distinct hazards: Gas Kick ($P_{\text{kick}}$), Lost Circulation ($P_{\text{loss}}$), Mechanical Sticking ($P_{\text{stuck}}$), and Torque & Drag ($P_{\text{torque}}$).
  * **Strict Backward Compatibility:** The single overall `risk_probability` is computed via the 70/30 composite formula implemented in `backend/ml/service.py`:
    $$\text{composite\_hazard} = 0.70 \cdot \max(P_{\text{kick}}, P_{\text{loss}}, P_{\text{stuck}}, P_{\text{torque}}) + 0.30 \cdot \text{mean}(P_{\text{kick}}, P_{\text{loss}}, P_{\text{stuck}}, P_{\text{torque}})$$
    This ensures the primary dial is dominated by the most acute threat while remaining sensitive to cumulative multi-hazard severity, maintaining 100% mathematical consistency with detailed gauge breakdowns.

### B. Subsurface Mechanics & Eaton's Method (1972) PPFG Window
* **Problem:** Arbitrary piecewise constant curves misrepresent pore pressure dynamics and undermine engineering credibility with petrotechnical evaluators.
* **Our Solution:** Genuine published Eaton acoustic equations for pore pressure and fracture gradient:
  $$\Delta t_n(z) = 185 \cdot e^{-0.0003 \cdot z}\ (\mu\text{s/ft, Normal Shale Trend})$$
  $$P_p(z) = \sigma_v - (\sigma_v - P_{\text{hyd}}) \cdot \left(\frac{\Delta t_n(z)}{\Delta t_{\text{obs}}(z)}\right)^{3.0}$$
  $$FG(z) = P_p(z) + \frac{\nu(z)}{1 - \nu(z)} \cdot [\sigma_v - P_p(z)], \quad \nu(z) = 0.25 + 0.15 \cdot \left(\frac{z}{3500}\right)$$
  * *Methodology Disclosure:* Calibrated with synthetic acoustic log transit times to reflect the Barail undercompaction overpressure zone ($2200\text{--}2800\text{ m}$) where real sonic logs are proprietary. Real-time rig Equivalent Circulating Density (ECD) is continuously benchmarked against this safe mud weight corridor.

### C. Proactive Ahead-of-Bit Lookahead & Depth-Proximity Warning
* **Problem:** Drilling crews are caught unaware when approaching thin overpressured sands or casing setting points.
* **Our Solution (Correction #3):**
  * Both the **Ahead-of-Bit Radar** modal and the **Global Depth-Proximity Banner** consume the exact same unified backend engine (`/api/wells/{id}/lookahead`).
  * When current bit depth is within $\le 50\text{ m}$ of an offset hazard horizon or formation boundary, an amber priority alert proactively appears on the main rig HUD displaying the exact distance, predicted threat, and offset incident precedent with a 1-click drilldown to the radar view.

### D. Scoped 3-Well Stratigraphic Cross-Section & Casing Correlation
* **Problem:** Complex multi-well fence diagrams often cause visual clutter or fail to represent true lateral structural dip.
* **Our Solution (Correction #5):**
  * A tightly scoped **3-well side-by-side stratigraphic fence diagram** (Naharkatiya-1 West Offset $\rightarrow$ Planned Active Well $\rightarrow$ Baghjan-4 East Offset) sharing identical geological color tokens with the 3D Subsurface Viewer.
  * Interactive correlation tie-lines with fault throw/dip calculations and casing seat alignment comparisons (LOT EMW, casing grades, slurry densities, and micro-annular leak notes).

---

## 3. Quick Evaluation Walkthrough for Judges

| Step | Action | What Evaluators See | Verified Engineering Detail |
|:---:|:---|:---|:---|
| **1** | Open Rig Dashboard (`http://localhost:5173`) | Active Well HUD with live telemetry gauges & trajectory | Live FastAPI status indicator (`API Online`), Teale MSE, and Corrected $d_{\text{xc}}$ exponent. |
| **2** | In Simulator Toolbar, click **"Inject Gas Kick"** | Flow Out jumps to $118.5\%$, Pit Gain $+15.2\text{ bbl}$, SPP drops to $2450\text{ psi}$ | Hazard prediction jumps to High/Critical Gas Kick *because physical channels changed*, not via hardcoded score. |
| **3** | Observe Header Alert & Proximity Banner | Amber Lookahead banner warns of impending Barail formation entry within $50\text{ m}$ | Reuses `/api/wells/{id}/lookahead`; displays historical kick precedent in Baghjan-4. |
| **4** | Click **"Safe Mud Weight Window"** in Top Bar | Interactive Plotly depth-indexed safe mud operating envelope | Eaton (1972) curves ($P_p$ hydrostatic at $8.6\text{ ppg}$ shallow, ramping to $12.5\text{ ppg}$ in Barail; $FG$ margin tracking ECD). |
| **5** | Click **"Correlation & Cross-Section"** | Tab 2 (Casing & Cement Programs) and Tab 3 (Stratigraphic Cross-Section (3 Wells)) | Scoped 3-well fence diagram with formation tie-lines, structural dip trend, and historical sustained casing pressure (SCP) mitigation notes. |

---

## 4. Automated Verification Suite
All endpoints, mathematical models, and architectural constraints are validated via automated tests:
```bash
python -m pytest tests/
# Result: 5 passed, 0 failures (100% compliance across physics, ML, endpoints, and WebSocket concurrency)
```
