# PetrolQ (eRTMAC-NWIS): 5-Minute Master Presentation & Live Demo Script
**Problem Statement ID:** 26121 (Oil India Limited — Smart Automation)  
**Target Time:** 5 Minutes Total (Live Web App Demonstration)

---

## 5-Minute Click-by-Click Live Demo Guide

Keep `http://localhost:5173` open on the screen and execute the following 8 steps in sequence:

---

### Minute 0:00 – 0:40 | Problem 1: Geospatial Offset Well Mapping
* **Problem in Statement:** Drilling teams cannot see nearby offset wells relative to their active rig on an interactive map within a user-defined radius.
* **Exact Web App Action (The Click):**
  1. Point to the interactive map on the left.
  2. Click the preset button **`Cluster (30km)`** or drag the **Inspection Radius Slider**.
  3. Hover over an in-radius well (Cyan) and an out-of-radius well (Grey) to reveal the tooltip.
* **What to Say (Spoken Script):**
  > *"Respected Judges, first, our **Geospatial Intelligence Engine**. Rather than submitting slow GIS requests, our platform uses PostGIS to instantly project offset wells around our active rig (`OIL-BAGHJAN-1`).*
  >
  > *Watch: as I set the inspection radius to 30 km, nearby wells illuminate in bright Cyan with real-time geodetic distance tags, while distant rigs fade into grey. The HUD instantly computes that 3 historical wells exist in our reservoir block."*

---

### Minute 0:40 – 1:20 | Problem 2: Digitizing Legacy PDF & Paper Reports
* **Problem in Statement:** Decades of drilling lessons are trapped in unsearchable PDF Daily Drilling Reports (DDRs) and Well Completion Reports (WCRs).
* **Exact Web App Action (The Click):**
  1. Click **"Upload Document"** in the top navigation bar.
  2. Select `OIL-HAPJAN-1_welllog.las` or a sample PDF report and click **"Process Document"**.
* **What to Say (Spoken Script):**
  > *"Second, solving the data trap. Decades of Oil India knowledge sit unread in scanned PDFs. Our backend ingestion pipeline runs automated OCR and tabular parsing.*
  >
  > *In seconds, it converts messy mud tables, casing depths, and operational incident logs from raw documents into structured database records, ready for real-time decision support."*

---

### Minute 1:20 – 2:00 | Problem 3: Semantic Knowledge Search for Past Incidents
* **Problem in Statement:** Engineers cannot quickly search how past problems (stuck pipe, kicks) were solved in adjacent wells.
* **Exact Web App Action (The Click):**
  1. Click the **"Knowledge Search"** input box (or Knowledge Base tab).
  2. Type: `stuck pipe in Barail formation` and press **Enter**.
* **What to Say (Spoken Script):**
  > *"Third, **Instant Institutional Memory**. When an engineer faces high torque, keyword search fails because drillers use different jargon.*
  >
  > *With our vector semantic search, the engineer types in plain English: 'stuck pipe in Barail formation'. In under 200 milliseconds, the system pulls up the exact historical incident from offset well `OIL-BAGHJAN-1` and displays the exact mitigation recipe that freed the pipe."*

---

### Minute 2:00 – 2:40 | Problem 4 & 5: Stratigraphy Correlation & 3D Trajectory
* **Problem in Statement:** Inability to correlate geological formations by depth across wells or visualize directional trajectories in 3D.
* **Exact Web App Action (The Click):**
  1. Point to the central **Stratigraphy Column** showing *Tipam Sandstone*, *Girujan Clay*, and *Barail Formation*.
  2. Click **"View 3D Subsurface Trajectory"**, left-click and drag to rotate the wellbore in 3D, then close or keep in split-view.
