# PetrolQ: Solution & Architecture Mapping

This document maps the core challenges from the official problem statement to the specific features built into PetrolQ, explains how to use these features on the web application, and highlights the strategic advantages for the jury.

---

## Problem 1: No unified platform to display nearby wells geospatially
**The Problem Statement:** *Currently, drilling teams do not have a unified platform that can display nearby wells on a geospatial map relative to the active well.*

### Our Solution: MapLibre Geospatial Dashboard & Regional Configuration
We built an interactive, 2D geospatial map interface that visualizes the current drilling rig ("Active Well") in relation to all historical offset wells within a defined radius. The platform supports multiple regions (Upper Assam, Rajasthan Basin, KG Deepwater, and Mizoram Fold Belt).

* **How to use it on the Web App:**
  1. Look at the top-left section of the dashboard labeled **"Radius Search"**.
  2. Adjust the slider (e.g., set to 15km).
  3. The map dynamically updates, zooming in and placing interactive pins on historical offset wells that fall within that specific radius.
* **The Advantage (ROI):** Engineers no longer need to rely on static GIS requests or memory. They can instantly visually identify which nearby wells might share the same geological footprint and risks.

---

## Problem 2: Lack of instant access to historical drilling experiences
**The Problem Statement:** *Provide instant access to historical drilling experiences and operational events from offset wells. Information currently resides across numerous unsearchable PDF documents.*

### Our Solution: AI-Powered OCR Ingestion & Semantic Vector Search
We developed a complete NLP pipeline (`ingest.py`) that uses Tesseract OCR to extract text from unstructured PDFs like Daily Drilling Reports (DDR) and Well Completion Reports (WCR). This text is embedded into a vector database for semantic search.

* **How to use it on the Web App:**
  1. Click on the **"Knowledge Base"** tab or the **"Upload DDR/WCR"** button in the modal.
  2. Upload a sample document (like `OIL-HAPJAN-1_welllog.las` or a PDF report).
  3. Use the global search bar to ask natural questions like *"Did Baghjan-1 experience stuck pipe?"*
  4. The system will retrieve the exact paragraph from the historical report.
* **The Advantage (ROI):** What used to take a team of engineers weeks to read through physical or scanned reports now takes milliseconds. Institutional memory is digitized, searchable, and instantly accessible.

---

## Problem 3: Inability to correlate data across multiple wells
**The Problem Statement:** *Correlate drilling parameters, reservoir characteristics, mud losses, kicks, stuck pipe incidents, casing programs, cementing practices, and formation-specific risks across wells based on depth and formation.*

### Our Solution: 3D Subsurface Trajectory & Depth Correlation Panel
We built a dual-view correlation engine. First, a 3D WebGL viewer (Plotly/MapLibre) visualizes the true vertical depth (TVD) and inclination of the wellbore, mapped against formation tops (e.g., Tipam, Barail, Kopili). Second, an interactive Pore Pressure vs. Fracture Gradient (PPFG) chart allows side-by-side comparison.

* **How to use it on the Web App:**
  1. Navigate to the **"Correlation Panel"** (or view the 3D Trajectory module).
  2. Observe the depth tracker as the live telemetry updates. 
  3. Notice how the current bit depth is overlaid on top of the geological formations (e.g., transitioning from Girujan Clay to the high-pressure Barail formation).
* **The Advantage (ROI):** Unprecedented spatial awareness. Drilling engineers can physically "see" when the drill bit is about to cross into a dangerous formation where a neighboring well lost circulation, allowing them to preemptively adjust mud weight.

---

## Problem 4: Absence of proactive, real-time alerts for impending risks
**The Problem Statement:** *Generate proactive alerts when current drilling operations approach depths or formations where similar challenges were encountered in nearby wells. Identify potential risks like mud losses, stuck pipe, overpressure, and torque spikes.*

### Our Solution: The Hybrid Physics-ML Real-Time Risk Engine
We built a real-time WebSocket backend that streams 1Hz rig telemetry (ROP, RPM, Mud Weight, WOB). This stream is fed into our proprietary risk engine that combines traditional petroleum physics equations (Teale MSE, Eaton equation) with an advanced LightGBM machine learning model.

* **How to use it on the Web App:**
  1. On the main dashboard, click the **"Play Simulation"** button.
  2. Watch the live telemetry gauges start moving. 
  3. Keep an eye on the "Risk Stream" or "AI Recommendations" feed.
  4. As the bit depth increases, the system will look 250 meters ahead and suddenly flash a **High Risk** alert (e.g., *"Warning: High stuck pipe risk detected in Barail formation. SHAP explanation: Torque spike + high differential pressure."*)
  5. The LLM Guardrails service ensures the AI's mitigation recommendation (e.g., *"Increase Mud Weight to 1.15 SG"*) is physically safe.
* **The Advantage (ROI):** This is the ultimate cost-saver. A single stuck pipe incident or gas kick can cost millions of dollars in Non-Productive Time (NPT). By providing a 250-meter advance warning with high accuracy (and explaining *why* via SHAP values), operators can change drilling parameters before the disaster happens.
