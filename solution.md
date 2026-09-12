# PetrolQ (Nearby Wells Intelligence System) — Solution Architecture & User Guide

---

## 1. Problem Statement Overview

* **Problem Statement Title:** PetrolQ (Nearby Wells Intelligence System): An AI-Powered Offset Well Knowledge and Decision Support Platform for Drilling Operations
* **Organization / Sponsoring Body:** Oil India Limited (OIL), Ministry of Petroleum and Natural Gas
* **Theme / Category:** Smart India Hackathon — Smart Automation / Clean & Green Energy / AI Decision Support
* **Core Mandate:** Develop an AI/ML-enabled, standalone decision-support platform that acts as an **institutional memory** alongside existing real-time rig monitoring systems. The system must transform scattered historical records into active, proactive operational intelligence to eliminate drilling hazards and minimize Non-Productive Time (NPT).
* **Live Deployment Environments:**
  * **Production Web Application (Vercel):** [`https://petrol-q.vercel.app`](https://petrol-q.vercel.app)
  * **Production Backend API (Render):** [`https://petrolq.onrender.com`](https://petrolq.onrender.com)
  * **Production Cloud Database:** Supabase PostgreSQL with PostGIS spatial extensions
  * **Local Offline Rig Appliance:** 100% offline-first execution via `start.bat` on `localhost:5173` / `localhost:8000`

---

## 2. Background: The Real-World Challenge in Simple Terms

When oil companies drill thousands of meters beneath the Earth's surface, they face extreme underground temperatures, unpredictable rock formations, and dangerous pockets of high-pressure gas or fluid loss. 

Before drilling a new well, engineers need to know what happened in neighboring ("offset") wells that were drilled through the exact same underground rock layers in the past. 

### Why This Was Broken Before PetrolQ:
1. **Trapped Knowledge:** Decades of invaluable lessons learned—such as where drill pipes got stuck, where gas kicks occurred, and what mud weights worked—are trapped inside hundreds of static PDF reports, paper files, or inside the memories of senior engineers who retire.
2. **Slow, Manual Searches:** When a driller on a live rig encounters abnormal torque or vibration, finding historical precedents requires hours of manually digging through archives.
3. **Reactive Instead of Proactive:** Existing rig systems only display what is happening *at the current second*. They cannot look 50 meters deeper to warn the driller: *"Slow down! Three neighboring wells hit a sudden high-pressure kick at this exact stratum."*
4. **High Financial Stakes:** A single drilling accident (like a stuck drill string or well blowout) can cause days of Non-Productive Time (NPT), costing millions of dollars and endangering human lives.

---

## 3. Problems from the Problem Statement & Solutions Built

Below is the breakdown of each challenge explicitly stated in the problem statement, the real software solution built inside PetrolQ, and step-by-step instructions on how anyone can use it in the web application.

---

### Problem 1: No Unified Geospatial Map of Nearby Wells
> *"Problem Statement Requirement: Display nearby wells on a geospatial map relative to the active well within a user-defined radius."*

#### The Solution We Built:
* **Interactive Carto Dark Matter GIS Map with Dynamic Radius Search:**
  * Uses **Carto Dark Matter** high-performance raster tiles (`https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png`) with an automatic OpenStreetMap tile fallback.
  * Completely immune to Web Worker worker-loader crashes, CSP, or CORS failures on cloud platforms (Vercel).
  * Accurately displays the Assam-Arakan oilfields (`Baghjan`, `Naharkatiya`, `Dikom`, `Moran`, `Tengakhat`, `Kothaloni`, `Hapjan`, `Shalmari`) with clean borders avoiding disputed geopolitical boundary artifacts.
  * Powered by **PostGIS** spatial indexing (`ST_DWithin`, `ST_Distance`, SRID 4326) to calculate geodesic distances between the active well and all offset wellheads in sub-milliseconds.
  * Dynamic radius search slider (5 km to 50 km) that renders an interactive geospatial radius circle and real-time offset counter.
  * One-click re-centering to shift the platform's operational focus to any offset well.

#### How to Use It in the Webapp:
1. Open the web application ([`https://petrol-q.vercel.app`](https://petrol-q.vercel.app) or `http://localhost:5173`).
2. Look at the **Interactive Field Map** located at the bottom-left on desktop (or tap the **Well Map** tab on mobile).
3. Use the floating **Radius Search Card**:
   * Drag the **Search Radius Slider** (e.g., set to 15 km, 25 km, or 50 km).
   * Notice the circular zone expands and contracts on the map, updating the nearby well counter.
4. Click on any well marker on the map to inspect its well ID, surface coordinates, and total vertical depth (TVD).
5. Click **"Set Selected as Active Rig Location"** to shift the entire platform's real-time focus to that well.

---

### Problem 2: Trapped Historical Reports & Manual Document Review
> *"Problem Statement Requirement: Use AI, NLP, OCR, and data analytics to automatically extract and structure information from historical drilling reports and well documents."*

#### The Solution We Built:
* **Automated AI Document Ingestion Pipeline:**
  * Ingests unstructured **Daily Drilling Reports (DDRs)** and **Well Completion Reports (WCRs)** in PDF format.
  * Uses **OCR & Table Extraction (`pdfplumber` / PyPDF)** to parse tabular operational summaries, depth logs, and incident remarks.
  * Employs an intelligent **NLP Incident Extraction Engine** to parse dense drilling descriptions into structured incidents: Depth (TVD), Stratigraphic Formation, Incident Type (Kick, Stuck Pipe, Loss, Wellbore Instability), Root Cause, Applied Mitigation, and NPT Hours.
  * Automatically calculates **1536-dimensional vector embeddings** (`bge-small-en-v1.5`) and stores them in the PostgreSQL database for semantic search.

#### How to Use It in the Webapp:
1. In the top navigation bar, click the **"Ingest Document"** button.
2. A modal window opens: drag and drop a Daily Drilling Report (a ready-to-test sample is provided in `sample_reports/OIL_Baghjan_DDR_Well_04.pdf`).
3. Select which well this report belongs to.
4. Click **"Extract & Ingest"**.
5. The system parses the document, extracts incidents into clean database records, and displays a success notification.
6. The newly ingested lessons immediately appear at the top of the **Offset Well Intelligence History** timeline on the right drawer.

---

### Problem 3: Instant Access to Offset Well Institutional Memory
> *"Problem Statement Requirement: Create a searchable knowledge repository of drilling events, lessons learned, operational challenges, and mitigation measures."*

#### The Solution We Built:
* **Semantic Vector Knowledge Search Engine (RAG):**
  * Rather than relying on exact keyword matches, engineers can search using everyday conversational language (e.g., *"mud loss in fractured limestone"* or *"pipe stuck while pulling out of hole"*).
  * The search engine computes cosine similarity across stored incident embeddings to find the most relevant historical incidents across all offset wells.
  * Displays similarity scores, incident severity, exact formation depths, root causes, and the exact mitigation steps applied by past engineers.

#### How to Use It in the Webapp:
1. In the top navigation bar, click the **"Knowledge Search"** button (or switch your role to *"Office Reviewer"*).
2. Type any natural language query into the search bar, for example:
   * `high torque while drilling Kopili shale`
   * `mud loss in Tipam sandstone`
   * `kick incident during trip in`
3. Hit **Enter** or click Search.
4. Review the returned historical cards showing:
   * **Well ID & Depth** where the incident occurred.
   * **Root Cause:** What caused the problem.
   * **Mitigation Applied:** The proven corrective action used to solve it.
   * **Semantic Similarity %:** How closely this historical case matches your current query.

---

### Problem 4: Cross-Well Geological and Operational Correlation
> *"Problem Statement Requirement: Correlate geological, drilling, and reservoir data across wells based on depth and formation."*

#### The Solution We Built:
* **Side-by-Side Stratigraphic & Parameter Correlation Matrix:**
  * Compares the active well against chosen offset wells across standardized geological formations (Alluvium, Tipam, Girujan, Barail, Kopili).
  * Plots high-resolution well log curves side-by-side: **Gamma Ray (GR)**, **Resistivity (RES)**, **Density (RHOB)**, and **Sonic Transit Time (DT)**.
  * Displays comparative drilling performance metrics: average Rate of Penetration (ROP), Weight on Bit (WOB), surface Torque, and typical mud weights used in each formation.
  * Allows engineers to spot geological faulting, thickness variations, and lithology changes before the drill bit enters the formation.

#### How to Use It in the Webapp:
1. In the top navigation bar, click the **"Correlations"** button.
2. The **Cross-Well Correlation Matrix** opens in a clean side-by-side view.
3. Select the offset well you wish to compare against the active rig.
4. View the aligned formation tops, log curve comparisons, and historical drilling parameter ranges for each geological layer.

---

### Problem 5: Lack of Early Warnings Before Reaching Hazard Zones
> *"Problem Statement Requirement: Generate proactive alerts when current drilling operations approach depths or formations where similar challenges were encountered in nearby wells."*

#### The Solution We Built:
* **Proactive Lookahead & Hazard Corridor Early Warning Engine:**
  * Continuously evaluates the active drill bit's depth against neighboring formation boundaries within a 250-meter downward window.
  * When the bit comes within **50 meters** of an impending formation boundary or historical hazard corridor, an **Amber Proactive Warning Banner** appears automatically on the dashboard.
  * Details the exact distance remaining, the impending formation name, the historical risks encountered in offset wells, and precautionary recommendations (e.g., *"Prepare LCM spacer; check mud weight before entering Barail sandstone"*).

#### How to Use It in the Webapp:
1. In the **Simulation & Playback Controller** (located at the top-left of the screen), click the **Play** button (`▶`).
2. Watch the **Current Depth (TVD)** meter advance as virtual drilling progresses.
3. When the drill bit enters within 50 meters of a formation transition:
   * An **Amber Lookahead Banner** automatically slides in at the top of the screen.
   * It alerts the crew to the upcoming formation transition and summarizes offset well incidents at that stratum.
4. You can also drag the **Depth Scrubber** slider to jump directly to any depth (e.g., 2,230m or 2,680m) to see how the lookahead responds instantly.

---

### Problem 6: Real-Time Risk Detection & Hazard Classification
> *"Problem Statement Requirement: Develop predictive analytics models that can identify potential drilling risks such as mud losses, stuck pipe, overpressure zones, or torque spikes."*

#### The Solution We Built:
* **Multi-Parameter Physics & ML Risk Classification Engine:**
  * Evaluates high-frequency rig telemetry streams over WebSockets and local sensor models.
  * Integrates trained LightGBM gradient-boosted decision trees with empirical physics metrics (Teale Mechanical Specific Energy, Bingham $d_{xc}$, and Eaton PPFG) to categorize risk into **NORMAL**, **ELEVATED**, **HIGH**, or **CRITICAL**.
  * **Dedicated Rig Physical Telemetry Stream Matrix:**
    * Displays 6 mission-critical physical drilling parameters in dedicated HUD cards:
      1. **Weight on Bit (WOB)** in klbf
      2. **Rotary Speed (RPM)**
      3. **Standpipe Pressure (SPP)** in psi
      4. **Flow Out %**
      5. **Pit Volume Delta ($\Delta$)** in bbl
      6. **Dynamic ECD** in ppg
    * Employs reactive visual alert pulses when parameters breach safe operating bounds.
  * **Tactical Cyber-Console Simulator Controls:**
    * Docked directly beneath the map on desktop (and as a dedicated full screen on mobile).
    * Features status LED, playback buttons (`Play`, `Pause`, `Step +1m`, `Reset`), speed multipliers (`1x`, `2x`, `5x`), and a real-time TVD drill bit seek track.
    * Features a **Scenario Injector** supporting 4 distinct physical simulation states:
      1. **Normal Drilling:** Stable baseline parameters.
      2. **Gas Kick:** Sudden pit volume gain, flow-out surge, and standpipe pressure fluctuations.
      3. **Lost Circulation:** Sudden pit volume loss and drop in return flow percentage.
      4. **Stuck Pipe:** Overpull, sudden RPM drop, and sharp torque spikes.
  * **Client-Side Simulation Isolation (No Cross-Device Interference):**
    * Simulation tick loops, playback status, depth seeking, and scenario selection run strictly within the client's local React session memory.
    * Multiple engineers can test simultaneously (e.g., an evaluator on a mobile phone and a presenter on a laptop) with **zero screen hijacking or cross-talk**, while each device independently queries real-time ML risk predictions for its active simulated depth.

#### How to Use It in the Webapp:
1. In the **Tactical Cyber-Console** docked under the map (or the **Simulator** tab on mobile), find the **"Inject Scenario"** controls (set to *"Normal"*).
2. Change the scenario to **"Gas Kick"**:
   * Watch the **Pit Gain** and **Flow Out** meters immediately spike.
   * A prominent **High-Risk Alert Banner** flashes in red at the top of the right drawer.
   * The system automatically pulls real-time AI mitigation advice tailored to well control.
3. Try switching to **"Stuck Pipe"** or **"Lost Circulation"** to see how the dials, mechanical indicators, and AI recommendations adapt to each physical condition.
4. Use the **1x / 2x / 5x** speed buttons to accelerate virtual drilling, or drag the **TVD Scrubber** to jump to any depth.
5. Switch back to **"Normal"** or click **"Dismiss"** to clear the emergency state.

---

### Problem 7: Pore Pressure & Fracture Gradient (PPFG) Safe Mud Window
> *"Problem Statement Requirement: Correlate drilling parameters, mud losses, kicks, and overpressure zones across wells."*

#### The Solution We Built:
* **Automated Eaton PPFG Calculation Window:**
  * Uses Eaton's sonic and resistivity ratio methods to compute real-time **Pore Pressure Gradient** and **Fracture Gradient** from depth surface to total depth.
  * Visually displays the **"Safe Operating Mud Weight Window"** (the safe zone between the green pore pressure curve and the red fracture gradient curve).
  * Plots the active Equivalent Circulating Density (ECD) in real time to guarantee drillers never drop below pore pressure (causing kicks) or exceed fracture pressure (causing lost circulation).

#### How to Use It in the Webapp:
1. In the top navigation bar, click the **"PPFG Window"** button.
2. An interactive chart displays:
   * **Pore Pressure Gradient (Green curve):** Minimum mud density required to keep formation fluids from entering the wellbore.
   * **Fracture Gradient (Red curve):** Maximum pressure before rock fractures and absorbs drilling mud.
   * **Safe Drilling Window (Shaded region):** Safe operating corridor.
   * **Active Mud Weight (Cyan dashed line):** Shows exactly where your current drilling fluid sits relative to the safety boundaries.

---

### Problem 8: Multi-Well Subsurface Anti-Collision & 3D Proximity
> *"Problem Statement Requirement: Correlate well trajectory and survey data across wells to manage subsurface risks."*

#### The Solution We Built:
* **Interactive 3D Subsurface Trajectory Visualizer & Proximity Radar:**
  * Computes minimum 3D Euclidean distances across directional trajectories between the active wellbore and all neighboring wells.
  * Features an **Anti-Collision Radar** displaying the **Separation Factor (SF)** and warning flags when adjacent wellbores converge within safety thresholds.
  * Includes a full-screen **3D Subsurface Viewer** featuring:
    * 3D wellbore trajectory paths with casing shoes and formation tops.
    * Real-time moving drill bit indicator showing current TVD depth.
    * Hydrocarbon reservoir target zones rendered as 3D subsurface lenses.
    * Stratigraphic geological strata layers with realistic color coding.
    * Multiple view presets: **Plan View (Top-Down)**, **East-West Cross Section**, **North-South Cross Section**, and **Free 3D Orbit**.
    * **Fluid Interaction Guard:** Smooth 60 FPS camera rotation, panning, and zooming even while live simulation streaming is active.

#### How to Use It in the Webapp:
1. In the floating card on the field map, click **"View 3D Subsurface"** (or click the 3D cube icon in the navigation bar).
2. The full-screen 3D Subsurface window opens:
   * **Click and drag** anywhere on the black canvas to freely rotate the subsurface in 3D.
   * **Scroll your mouse wheel** to zoom in and out of the wellbore path.
   * Use the preset camera buttons at the top (**"Plan View"**, **"Section E-W"**, **"Section N-S"**) to instantly switch viewing angles.
   * Toggle **"Offset Wells"**, **"Formation Tops"**, or **"Closest Approach Line"** on/off using the checkboxes.
   * Switch between **Dark Mode** and **Geological Stratigraphy Mode** using the theme toggle.
3. Click the close icon (`✕`) in the top-right corner to return to the main dashboard.

---

### Problem 9: Slow Pre-Spud Well Planning & Reporting
> *"Problem Statement Requirement: Present information through a user-friendly dashboard for field and office-based personnel to support fast, data-driven decisions."*

#### The Solution We Built:
* **One-Click Pre-Spud Offset Intelligence Dossier:**
  * Aggregates all relevant offset well intelligence into an executive, printable briefing dossier before drilling begins.
  * Summarizes nearby well depths, nearest offset proximity, historical kick occurrences, lost circulation events, recommended mud weight schedules, and casing point recommendations.
  * Allows engineers to export well data directly to CSV with a single click.

#### How to Use It in the Webapp:
1. In the top navigation bar, click the **"Pre-Spud Dossier"** button.
2. An executive summary report is generated on the fly, consolidating:
   * Target well coordinates and planned total depth.
   * Closest offset wells and their historical hazard counts.
   * Casing design recommendations and critical formation depths.
3. Click **"Print Dossier"** to generate a clean PDF/paper copy, or click **"Export Well Data"** in the top bar to download complete telemetry and incident logs as a CSV file.

---

### Problem 10: Role-Based Views for Field Rig vs. Headquarters Office
> *"Problem Statement Requirement: Present information through a user-friendly dashboard for field and office-based personnel."*

#### The Solution We Built:
* **Dynamic Role Switcher:**
  * **Field Engineer View:** Emphasizes high-visibility real-time gauges, live telemetry dials, simulation controls, and immediate emergency banners suited for rig-floor consoles.
  * **Office Reviewer View:** Automatically opens deep-dive analytical panels (Cross-Well Correlation Matrix, Semantic Knowledge Search) tailored for subsurface planning teams and drilling superintendents in headquarters.

#### How to Use It in the Webapp:
1. In the top navigation bar, find the **Role Selector** dropdown (defaults to *"Field Engineer"*).
2. Select **"Office Reviewer"**:
   * The interface automatically opens the in-depth correlation and research tools suited for office engineering reviews.
3. Switch back to **"Field Engineer"** to restore the focused rig-floor telemetry layout.

---

### Problem 11: Field Usability & Mobile Rig-Floor Accessibility
> *"Problem Statement Requirement: Provide an accessible, responsive user interface operational across control rooms, rig doghouses, and mobile handheld devices."*

#### The Solution We Built:
* **Mobile-First Ergonomic Architecture & Touch Experience:**
  * Tailored for engineers on the rig floor carrying smartphones or tablets in portrait or landscape orientations (`@media (max-width: 1024px)`).
  * **Compact Mobile Top Bar**: Includes quick active well switcher and one-touch document upload modal trigger.
  * **Mobile Floating HUD**: Docked over the top of the map showing real-time TVD Bit Depth, ROP, and operational Risk status.
  * **Frosted Glass Bottom Navigation Bar**: One-touch thumb switching between 5 primary operational views:
    1. **Well Map:** Full-screen geospatial oilfield map with radius slider and interactive wellheads.
    2. **Telemetry:** Complete 6-parameter physical telemetry sensor matrix (WOB, RPM, SPP, Flow %, Pit Delta, ECD).
    3. **Simulator:** Dedicated touch-first cyber-console with oversized playback buttons, speed selector pills, full-width TVD track, and hazard scenario buttons.
    4. **Radar:** Lookahead hazard corridor and impending formation boundary tracker.
    5. **Offsets:** Slide-up drawer displaying offset well intelligence and historical incident cards.

#### How to Use It on Mobile:
1. Open [`https://petrol-q.vercel.app`](https://petrol-q.vercel.app) in any mobile browser (Chrome, Safari, Firefox).
2. Use the **Bottom Navigation Bar** to glide between Map, Telemetry, Simulator, Radar, and Offsets.
3. In the **Simulator** tab, tap **Play** (`▶`), toggle speeds (1x / 2x / 5x), or tap any scenario pill (Gas Kick, Lost Circulation, Stuck Pipe) to experience real-time rig physics right on your phone.

---

## 4. Summary Table: Problem vs. Solution

| Problem Mentioned in Problem Statement | Solution Implemented in PetrolQ | Where to Access in Webapp |
| :--- | :--- | :--- |
| **1. No geospatial map of nearby wells** | Carto Dark Matter raster GIS map with dynamic 5–50km radius circle & PostGIS spatial indexing | Desktop: Bottom-left map / Mobile: **Well Map** tab |
| **2. Trapped knowledge in PDF drilling reports** | AI OCR & NLP incident extraction pipeline (`pdfplumber` + regex fallback) | Top bar &rarr; **"Ingest Document"** modal |
| **3. Manual, slow searching through archives** | Semantic Vector RAG Search (`bge-small` + cosine similarity) | Top bar &rarr; **"Knowledge Search"** |
| **4. Lack of cross-well geological correlation** | Multi-well side-by-side well log & drilling parameter correlation matrix | Top bar &rarr; **"Correlations"** modal |
| **5. No early warning before hitting hazards** | Proactive 50m Lookahead & Hazard Corridor banner | Desktop header &rarr; Mobile: **Radar** tab |
| **6. Real-time hazard detection & classification** | ML + physics classifier with 6 physical sensors, Cyber-Console, and isolated client sessions | Docked under map &rarr; Mobile: **Simulator** tab |
| **7. Overpressure and mud weight estimation** | Real-time Eaton Pore Pressure & Fracture Gradient (PPFG) window | Top bar &rarr; **"PPFG Window"** |
| **8. Multi-well collision & crowded pad risk** | 3D Subsurface Trajectory Visualizer & Anti-Collision Radar | Map card &rarr; **"View 3D Subsurface"** |
| **9. Time-consuming pre-spud planning** | One-click Automated Pre-Spud Offset Intelligence Dossier | Top bar &rarr; **"Pre-Spud Dossier"** |
| **10. Cluttered UI for different personas** | Field Engineer vs. Office Reviewer role-based operational layouts | Top bar &rarr; **Role Selector** dropdown |
| **11. Inconvenient rig-floor mobile access** | Touch-first mobile shell with fixed frosted bottom navigation & mobile simulator | Open on any smartphone / tablet viewport |

---

## 5. Verification & Codebase Integrity

All solutions described in this document are **100% real, fully implemented, and deployed**:
* **Live Production Cloud Application:** Available at [`https://petrol-q.vercel.app`](https://petrol-q.vercel.app).
* **Live Backend API & ML Inferences:** Operating on Render at [`https://petrolq.onrender.com`](https://petrolq.onrender.com).
* **Production Database:** Supabase PostgreSQL with PostGIS geometry and dense vector storage.
* **100% Offline Mode:** Can run as a completely local rig appliance via `start.bat` on Windows or `npm run dev`.
* **Multi-Device Isolation:** Tested across simultaneous mobile and desktop sessions with zero cross-talk or UI interference.
* **Failure-Free Basemap:** Verified on Carto Dark Matter raster tiles with zero Web Worker or CORS errors.