* **What to Say (Spoken Script):**
  > *"Fourth, **Subsurface Correlation**. Wells have different ground elevations and inclinations, making raw measured depth misleading.*
  >
  > *We correlate live depth directly against real published Upper Assam stratigraphy. Drillers see the high-loss Tipam sand and the overpressured Barail kick zone. In 3D space, our WebGL trajectory viewer renders the true directional path navigating through these formation surfaces."*

---

### Minute 2:40 – 3:40 | Problem 6: Predictive Risk Engine Ahead of the Bit (The Climax)
* **Problem in Statement:** Lack of predictive models to forecast drilling risks (kicks, stuck pipe, torque spikes) before entering hazardous zones.
* **Exact Web App Action (The Click):**
  1. Click the green **"Play Simulation"** button.
  2. Watch the live gauges (ROP, RPM, Mud Weight, WOB) stream over WebSockets at 1 Hz.
  3. Point to the **Risk Meter** climbing to **Red** and the **Risk Stream Alert** flashing.
* **What to Say (Spoken Script):**
  > *"Fifth, our core innovation: **Proactive Lookahead Risk Prediction**.*
  >
  > *Watch the telemetry stream over WebSockets at 1 Hz, simulating OIL's eRTMAC system. Instead of waiting for a kick to happen, our Hybrid Engine—80% Drilling Physics (Teale MSE and Eaton Pore Pressure) plus 20% LightGBM—scans **250 meters ahead of the drill bit**.*
  >
  > *Notice the red alert: it warns of an impending gas kick in the Barail formation **20 minutes before the bit reaches it**, with SHAP explainability proving that 42% of the risk is driven by torque spikes and escalating pore pressure."*

---

### Minute 3:40 – 4:20 | Problem 7: Safe Geomechanical Guardrails
* **Problem in Statement:** Alerts without engineering guidance cause alarm fatigue, and unchecked AI can recommend dangerous drilling parameters.
* **Exact Web App Action (The Click):**
  1. Click directly on the **Red Alert Card** in the Risk Stream.
  2. Point to the **Guardrail Status** and **Recommended Action** (e.g., *Increase Mud Weight to 1.15 SG*).
* **What to Say (Spoken Script):**
  > *"Sixth, **Zero AI Hallucinations**. Generic LLMs can suggest dangerous parameters that fracture the formation and cause a blowout.*
  >
  > *Every recommendation in PetrolQ is programmatically bounded by our **Pore Pressure vs. Fracture Gradient (PP-FG) Guardrails**. The system recommends increasing mud weight to 1.15 SG—verifying that it stays safely below the 1.35 SG rock fracture limit."*

---

### Minute 4:20 – 5:00 | Problem 8: Dual-Persona Dashboard (Field vs. Office) & Closing
* **Problem in Statement:** Requirement for a unified dashboard serving both field rig crews and office superintendents.
* **Exact Web App Action (The Click):**
  1. Click the **Mode Toggle** at the top right from **"Field Mode"** to **"Office Reviewer"**.
  2. Show the Pre-Spud Dossier and well log analysis view.
* **What to Say (Spoken Script):**
  > *"Finally, satisfying Clause vii: a **Dual-Persona Dashboard**.*
  >
  > *With one toggle, the driller on the rig floor gets high-contrast, distraction-free gauges, while the chief drilling superintendent at Oil India headquarters accesses the full Pre-Spud Dossier and historical log backtester.*
  >
  > *In conclusion, PetrolQ does not just monitor drilling—it equips Oil India Limited with institutional memory, saving crores in non-productive time. Thank you, and we are ready for your questions!"*

---

## Emergency Presentation Tips:
1. **If time is running short:** Go straight to **Step 6 ("Play Simulation")**—it has moving dials, real-time alerts, and SHAP graphs that immediately capture attention.
2. **If asked about proprietary data:** *"We calibrated our Upper Assam models with the industry-standard Equinor Volve open data and FORCE 2020 benchmark mapped to real Assam lithology, with full architecture ready to plug into OIL's live eRTMAC WITSML stream on day one."*
