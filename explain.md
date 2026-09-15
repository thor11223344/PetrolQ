# PetrolQ (eRTMAC-NWIS): 5-Minute Master Presentation & Live Demo Script
**Problem Statement Document:** `problem_statement.md`  
**Problem Statement ID:** 26121 (Oil India Limited — Smart Automation)  
**Target Time:** Exactly 5 Minutes (Live Web App Demonstration)

> [!NOTE]
> All problems below are quoted **word-for-word** directly from the official [`problem_statement.md`](file:///c:/Users/MOHITH/Downloads/sih_2026/problem_statement.md).

---

## 5-Minute Click-by-Click Live Demo Guide

Keep `http://localhost:5173` open on the screen and execute the following steps in sequence:

---

### Minute 0:00 – 0:40 | Step 1: Geospatial Radius Map
* **Exact Problem from `problem_statement.md`:**
  * *Problem Description (i):* **"Display nearby wells on a geospatial map relative to the active well."**
  * *Expected Outcome (ii):* **"Provide an interactive map-based visualization of nearby wells within a user-defined radius."**
* **Exact Web App Action (The Click):**
  1. Point to the interactive map on the left.
  2. Click the preset button **`Cluster (30km)`** or drag the **Inspection Radius Slider**.
  3. Hover over an in-radius well (Cyan) and an out-of-radius well (Grey) to reveal the tooltip.
* **What to Say (Spoken Script):**
  > *"Respected Judges, first, addressing **Problem Description (i) and Expected Outcome (ii)**: our **Geospatial Intelligence Engine**. Rather than submitting slow GIS requests, our platform uses PostGIS to instantly project offset wells around our active rig (`OIL-BAGHJAN-1`).*
  >
  > *Watch: as I set the inspection radius to 30 km, nearby wells illuminate in bright Cyan with real-time geodetic distance tags, while distant rigs fade into grey. The HUD instantly computes that 3 historical wells exist in our reservoir block."*

---

### Minute 0:40 – 1:20 | Step 2: Document Ingestion (OCR & Data Extraction)
* **Exact Problem from `problem_statement.md`:**
  * *Background Problem:* **"Historical drilling knowledge currently resides across numerous well completion reports, drilling reports, PDF documents, and individual experience, making retrieval time-consuming and dependent on individual experience & memory."**
  * *Expected Outcome (i):* **"Use AI, NLP, OCR, and data analytics to automatically extract and structure information from historical drilling reports and well documents."**
* **Exact Web App Action (The Click):**
  1. Click **"Upload Document"** in the top navigation bar.
  2. Select `OIL-HAPJAN-1_welllog.las` or a sample PDF report and click **"Process Document"**.
* **What to Say (Spoken Script):**
  > *"Second, addressing **Expected Outcome (i)**: solving the data trap. Decades of Oil India knowledge sit unread in scanned PDFs. Our backend ingestion pipeline runs automated OCR and tabular parsing.*
  >
  > *In seconds, it converts messy mud tables, casing depths, and operational incident logs from raw documents into structured database records, ready for real-time decision support."*

---

### Minute 1:20 – 2:00 | Step 3: Searchable Incident Knowledge Repository
* **Exact Problem from `problem_statement.md`:**
  * *Problem Description (ii):* **"Provide instant access to historical drilling experiences and operational events from offset wells."**
  * *Expected Outcome (iii):* **"Create a searchable knowledge repository of drilling events, lessons learned, operational challenges, and mitigation measures."**
* **Exact Web App Action (The Click):**
  1. Click the **"Knowledge Search"** input box (or Knowledge Base tab).
  2. Type: `stuck pipe in Barail formation` and press **Enter**.
* **What to Say (Spoken Script):**
  > *"Third, addressing **Expected Outcome (iii)**: **Instant Institutional Memory**. When an engineer faces high torque, keyword search fails because drillers use different jargon.*
  >
  > *With our vector semantic search, the engineer types in plain English: 'stuck pipe in Barail formation'. In under 200 milliseconds, the system pulls up the exact historical incident from offset well `OIL-BAGHJAN-1` and displays the exact mitigation recipe that freed the pipe."*

---

### Minute 2:00 – 2:40 | Step 4: Stratigraphy Correlation & 3D Trajectory
* **Exact Problem from `problem_statement.md`:**
  * *Problem Description (iii):* **"Correlate drilling parameters, reservoir characteristics, mud losses, kicks, stuck pipe incidents, casing programs, cementing practices, and formation-specific risks across wells."**
  * *Expected Outcome (iv):* **"Correlate geological, drilling, and reservoir data across wells based on depth and formation."**
  * *Data Availability (vii):* **"Well trajectory and survey data"**
* **Exact Web App Action (The Click):**
  1. Point to the central **Stratigraphy Column** showing *Tipam Sandstone*, *Girujan Clay*, and *Barail Formation*.
  2. Click **"View 3D Subsurface Trajectory"**, left-click and drag to rotate the wellbore in 3D, then close or keep in split-view.
* **What to Say (Spoken Script):**
  > *"Fourth, addressing **Problem Description (iii) and Expected Outcome (iv)**: **Subsurface Correlation**. Wells have different ground elevations and inclinations, making raw measured depth misleading.*
  >
  > *We correlate live depth directly against real published Upper Assam stratigraphy. Drillers see the high-loss Tipam sand and the overpressured Barail kick zone. In 3D space, our WebGL trajectory viewer renders the true directional path navigating through these formation surfaces."*

---

### Minute 2:40 – 3:40 | Step 5: Predictive Analytics for Drilling Risks (Ahead of the Bit)
* **Exact Problem from `problem_statement.md`:**
  * *Problem Description (iv):* **"Generate proactive alerts when current drilling operations approach depths or formations where similar challenges were encountered in nearby wells."**
  * *Expected Outcome (v):* **"Develop predictive analytics models that can identify potential drilling risks such as mud losses, stuck pipe, overpressure zones, torque spikes, or cementing issues based on historical offset-well behaviour."**
* **Exact Web App Action (The Click):**
  1. Click the green **"Play Simulation"** button.
  2. Watch the live gauges (ROP, RPM, Mud Weight, WOB) stream over WebSockets at 1 Hz.
  3. Point to the **Risk Meter** climbing to **Red** and the **Risk Stream Alert** flashing.
* **What to Say (Spoken Script):**
  > *"Fifth, our core innovation addressing **Expected Outcome (v)**: **Proactive Lookahead Risk Prediction**.*
  >
  > *Watch the telemetry stream over WebSockets at 1 Hz, simulating OIL's eRTMAC system. Instead of waiting for a kick to happen, our Hybrid Engine—80% Drilling Physics (Teale MSE and Eaton Pore Pressure) plus 20% LightGBM—scans **250 meters ahead of the drill bit**.*
  >
  > *Notice the red alert: it warns of an impending gas kick in the Barail formation **20 minutes before the bit reaches it**, with SHAP explainability proving that 42% of the risk is driven by torque spikes and escalating pore pressure."*

---

### Minute 3:40 – 4:20 | Step 6: Real-Time Alerts & Validated Recommendations
* **Exact Problem from `problem_statement.md`:**
  * *Expected Outcome (vi):* **"Generate real-time alerts and recommendations to assist drilling engineers in proactive decision-making."**
* **Exact Web App Action (The Click):**
  1. Click directly on the **Red Alert Card** in the Risk Stream.
  2. Point to the **Guardrail Status** and **Recommended Action** (e.g., *Increase Mud Weight to 1.15 SG*).
* **What to Say (Spoken Script):**
  > *"Sixth, fulfilling **Expected Outcome (vi)**: **Zero AI Hallucinations**. Generic LLMs can suggest dangerous parameters that fracture the formation and cause a blowout.*
  >
  > *Every recommendation in PetrolQ is programmatically bounded by our **Pore Pressure vs. Fracture Gradient (PP-FG) Guardrails**. The system recommends increasing mud weight to 1.15 SG—verifying that it stays safely below the 1.35 SG rock fracture limit."*

---

### Minute 4:20 – 5:00 | Step 7: Dual-Persona Dashboard for Field & Office Personnel
* **Exact Problem from `problem_statement.md`:**
  * *Expected Outcome (vii):* **"Present information through a user-friendly dashboard for field and office-based personnel."**
* **Exact Web App Action (The Click):**
  1. Click the **Mode Toggle** at the top right from **"Field Mode"** to **"Office Reviewer"**.
  2. Show the Pre-Spud Dossier and well log analysis view.
* **What to Say (Spoken Script):**
  > *"Finally, satisfying **Expected Outcome (vii)**: a **Dual-Persona Dashboard**.*
  >
  > *With one toggle, the driller on the rig floor gets high-contrast, distraction-free gauges, while the chief drilling superintendent at Oil India headquarters accesses the full Pre-Spud Dossier and historical log backtester.*
  >
  > *In conclusion, PetrolQ directly answers every single clause of the problem statement: it equips Oil India Limited with institutional memory, saving crores in non-productive time. Thank you, and we are ready for your questions!"*

---

## Direct Cross-Reference Table: `problem_statement.md` vs. PetrolQ

| Clause in `problem_statement.md` | Exact Text from Document | Solution Built in PetrolQ |
|---|---|---|
| **Background** | *"Historical drilling knowledge currently resides across numerous WCRs, DDRs, PDFs... retrieval time-consuming"* | **Automated OCR & Document Ingestion (`ingest.py`)** |
| **Problem Description (i)** | *"Display nearby wells on a geospatial map relative to active well"* | **PostGIS Geospatial Map with Dynamic Radius (5–50 km)** |
| **Problem Description (ii)** | *"Instant access to historical drilling experiences and operational events"* | **Vector Semantic Knowledge Search (<200 ms retrieval)** |
| **Problem Description (iii)** | *"Correlate drilling parameters, reservoir characteristics, mud losses, kicks, stuck pipe across wells"* | **Stratigraphy Correlation Column (Upper Assam Formations)** |
| **Problem Description (iv)** | *"Generate proactive alerts when operations approach depths/formations where challenges occurred"* | **250m Lookahead Hybrid Risk Engine (80% Physics + 20% ML)** |
| **Expected Outcome (i)** | *"AI, NLP, OCR... automatically extract and structure information from reports"* | **OCR & LAS Log Extractor with Tabular Parser** |
| **Expected Outcome (ii)** | *"Interactive map-based visualization within user-defined radius"* | **Concentric Radius Circles & Operational Presets** |
| **Expected Outcome (iii)** | *"Searchable knowledge repository of drilling events, lessons, mitigations"* | **FAISS Embedding Index for Historical OIL Incidents** |
| **Expected Outcome (iv)** | *"Correlate geological, drilling, and reservoir data across wells based on depth"* | **TVD vs. MD Geological Stratigraphy Alignment** |
| **Expected Outcome (v)** | *"Predictive analytics models for mud losses, stuck pipe, overpressure, torque spikes"* | **LightGBM + Teale MSE + Eaton with SHAP Root Cause** |
| **Expected Outcome (vi)** | *"Real-time alerts and recommendations to assist drilling engineers"* | **1 Hz Telemetry Alert Stream with PP-FG Safety Guardrails** |
| **Expected Outcome (vii)** | *"User-friendly dashboard for field and office-based personnel"* | **Dual-Mode UI: Field Driller Cockpit vs. Office Reviewer Dossier** |
| **Data Availability (vii)** | *"Well trajectory and survey data"* | **Interactive 3D Subsurface Trajectory Viewer (WebGL)** |
