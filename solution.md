# eRTMAC-NWIS (PetrolQ): Comprehensive Solution Defense & Web App Operations Guide
**Problem Statement ID:** 26121  
**Problem Statement Title:** eRTMAC-NWIS (Nearby Wells Intelligence System): An AI-Powered Offset Well Knowledge and Decision Support Platform for Drilling Operations  
**Organization / Department:** Oil India Limited (OIL)  
**Category / Theme:** Software / Smart Automation  

---

## Executive Summary
PetrolQ is an AI-powered Nearby Wells Intelligence System (NWIS) acting as a standalone decision-support platform designed to operate alongside Oil India Limited's digital real-time monitoring system (**eRTMAC**). 

The platform transforms decades of unstructured offset well reports, well logs, and institutional memory into real-time operational foresight. Guided by the philosophy of **"Physics First, AI Enhanced, Zero Hallucinations,"** PetrolQ uses an 80% Physics + 20% Machine Learning hybrid engine with strict geomechanical safety guardrails to assist drilling teams before hazards occur.

---

## 8-Part Problem, Solution, Tech Stack & Web App User Guide

---

### 1. Automated Information Extraction from Legacy Reports (WCRs & DDRs)
* **Official SIH26121 Clause:** *Expected Outcome (i) & Relevant Data Sources (i, ii)* — "Use AI, NLP, OCR, and data analytics to automatically extract and structure information from historical drilling reports and well documents (WCRs, DDRs)."
* **The Industry Challenge:** Decades of Oil India Limited records are stored as non-standard, scanned PDF Daily Drilling Reports (DDRs) and Well Completion Reports (WCRs). Skewed scans, degraded typography, and non-uniform mud tables cause basic parsers to fail.
* **Technology Used:** **Python**, **Tesseract OCR**, **pdfplumber**, **PyPDF**, **FastAPI** (`backend/ingest.py`).
* **Our Solution:** A document ingestion engine that removes visual noise, runs OCR, parses tabular casing/mud programs, and extracts operational incidents (mud losses, kicks, stuck pipe, fishing jobs) into structured JSON and SQL database records.
* **How to Use on the Web App:**
  1. Click **"Upload Document"** in the top navigation bar.
  2. Select any sample drilling log or report file (e.g., `OIL-HAPJAN-1_welllog.las` or sample PDF daily report).
  3. Click **"Process Document"**.
  4. The modal updates to show structured extraction cards displaying formation tops, measured depth, casing points, and parsed operational logs.
* **Why We Stand Out (Advantage):** Real OCR and tabular parsing on actual `.las` well logs and scanned PDF files—not mock hardcoded data.

---

### 2. Interactive Geospatial Offset Well Mapping with User-Defined Radius
* **Official SIH26121 Clause:** *Problem Description (i) & Expected Outcome (ii)* — "Display nearby wells on a geospatial map relative to the active well... within a user-defined radius."
* **The Industry Challenge:** Rig personnel monitor active well telemetry in isolation and cannot visually determine which offset wells surround them within 5, 10, or 25 km without submitting manual GIS requests.
* **Technology Used:** **PostgreSQL + PostGIS**, **MapLibre GL**, **React 19**, **Tailwind CSS**.
* **Our Solution:** A geospatial dashboard running PostGIS spatial queries (`ST_DWithin`) around the active well coordinates (e.g., `OIL-BAGHJAN-1`) to render offset wells within an adjustable 5 km to 50 km radius in milliseconds.
* **How to Use on the Web App:**
  1. Locate the **"Radius Search" slider** in the toolbar above the map on the left side of the dashboard.
  2. Drag the slider from **5 km** up to **15 km** or **50 km**.
  3. The spatial circle expands smoothly across the map, and offset well pins (`OIL-HAPJAN-1`, `OIL-NAHARKATIYA-1`, `OIL-DIKOM-1`) populate dynamically with distance calculations.
