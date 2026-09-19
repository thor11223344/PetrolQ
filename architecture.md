# PetrolQ — System Architecture Specification

> **Enterprise-Grade, Offline-First Nearby Wells Intelligence & Real-Time Decision Support System for Oil & Gas Drilling Operations**  
> *Developed for Smart India Hackathon (SIH) 2026*

---

## 1. Executive Summary & Architectural Philosophy

Drilling high-pressure, high-temperature (HPHT) and complex directional wells in structurally intricate fields (such as Upper Assam’s Baghjan, Moran, and Naharkatiya plays) carries extreme risks: wellbore collisions, sudden gas kicks, catastrophic lost circulation, and stuck pipe incidents resulting in millions of dollars in Non-Productive Time (NPT).

**PetrolQ** is engineered as an **offline-first, edge-ready, AI-augmented drilling intelligence platform**. The architecture synthesizes:
1. **Historical Subsurface Intelligence**: High-dimensional geospatial indexing (PostGIS) and Dynamic Time Warping (DTW) well log correlation across offset wells.
2. **Real-Time Physics & ML Hybrid Reasoning**: LightGBM multi-hazard classification coupled with Teale Mechanical Specific Energy (MSE), Bingham $d_{xc}$ exponent, and Eaton Pore Pressure/Fracture Gradient (PPFG) models.
3. **Transparent Explainability**: Local SHAP feature-attribution engine providing actionable engineering recommendations rather than "black-box" predictions.
4. **Resilient Unstructured Document Ingestion**: Dual-mode extraction combining LLM/Ollama semantic parsing with a deterministic regex domain fallback, coupled with vector similarity search.

---

## 2. High-Level System Architecture Diagram

```mermaid
flowchart TB
    subgraph ClientLayer["🖥️ CLIENT PRESENTATION LAYER (React 19 + Vite 8)"]
        UI["Main Mission Control Dashboard (Space Grotesk / Inter / JetBrains Mono)"]
        MapBox["Geospatial Offset Well Map (Carto Dark Matter + MapLibre GL + OSM Fallback)"]
        ThreeD["3D Anti-Collision & Trajectory Viewer (Plotly WebGL)"]
        Radar["Lookahead Hazard Radar & Formation Tracker"]
        PPFG["Eaton PPFG & Mud Weight Window Modal"]
        Correlate["Log Correlation Panel (FastDTW + Stratigraphy)"]
        Dossier["Pre-Spud Engineering Risk Dossier Generator"]
        Console["Tactical Cyber-Console & Physical Telemetry Matrix (6 Sensors)"]
        MobileShell["Mobile Responsive Shell (Bottom Nav, Mobile Simulator, Quick Bar)"]
        ClientSandbox["Client-Isolated Simulation Sandbox (Independent Session State)"]
    end

    subgraph Transport["⚡ PROTOCOL & HYBRID CLOUD TRANSPORT LAYER"]
        REST["REST API (HTTP/JSON over HTTPS)"]
        WS["Bidirectional WebSocket (/api/ws/telemetry / WSS)"]
        Hosting["Production Cloud: Vercel (Frontend) & Render (FastAPI Backend)"]
    end

    subgraph BackendLayer["⚙️ APPLICATION & INFERENCE BACKEND (FastAPI + Uvicorn)"]
        Router["FastAPI Core Routing & Middleware (CORS / Static)"]
        SimEngine["In-App Physics Telemetry Simulator (Singleton Event Loop)"]
        
        subgraph AI_Engine["🧠 Physics & Machine Learning Pipeline"]
            LGBM["LightGBM Multi-Hazard Classifier (Gas Kick, Loss, Stuck Pipe, T&D)"]
            SHAPEngine["SHAP Local Explainer (TreeExplainer Feature Attribution)"]
            PhysicsCalc["Rig Mechanics Engine (Teale MSE, Bingham d_xc, Eaton PPFG)"]
            DTWEngine["FastDTW Well Log Alignment Engine (GR/Resistivity Shift)"]
        end

        subgraph NLPEngine["📄 Document & NLP Processing Pipeline"]
            Parser["PyMuPDF + pdfplumber + Tesseract OCR"]
            Extractor["LangChain + LLM/Ollama Structured Extractor"]
            RegexFallback["Deterministic Oilfield Regex Ingestion Fallback"]
            VectorEmbed["SentenceTransformer (BAAI/bge-small-en-v1.5)"]
        end
    end

    subgraph PersistenceLayer["💾 PERSISTENCE & SUBSURFACE DATA LAYER (Supabase / Local)"]
        DB[(PostgreSQL Database with SSL Pooling)]
        PG_Geo["PostGIS Spatial Geometry (ST_DWithin, ST_Distance, EPSG:4326)"]
        Tables["WellMaster | SyntheticEvents | WellLogs (LAS Depths)"]
    end

    %% Client internal & Transport
    UI --> MobileShell
    MobileShell --> ClientSandbox
    ClientSandbox --> Console
    Console --> REST
    Console --> WS
    MapBox --> REST
    ThreeD --> REST
    Radar --> REST
    PPFG --> REST
    Correlate --> REST
    Dossier --> REST

    %% Transport to Backend
    REST --> Hosting
    WS --> Hosting
    Hosting --> Router
    Hosting <--> SimEngine

    %% Backend internal routing
    Router --> SimEngine
    Router --> AI_Engine
    Router --> NLPEngine
    SimEngine --> LGBM
    SimEngine --> PhysicsCalc
    AI_Engine --> SHAPEngine

    %% Data access
    Router --> Tables
    AI_Engine --> Tables
    NLPEngine --> VectorEmbed
    VectorEmbed --> Tables
    Tables --> DB
    PG_Geo --> DB
```