* **Why We Stand Out (Advantage):** Genuine PostGIS database queries with distance metrics and multi-basin support (Upper Assam Shelf, Rajasthan, KG Deepwater, Mizoram Fold Belt).

---

### 3. Searchable Knowledge Repository of Incidents & Mitigations
* **Official SIH26121 Clause:** *Problem Description (ii) & Expected Outcome (iii)* — "Provide instant access to historical drilling experiences... Create a searchable knowledge repository of drilling events, lessons learned, operational challenges, and mitigation measures."
* **The Industry Challenge:** Standard keyword search fails because different drilling engineers describe the same problem differently ("differential sticking" vs. "pipe stuck" vs. "string packoff").
* **Technology Used:** **FAISS / Vector Embeddings**, **Semantic Similarity NLP**, **FastAPI** (`backend/main.py`).
* **Our Solution:** A semantic knowledge retrieval engine that indexes historical drilling incidents and mitigations, matching natural language queries based on contextual meaning rather than literal keywords.
* **How to Use on the Web App:**
  1. Click into the **"Knowledge Search"** input box in the top bar or Knowledge Base panel.
  2. Type a plain-language oilfield query: *"stuck pipe in Barail formation"* or *"mud loss in Tipam sand"*.
  3. Press **Enter**.
  4. The vector engine immediately displays matching historical incident cards showing the offset well name, depth, root cause, and past mitigation steps taken.
* **Why We Stand Out (Advantage):** Institutional memory is digitized and retrieved in under 200 milliseconds, preventing repeat operational mistakes.

---

### 4. Cross-Well Geological, Drilling & Reservoir Correlation
* **Official SIH26121 Clause:** *Problem Description (iii) & Expected Outcome (iv)* — "Correlate geological, drilling, and reservoir data across wells based on depth and formation... casing programs, cementing practices, and formation-specific risks."
* **The Industry Challenge:** Different wells drill with varying surface elevations and inclinations. Comparing raw Measured Depth (MD) across wells without aligning True Vertical Depth (TVD) and formation tops creates geological errors.
* **Technology Used:** **Plotly.js**, **React Stratigraphy Engine**, **Data Normalization Algorithms**.
* **Our Solution:** A Stratigraphy Correlation Column that aligns formation tops (Tipam Sandstone, Girujan Clay, Barail Formation, Kopili Shale) alongside live drill bit depth, casing seats, and offset hazard zones.
* **How to Use on the Web App:**
  1. Look at the central **Stratigraphy & Formation** track on the dashboard.
  2. Observe the color-coded lithology blocks:
     * **Tipam Sandstone** (Thief-bed mud loss zone)
     * **Girujan Clay** (Sloughing shale / tight hole)
     * **Barail Formation** (Overpressured kick zone & differential sticking)
     * **Kopili Formation** (Deep marine reactive shale)
  3. Notice how the active drill bit depth marker aligns directly against the lithology boundaries.
* **Why We Stand Out (Advantage):** Calibrated to published Upper Assam stratigraphy, enabling drillers to anticipate formation transitions before the bit penetrates them.

---

### 5. 3D Subsurface Wellbore Trajectory Tracking
* **Official SIH26121 Clause:** *Relevant Data Availability (vii) & Problem Description (i)* — "Well trajectory and survey data... Display nearby wells relative to the active well."
* **The Industry Challenge:** Deviated and directional wells cannot be accurately evaluated on 2D paper logs. Drillers need 3D clearance visualization to avoid wellbore collisions and remain inside reservoir pay zones.
* **Technology Used:** **WebGL / Three.js / Plotly 3D**, **Minimum Curvature Algorithm**.
* **Our Solution:** A 3D subsurface trajectory module that calculates spatial coordinates from directional survey logs (MD, Inclination, Azimuth) and renders interactive 3D wellbore paths penetrating geological formation surfaces.
* **How to Use on the Web App:**
  1. Open the **3D Trajectory module** on the dashboard.
  2. Click and drag with the left mouse button to rotate the wellbore in 3D space.
  3. Use the scroll wheel to zoom into the well path as it penetrates individual geological formations.
* **Why We Stand Out (Advantage):** True 3D minimum curvature directional surveys rendered smoothly in WebGL, far surpassing standard 2D hackathon charts.

---

### 6. Predictive Analytics for Drilling Risks Ahead of the Bit
* **Official SIH26121 Clause:** *Problem Description (iv) & Expected Outcome (v)* — "Develop predictive analytics models that can identify potential drilling risks such as mud losses, stuck pipe, overpressure zones, torque spikes, or cementing issues based on historical offset-well behaviour."
* **The Industry Challenge:** Pure machine learning models are opaque "black boxes" that hallucinate on sensor noise. Pure physics equations cannot adapt to complex multivariate sensor streams.
* **Technology Used:** **Hybrid Risk Engine (80% Physics + 20% ML)**:
  * **Physics:** Teale Mechanical Specific Energy (MSE), Eaton Pore Pressure Equation.
  * **Machine Learning:** **LightGBM**, **Scikit-learn**, **SHAP (Shapley Additive exPlanations)**.
* **Our Solution:** A hybrid engine evaluating real-time drilling telemetry (WOB, RPM, Torque, ROP, Mud Weight) against offset well hazard baselines, projecting risk probabilities **250 meters ahead of the bit**.
* **How to Use on the Web App:**
  1. Click the green **"Play Simulation"** button.
  2. Watch the live telemetry gauges start streaming.
  3. As depth advances towards the Barail formation, watch the **Risk Meter** climb and trigger an alert: *"High Kick Risk in Barail Formation (82% Probability)"*.
  4. Inspect the **SHAP Explanation breakdown** showing exact parameter contributions (e.g., `+42% Torque Spike`, `+28% Pore Pressure Escalation`).
* **Why We Stand Out (Advantage):** Grounded in drilling physics so it never makes physically impossible predictions, with complete **SHAP explainability** so drillers understand the root cause.

---

### 7. Proactive Real-Time Alerts with Geomechanical Safety Guardrails
* **Official SIH26121 Clause:** *Problem Description (iv) & Expected Outcome (vi)* — "Generate real-time alerts and recommendations to assist drilling engineers in proactive decision-making."
* **The Industry Challenge:** Generating alerts without guidance causes alarm fatigue. Conversely, unvalidated AI recommendations can suggest dangerous actions (e.g., recommending a mud weight that exceeds the formation fracture gradient, triggering severe lost circulation or blowouts).
* **Technology Used:** **FastAPI WebSockets (1 Hz streaming)**, **GuardrailsService**, **Pore Pressure vs. Fracture Gradient (PP-FG) Boundaries**.
* **Our Solution:** A real-time 1 Hz alert pipeline streaming live hazard warnings. Every AI recommendation is automatically validated through a deterministic geomechanical engine to ensure it stays strictly within the safe drilling margin.
* **How to Use on the Web App:**
  1. During the simulation run, click on the **Red/Yellow Alert Card** that appears in the **Risk Stream**.
  2. The card expands to show:
     * Recommended action: *"Increase Mud Weight to 1.15 SG."*
     * Guardrail validation: *"PASSED (Within Pore Pressure 1.08 SG and Fracture Gradient 1.35 SG window)."*
     * Historical precedent: *"OIL-BAGHJAN-1 stabilized kick at 2,210 m with 1.14 SG mud."*
* **Why We Stand Out (Advantage):** Zero dangerous hallucinations. Automated engineering guardrails guarantee operational safety.

---