---

## 3. Layer-by-Layer Architectural Breakdown

### 3.1. Client Presentation Layer (Frontend)
Built with **React 19** and bundled with **Vite 8**, styled using **Tailwind CSS** and custom **Glassmorphism design tokens**, deployed to cloud hosting or run locally:
* **Multi-Tier Typography System**:
  * `Space Grotesk`: High-tech industrial headers and modal titles.
  * `Inter`: Clean, legible UI controls, drawer logs, and microcopy.
  * `JetBrains Mono`: Monospace precision telemetry readouts (TVD/MD, WOB, RPM, SPP, Flow %, Pit Gain, coordinates).
* **`WellMap.jsx`**: High-contrast dark GIS visualization. Powered by `maplibre-gl` utilizing **Carto Dark Matter** raster tiles (`https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png`) with an automatic OpenStreetMap fallback. Eliminates Web Worker bundle failures and CORS restrictions on cloud CDNs while rendering accurate Upper Assam borders without geopolitical anomalies.
* **Tactical Cyber-Console & Physical Telemetry Matrix**:
  * Docked directly beneath the geospatial map on desktop.
  * Features simulation status LED, playback controls (`Play`, `Pause`, `Step +1m`, `Reset`), speed multipliers (`1x`, `2x`, `5x`), a real-time TVD drill bit seek track, and physical hazard scenario injectors (`Normal`, `Gas Kick`, `Lost Circulation`, `Stuck Pipe`).
  * Live physical sensor array displaying 6 real-time parameters: **WOB** (klbf), **Rotary RPM**, **Standpipe Pressure** (psi), **Flow Out %**, **Pit Volume Delta ($\Delta$)** (bbl), and **Dynamic ECD** (ppg) with pulsing warning states.
* **Mobile-First Responsive Shell**:
  * Dedicated ergonomic viewports optimized for rig engineers on smartphones and tablets.
  * **Compact Mobile Header**: Quick well selector dropdown and one-tap document upload modal trigger.
  * **Floating Map HUD**: Anchored to the top of the map showing active Bit Depth (TVD), ROP, and live Risk level.
  * **Frosted Glass Bottom Navigation Bar**: One-touch navigation between `Well Map`, `Telemetry`, `Simulator`, `Radar`, and `Offsets`.
  * **Dedicated Mobile Simulator Screen**: Full-screen touch-optimized controls with oversized playback buttons, speed selector pills, depth seek slider, and hazard scenario buttons.
* **`Trajectory3DViewer.jsx`**: Interactive 3D trajectory visualization built on Plotly WebGL. Plots Minimum Curvature 3D paths for active wells and surrounding offset wells. Calculates 3D euclidean separation distance vectors and triggers 3D anti-collision proximity warnings.
* **`LookAheadRadar.jsx`**: Displays upcoming geological formations, historical fault zones, casing shoe depths, and potential NPT incidents projected within a customizable depth window ahead of the current bit depth.
* **`PPFGWindowModal.jsx`**: Renders real-time Eaton Pore Pressure Gradient, Mud Weight Equivalent Circulating Density (ECD), and Fracture Gradient curves. Highlights dynamic kick/loss kick tolerances.
* **`CorrelationPanel.jsx`**: FastDTW (Dynamic Time Warping) side-by-side well log correlation (Gamma Ray & Deep Induction Log). Highlights stratigraphic depth shifts and casing programs.
* **`PreSpudDossierModal.jsx`**: 1-Click executive engineering PDF-ready risk dossier aggregating offset well histories, NPT lessons learned, mud schedules, and clearance margins.

### 3.2. Communications & Streaming Layer
* **REST Endpoints (`/api/*`)**: Clean, OpenAPI/Swagger documented endpoints handling historical data queries, well trajectory lookups, PDF document parsing, and stratigraphic correlation. Centralized in `frontend/src/lib/api.js` to automatically target cloud backend (`https://petrolq.onrender.com`) or local host.
* **Telemetry WebSocket (`/api/ws/telemetry`)**: Bidirectional streaming channel with a centralized `WebSocketConnectionManager`. Broadcasts 1 Hz synchronized rig sensor packets and instant ML risk predictions.
* **Client-Side Simulation Isolation**: The simulation tick loop, playback speed, and scenario state are isolated to each user's local React session. This guarantees that multiple engineers testing simultaneously (e.g., one on a smartphone and one on a desktop monitor) experience zero cross-device collision or screen hijacking, while each device independently invokes backend ML inference and physics diagnostics for its own active depth.

### 3.3. Intelligence, ML & Physics Engine
The core backend combines empirical petroleum formulas with gradient-boosted decision trees:
1. **LightGBM Multi-Hazard Classifier**:
   * Evaluates dynamic drilling inputs against rolling statistical windows ($ROP_{roll5}$, $Torque_{roll5\sigma}$).
   * Predicts risk probabilities across 4 distinct hazard categories: **Gas Kick**, **Lost Circulation**, **Stuck Pipe**, and **Torque & Drag**.
2. **Physics Diagnostic Metrics**:
   * **Mechanical Specific Energy (Teale, 1965)**:
     $$MSE = \frac{WOB}{A_b} + \frac{120 \cdot \pi \cdot N \cdot T}{A_b \cdot ROP}$$
     Detects bit wear, vibration dysfunction, and formation boundary transitions.
   * **Corrected $d$-Exponent (Bingham / Jordan & Shirley)**:
     $$d_{xc} = \frac{\log_{10}\left(\frac{ROP}{60 \cdot N}\right)}{\log_{10}\left(\frac{12 \cdot WOB}{10^6 \cdot D_b}\right)} \cdot \frac{\rho_{normal}}{\rho_{actual}}$$
     Provides early detection of abnormal pore pressure transitions before physical kick influx.
   * **Eaton Pore Pressure & Fracture Gradient (Eaton, 1975)**:
     Establishes operational drilling margins and maximum allowable mud weight.