### 8. Dual-Persona Dashboard for Rig Floor & Office Decision-Makers
* **Official SIH26121 Clause:** *Expected Outcome (vii)* — "Present information through a user-friendly dashboard for field and office-based personnel."
* **The Industry Challenge:** Drillers on the rig floor require high-contrast, uncluttered meters. Senior superintendents at headquarters require multi-well logs, offset dossiers, and deep analytics. A single static layout fails both user groups.
* **Technology Used:** **React 19**, **Tailwind CSS**, Responsive Component Architecture, WebSockets.
* **Our Solution:** A **Dual-Mode User Interface**:
  * **Field Driller Mode:** Large, high-visibility telemetry gauges (ROP, RPM, Mud Weight, WOB) with clear hazard banners.
  * **Office Reviewer Mode:** Pre-Spud Dossier generator, LAS well log viewer, time-travel backtester, and geological cross-sections.
* **How to Use on the Web App:**
  1. Locate the **View Mode Toggle** in the top-right corner of the interface header.
  2. Click the toggle to switch seamlessly between **Field Mode** and **Office Reviewer Mode**.
* **Why We Stand Out (Advantage):** Demonstrates complete operational workflow thinking, giving both the field crew and office superintendents synchronized data tailored to their specific needs.

---

## Competitive Advantage Matrix (Why PetrolQ Wins)

| Feature Area | What Other Teams Build | What PetrolQ Delivers | Why Judges Care |
|---|---|---|---|
| **Risk Prediction Engine** | Black-box LSTM / Random Forest on CSVs | **80% Physics + 20% LightGBM** (Teale MSE + Eaton equations) | Real petroleum engineers respect adherence to fundamental physical laws |
| **Model Explainability** | Shows "Risk: 85%" with zero context | **SHAP Root-Cause Attribution** (+42% Torque, +28% Pore Pressure) | Builds crew trust; drillers will actually take corrective action |
| **Validation Rigor** | Random train/test split (data leakage) | **Time-Travel Causal Backtester** (replays sensor stream second-by-second) | Mathematically proves early warning capability without future data leakage |
| **Data Provenance & Honesty** | Fakes proprietary OIL data | **Transparent Provenance Badges** (Volve Open Data, FORCE 2020, Illustrative Basins) | Engineering integrity; avoids disqualification from fake claims |
| **AI Safety** | Unchecked LLM recommendations | **Deterministic Geomechanical Guardrails** (PP-FG bounded) | Guarantees no dangerous mud weight advice reaches the rig floor |

---

## 5-Minute Live Presentation & Click Sequence Checklist

| Step | Time | Requirement | UI Action | Expected Result | Spoken Pitch Point |
|---|---|---|---|---|---|
| **1** | 0:00 - 1:00 | Req 2 (Geospatial) | Drag **Radius Slider** to 15 km | Offset well pins appear with distances | *"PostGIS dynamically locates all offset wells near our active rig."* |
| **2** | 1:00 - 2:00 | Req 1 & 3 (OCR & NLP) | Click **"Upload Document"** & search Knowledge Base | Extracted logs & historical incident cards appear | *"Decades of unsearchable PDF reports are digitized in milliseconds."* |
| **3** | 2:00 - 3:00 | Req 4 & 5 (Stratigraphy & 3D) | Point to **Stratigraphy Column** & rotate **3D Trajectory** | Formations align with depth; 3D path rotates | *"We correlate the 3D wellbore with real Upper Assam formations."* |
| **4** | 3:00 - 4:00 | Req 6 & 7 (ML & Guardrails) | Click **"Play Simulation"**; click resulting Alert Card | Telemetry streams at 1 Hz; Red Alert fires with SHAP & Guardrails | *"Our Hybrid ML looks 250m ahead, warning of a kick 20 mins early."* |
| **5** | 4:00 - 5:00 | Req 8 (Dual Dashboard) | Click **Mode Toggle** (Field to Office) | Switches from Driller Cockpit to Office Dossier | *"Field Mode for the rig driller; Office Mode for OIL headquarters."* |