3. **SHAP (SHapley Additive exPlanations)**:
   * Translates gradient boosting decisions into human-readable engineering insights (e.g., *"Torque rolling standard deviation (+450 ft-lbf) is the primary driver of stuck pipe risk"*).

### 3.4. Document Ingestion & Natural Language Processing (NLP)
* **Multi-Format Extraction**: Extracts raw text and tabular data from daily drilling reports (DDR), end-of-well reports (EOWR), and casing manifests using `PyMuPDF`, `pdfplumber`, and `pytesseract` (OCR).
* **Graceful Degradation Pipeline**:
  * *Primary Path*: LangChain structured output prompt with local LLM (Ollama / Llama-3).
  * *Defensive Fallback*: If Ollama is offline or experiences socket timeout (>150ms), the system seamlessly falls back to a deterministic regex domain parser scanning for oilfield vocabulary, depths, and NPT events.
* **Semantic Embeddings**: Generates 384-dimensional vector embeddings via `BAAI/bge-small-en-v1.5` using on-demand, lazy-loaded PyTorch CPU execution.

### 3.5. Persistence & Subsurface Storage
* **Relational Core**: PostgreSQL managed via SQLAlchemy ORM, operational either locally or in cloud production via **Supabase PostgreSQL** with connection pooling and SSL encryption.
* **Spatial Indexing**: PostGIS geometry and geography types (`ST_MakePoint`, `ST_SetSRID`, `ST_DWithin`, `ST_Distance`) perform sub-millisecond offset well clustering and radial distance searches within any specified radius ($r \le 50\text{ km}$).
* **Relational Tables**:
  * `WellMaster`: Field, operator, surface latitude/longitude, total depth (TVD/MD), well status.
  * `SyntheticEvent`: Historical incidents, formation tops, root cause analyses, NPT hours, mitigation records, and 384-dim semantic embeddings.
  * `WellLog`: Digital LAS curves (Depth, GR, RES, NPHI, RHOB, DT).

---

## 4. End-to-End Data Flow Scenarios

### Scenario A: Real-Time Telemetry & Hazard Alerting
```
[ Rig Sensors / Simulator ]
         │ (Depth, WOB, RPM, ROP, Torque, Flow Out, Pit Gain, SPP)
         ▼
[ WebSocket Broadcast (/api/ws/telemetry) ]
         │
         ├──► [ Physics Engine: MSE, d_xc, PPFG Calculations ]
         │
         ├──► [ LightGBM Multi-Hazard Classifier ]
         │           │
         │           ▼
         ├──► [ SHAP Explainer: Top 3 Impact Factors ]
         │
         ▼
[ Broadcast to Client Dashboard (React / WebSocket) ]
         │
         ├──► Flash Red Alert Banner (if Risk >= 0.75)
         ├──► Update Live Gauge & Trajectory Position
         └──► Auto-Query RAG Engine for Offset Well Mitigations
```

### Scenario B: Offset Well RAG Search & Incident Mitigation
```
[ User Search / Automated Alert Trigger ]
         │ "Lost circulation in Barail Formation"
         ▼
[ SentenceTransformer: BAAI/bge-small-en-v1.5 ] ──► (384-dim vector)
         │
         ▼
[ PostgreSQL: In-Memory Cosine Similarity + PostGIS Spatial Filter ]
         │
         ▼
[ Ranked Historical Incidents with Proven Offset Well Mitigations ]
         │
         ▼
[ Rendered in Knowledge Search & Pre-Spud Dossier ]
```

---

## 5. Architectural Quality Attributes & Non-Functional Requirements

| Quality Attribute | Architectural Implementation |
|---|---|
| **Multi-Device Isolation** | Simulation tick loops and playback state are client-isolated in React state; multiple users on mobile and laptop operate concurrently with zero cross-device interference. |
| **Cloud & Edge Portability** | Dual-target architecture: fully hosted on Vercel + Render + Supabase for web evaluations, while maintaining 100% offline standalone capability for isolated rig cabins. |
| **100% Offline Resilience** | All ML models (`joblib`), embeddings (`bge-small`), GIS raster fallbacks, and database engines can run locally without external cloud API dependencies. |
| **Sub-Second Latency** | Telemetry loop executes at 1 Hz; ML hazard inference + physics calculations take $< 45\text{ ms}$ per sample. |
| **Low Memory Footprint** | Lazy-loads PyTorch sentence transformer; ring-buffer capped to 50 samples in frontend; LightGBM operates within $< 512\text{ MB}$ memory. |
| **Fault-Tolerant Basemap** | Carto Dark Matter raster tiles with OpenStreetMap fallback eliminate Web Worker and CORS failures across mobile and desktop browsers. |
| **Fail-Safe Robustness** | Telemetry simulator and parser employ deterministic fallbacks; missing log curves or sensor dropouts produce clean null states instead of fatal crashes. |
| **Geospatial Precision** | WGS-84 coordinate reference system (EPSG:4326) with spherical distance calculations on the earth ellipsoid. |

---

## 6. Directory & Module Mapping

```
sih_2026/
├── backend/
│   ├── main.py                  # ASGI FastAPI application entrypoint & REST/WS routes
│   ├── database.py              # SQLAlchemy engine, PostgreSQL connection pool & Supabase SSL
│   ├── models.py                # Database schemas (WellMaster, SyntheticEvent, WellLog)
│   ├── schemas.py               # Pydantic request/response validation schemas
│   ├── simulator.py             # In-app drilling physics simulator & WebSocket connection manager
│   ├── trajectory_calc.py       # Minimum Curvature 3D wellbore trajectory & anti-collision
│   ├── api/
│   │   ├── upload.py            # LAS and PDF report ingestion endpoints
│   │   ├── correlate.py         # FastDTW stratigraphic well log correlation
│   │   ├── lookahead.py         # Subsurface lookahead formation & hazard radar
│   │   ├── ppfg.py              # Eaton pore pressure & fracture gradient computation
│   │   └── dossier.py           # 1-Click Pre-Spud Risk Dossier compilation
│   ├── ml/
│   │   ├── service.py           # HazardPredictionService (LightGBM + SHAP + Physics)
│   │   └── artifacts/           # Trained LightGBM model, SHAP explainer, metadata
│   └── nlp/
│       ├── config.py            # Lazy-loaded BGE embedding model & LLM settings
│       ├── parser.py            # PDF text and tabular extraction engine
│       ├── extractor.py         # Structured incident extraction with regex fallback
│       └── ingest.py            # Automated report ingestion pipeline
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Mission Control layout, mobile shell & client simulation state
│   │   ├── index.css            # Multi-tier typography, glassmorphism design tokens & styles
│   │   ├── lib/api.js           # Centralized API_BASE & WS_BASE environment config (Vercel/Render)
│   │   └── components/
│   │       ├── WellMap.jsx               # Carto Dark Matter + MapLibre GL 2D spatial visualizer
│   │       ├── Trajectory3DViewer.jsx    # Plotly 3D directional wellbore clearance viewer
│   │       ├── LookAheadRadar.jsx        # Ahead-of-the-bit hazard & formation projection
│   │       ├── PPFGWindowModal.jsx       # Eaton Pore Pressure & Mud Weight Window plot
│   │       ├── CorrelationPanel.jsx      # Stratigraphic log correlation & casing alignment
│   │       ├── PreSpudDossierModal.jsx   # Pre-Spud Engineering Risk Dossier generator
│   │       └── DocumentUploadModal.jsx   # DDR / LAS file ingestion modal
│   └── vite.config.js           # Vite build and development configuration
├── vercel.json                  # Vercel deployment & SPA routing rewrites
├── render.yaml                  # Render backend deployment configuration
├── Procfile                     # Container process startup specification
└── package.json                 # Unified multi-service runner scripts
```
