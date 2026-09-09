# PetrolQ — Comprehensive Technology Stack & Dataset Architecture

> **A Complete Reference Guide for Hackathon Presentations, Technical Evaluations, and Architectural Reviews**

---

## 1. Executive Technology Summary

PetrolQ is built as an **offline-first, enterprise-grade AI decision-support platform** for upstream oil & gas drilling operations. The architecture is engineered to run seamlessly in high-security, low-connectivity field environments (such as offshore platforms or remote onshore drilling rigs in Upper Assam) without requiring cloud lock-in or external third-party API dependencies.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CLIENT PRESENTATION LAYER                       │
│      React 19  │  Vite 8  │  Tailwind CSS  │  MapLibre GL  │  Plotly 3D     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / WebSockets
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                              APPLICATION BACKEND                            │
│           FastAPI (Async ASGI)  │  Uvicorn  │  Pydantic Schemas             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           AI / ML & PHYSICS ENGINE                          │
│   LightGBM (Risk)  │  SHAP (Explainability)  │  Eaton PPFG  │  FastDTW      │
├─────────────────────────────────────────────────────────────────────────────┤
│                          DOCUMENT & NLP EXTRACTION                          │
│   PyMuPDF  │  pdfplumber  │  Tesseract OCR  │  bge-small-en-v1.5 Vectors    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ SQL / Spatial Queries
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                               PERSISTENCE LAYER                             │
│       PostgreSQL Database  │  PostGIS (Spatial)  │  SQLAlchemy ORM          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Programming Languages

### 1. Python (v3.10+)
* **Where Used:** Entire backend application, machine learning models, natural language processing pipelines, geospatial queries, data ingestion scripts, and automated testing.
* **Why Chosen:** Python is the undisputed standard for petroleum data science, ML engineering, and scientific computing. It provides native support for LAS well logs (`lasio`), geospatial analysis (`shapely`), and modern vector embeddings (`sentence-transformers`).

### 2. JavaScript / JSX (ES2022+ / React 19)
* **Where Used:** Entire frontend web application, interactive 3D visualizers, live WebSocket telemetry listeners, and state management.
* **Why Chosen:** JavaScript enables reactive UI state updates, hardware-accelerated 3D WebGL rendering, and real-time bidirectional WebSocket streaming without page reloads.

### 3. SQL (PostgreSQL Dialect + PostGIS Geometry)
* **Where Used:** Database schema definitions, spatial indexing (`ST_DWithin`, `ST_Distance`), and bulk historical incident retrieval.
* **Why Chosen:** Industry-standard relational integrity with specialized spatial extensions to calculate geodesic distances on the Earth's surface.

### 4. Windows Batch Scripting (`start.bat`)
* **Where Used:** Root directory single-click launcher.
* **Why Chosen:** Provides Windows rig engineers and hackathon judges with a zero-friction way to start both backend and frontend servers simultaneously in separate terminal windows.

---

## 3. Backend Frameworks & Core Libraries

### 1. FastAPI (`fastapi`)
* **Role:** High-performance, asynchronous REST API and WebSockets server.
* **How & Where Used:**
  * Serves all REST endpoints: nearby well searches (`/api/wells/nearby`), well trajectories (`/api/wells/{id}/trajectory`), Eaton PPFG computations (`/api/wells/{id}/ppfg`), lookahead hazard corridors (`/api/wells/{id}/lookahead`), and pre-spud dossiers (`/api/wells/{id}/pre-spud-dossier`).
  * Powers `/api/ws/telemetry`, the multi-client WebSocket connection that synchronizes real-time drilling dials across all connected browser tabs.

### 2. Uvicorn (`uvicorn`)
* **Role:** Lightning-fast ASGI (Asynchronous Server Gateway Interface) web server.
* **How & Where Used:**
  * Runs the FastAPI application with auto-reloading (`python -m uvicorn backend.main:app --port 8000`). Handles concurrent HTTP requests and non-blocking WebSocket loops.

### 3. Pydantic & Pydantic Settings (`pydantic`)
* **Role:** Strict data validation and schema serialization.
* **How & Where Used:**
  * Defines clean contracts for API requests and responses (e.g., `WellResponse`, `LookaheadResponse`, `RAGSearchResponse`, `TelemetryPacket`).
  * Automatically filters null values, validates sensor float types, and parses JSON payloads.

### 4. SQLAlchemy (`sqlalchemy`)
* **Role:** Object Relational Mapper (ORM).
* **How & Where Used:**
  * Maps Python classes to PostgreSQL tables in `backend/models.py` (`WellMaster`, `DrillingParam`, `WellLog`, `SyntheticEvent`).
  * Manages database sessions, connection pooling, chunked bulk inserts (`bulk_insert_mappings`), and foreign-key relationships.

### 5. Psycopg2-Binary (`psycopg2-binary`)
* **Role:** Low-level PostgreSQL database driver for Python.
* **How & Where Used:**
  * Connects SQLAlchemy directly to the PostgreSQL engine over TCP port 5432.

---

## 4. Database & Geospatial Technologies

### 1. PostgreSQL
* **Role:** Primary relational and spatial database.
* **How & Where Used:**
  * Stores master well attributes, time-series drilling parameters, high-resolution well log curves, and historical drilling incidents.

### 2. PostGIS (`geoalchemy2`, `shapely`)
* **Role:** Spatial database extender for PostgreSQL.
* **How & Where Used:**
  * Stores wellhead geographic coordinates as PostGIS `POINT(longitude, latitude)` geometry with SRID 4326 (WGS84).
  * Powers the nearby well radius query, instantly finding all offset wells within a given radius in kilometers without brute-force scanning.

### 3. PostgreSQL Dense Vector Arrays
* **Role:** In-database vector storage for institutional memory.
* **How & Where Used:**
  * Stores dense embedding vectors directly alongside historical drilling incidents in the `synthetic_event` table.
  * Eliminates external third-party vector database dependencies (like Pinecone or Qdrant) so the entire platform remains 100% self-contained and local.

---

## 5. AI, Machine Learning & NLP Technologies

### 1. LightGBM & Scikit-Learn (`lightgbm`, `scikit-learn`)
* **Role:** Gradient-boosted machine learning classifier for real-time hazard detection.
* **How & Where Used:**
  * Implemented in `backend/ml/service.py`.
  * Ingests real-time physical telemetry (ROP, WOB, RPM, Torque, Flow Out, Pit Gain, SPP, Mud Weight, MSE) and classifies current drilling risk into **NORMAL**, **ELEVATED**, **HIGH**, or **CRITICAL**.
  * Evaluates multi-parameter anomaly patterns to distinguish a true gas kick from benign sensor noise.

### 2. SHAP (SHapley Additive exPlanations) (`shap`)
* **Role:** Explainable AI (XAI) framework.
* **How & Where Used:**
  * Disaggregates high-risk predictions into the **Top 3 Contributing Mechanical Factors** (e.g., *"Risk is Critical primarily due to +18% Pit Gain Surge and +4,200 ft-lbs Torque Spike"*).
  * Crucial for field engineers who require transparent reasoning before activating emergency well-control protocols.

### 3. Sentence-Transformers (`BAAI/bge-small-en-v1.5`)
* **Role:** Local Transformer Neural Network for dense semantic text embeddings.
* **How & Where Used:**
  * Implemented in `backend/nlp/config.py` and `backend/main.py`.
  * Converts unstructured incident text into 384-dimensional dense vectors.
  * When an engineer types a natural-language query in **Knowledge Search**, cosine similarity is computed between the query vector and historical event vectors to retrieve identical past occurrences.

### 4. PyMuPDF (`fitz`) & pdfplumber (`pdfplumber`)
* **Role:** High-speed document text and tabular extraction.
* **How & Where Used:**
  * Implemented in `backend/nlp/parser.py`.
  * `pdfplumber` extracts structured operational tables (bit records, mud properties, casing tallies) from Daily Drilling Reports (DDRs).
  * `PyMuPDF` parses raw narrative text blocks, remarks, and incident logs with sub-second extraction speed.

### 5. Pytesseract & Pillow (`pytesseract`, `Pillow`)
* **Role:** Optical Character Recognition (OCR).
* **How & Where Used:**
  * Acts as an automated fallback when uploaded drilling reports are scanned images or flattened photocopies without digital text layers.

### 6. LangChain Text Splitters (`langchain-text-splitters`)
* **Role:** Semantic document chunking.
* **How & Where Used:**
  * Chunks large drilling reports into coherent operational paragraphs before feeding them into the embedding generator, ensuring context boundaries remain intact.

---

## 6. Petroleum Engineering & Scientific Computing

### 1. LASIO (`lasio`)
* **Role:** Standard petroleum well-log reader for Log ASCII Standard (`.las`) files.
* **How & Where Used:**
  * Parses commercial wireline and LWD (Logging While Drilling) LAS files containing Gamma Ray, Resistivity, Sonic, and Density curves.

### 2. FastDTW (`fastdtw`)
* **Role:** Fast Dynamic Time Warping algorithm.
* **How & Where Used:**
  * Implemented in `backend/api/correlation.py`.
  * Mathematically aligns well log curves across offset wells where geological strata may be stretched, compressed, or faulted, enabling automated formation-depth correlation.

### 3. SciPy & NumPy (`scipy`, `numpy`)
* **Role:** Scientific computation, numerical arrays, and matrix operations.
* **How & Where Used:**
  * Implements **Eaton's Mathematical Equations** for Pore Pressure Gradient ($PPG$) and Fracture Gradient ($FG$):
    $$PPG = OBG - (OBG - PPG_{normal}) \times \left(\frac{\Delta t_{normal}}{\Delta t_{observed}}\right)^3$$
  * Computes 3D directional minimum curvature trajectory coordinates (East, North, TVD) from measured depth, inclination, and azimuth.

---

## 7. Frontend User Interface & 3D Visualization

### 1. React 19 (`react`, `react-dom`)
* **Role:** Core reactive frontend architecture.
* **How & Where Used:**
  * Manages modular state across gauges, map views, 3D canvases, modals, and real-time WebSocket feeds in `frontend/src/App.jsx`.

### 2. Vite v8 (`vite`)
* **Role:** Frontend tooling and build engine.
* **How & Where Used:**
  * Bundles and serves the React application with Instant Hot Module Replacement (HMR) and optimized Rollup chunking (`npm run build`).

### 3. Tailwind CSS (`tailwindcss`, `postcss`, `autoprefixer`)
* **Role:** Utility-first CSS styling engine.
* **How & Where Used:**
  * Powers the industrial high-tech dark mode palette (`slate-950`, `slate-900`, `cyan-400`, `amber-500`, `red-500`).
  * Delivers responsive, high-contrast visual ergonomics tailored for rig-floor control cabins.

### 4. Plotly.js & React-Plotly (`react-plotly.js`, `plotly.js-dist-min`)
* **Role:** GPU-accelerated WebGL 3D visualization.
* **How & Where Used:**
  * Implemented in `frontend/src/components/Trajectory3DViewer.jsx`.
  * Renders 3D wellbore paths, casing shoes, surface planes, 3D hydrocarbon reservoir lenses, and geological strata.
  * Engineered with custom user-interaction guards (`isInteractingRef`) and constant `uirevision` to maintain 60 FPS smooth camera rotation and zoom during active live streaming.

### 5. MapLibre GL & React-Map-GL (`maplibre-gl`, `react-map-gl`)
* **Role:** Open-source vector tile mapping engine.
* **How & Where Used:**
  * Implemented in `frontend/src/components/WellMap.jsx`.
  * Renders the interactive geospatial map showing oilfield wellheads, surface coordinates, and the interactive radius circle.

### 6. Lucide React (`lucide-react`)
* **Role:** Modern UI vector iconography.
* **How & Where Used:**
  * Supplies clear visual icons across the dashboard (Drill bit, Compass, Radar, Shield Alert, Layers, Database, File Upload).

### 7. Axios (`axios`)
* **Role:** Promise-based HTTP client.
* **How & Where Used:**
  * Handles asynchronous API calls from the React frontend to FastAPI endpoints.

---

## 8. Development, Testing & Launch Orchestration

### 1. Concurrently (`concurrently`)
* **Role:** Multi-process Node.js CLI runner.
* **How & Where Used:**
  * Configured in the root `package.json`. Enables running both the Python FastAPI server (:8000) and Vite frontend server (:5173) with one unified command: `npm run dev`.

### 2. Pytest & Pytest-Asyncio (`pytest`, `pytest-asyncio`)
* **Role:** Automated testing framework.
* **How & Where Used:**
  * Runs backend test suites (`tests/test_ertmac_decision_support.py` and `scripts/test_offline.py`).
  * Validates physics equations, multi-client WebSocket broadcasts, ML scenario injection, and API response structures.

---

## 9. Datasets Used & Data Engineering Strategy

| Dataset Name | Origin / Source | Exact Role in PetrolQ |
| :--- | :--- | :--- |
| **Equinor Volve Field Dataset** | North Sea Open Benchmark (Equinor / Norwegian Petroleum Directorate) | Used as reference benchmark to calibrate realistic drilling telemetry ranges (ROP, WOB, RPM, torque, pit gain) and wireline LAS curve distributions. |
| **FORCE 2020 ML Benchmark** | Norwegian Computing Center / NPD | Used to inspect real-world lithology facies transitions and calibrate sensor behavior across shale-to-sandstone interfaces. |
| **Assam-Arakan Basin Digital Twin** | Modeled specifically for Oil India Limited (OIL) | The distilled, self-contained 99 KB operational seed dataset (`data/processed/`) modeling 8 real Upper Assam fields (`OIL-BAGHJAN-1`, `OIL-NAHARKATIYA-1`, `OIL-DIKOM-1`, `OIL-MORAN-1`, `OIL-TENGAKHAT-1`, `OIL-KOTHALONI-1`, `OIL-HAPJAN-1`, `OIL-SHALMARI-1`) with real Assam stratigraphy (`Tipam`, `Girujan`, `Barail`, `Kopili`). |
| **Historical Drilling Events Repository** | Calibrated Petroleum Incident Database | Structured database of historical incidents (`synthetic_events.csv`) with exact depths, severity levels, root causes, NPT hours, and proven mitigations. |
| **Daily Drilling Report (DDR) Sample** | `sample_reports/OIL_Baghjan_DDR_Well_04.pdf` | Realistic 15 KB multi-page Daily Drilling Report PDF used to demonstrate live AI OCR, table extraction, and institutional memory ingestion. |

---

## 10. Technology Quick-Reference Table

| Layer | Technology | Primary Purpose in Presentation |
| :--- | :--- | :--- |
| **Languages** | Python 3.10+, JavaScript, SQL | Full-stack oilfield engineering platform |
| **API Server** | FastAPI, Uvicorn | High-speed async REST API + real-time WebSockets |
| **Database** | PostgreSQL + PostGIS | Geospatial wellhead queries & vector incident storage |
| **Machine Learning** | LightGBM, Scikit-Learn, SHAP | Real-time hazard classification with explainable AI |
| **NLP & Vectors** | `bge-small-en-v1.5`, PyMuPDF, `pdfplumber` | Automated DDR report parsing & semantic RAG search |
| **Drilling Physics** | Eaton Method, FastDTW, SciPy, LASIO | Pore pressure estimation & well log curve alignment |
| **Frontend UI** | React 19, Vite, Tailwind CSS | Industrial dark-mode rig control room dashboard |
| **3D Visualization** | Plotly.js, WebGL | Interactive 3D subsurface trajectories & anti-collision radar |
| **GIS Mapping** | MapLibre GL, React-Map-GL | Dynamic 5–50km nearby well proximity search |
| **Testing** | Pytest, Pytest-Asyncio | 100% pass rate automated test verification |
| **Datasets** | Assam-Arakan Digital Twin, Volve/FORCE | Physically calibrated, lightweight (99 KB) self-contained data |

---

## 11. System Resilience & Anti-Crash Architecture (Why PetrolQ Won't Crash)

In mission-critical oil & gas environments and high-stakes hackathon presentations, software crashes, UI freezes, and disconnected screens are catastrophic. PetrolQ is architected with **5 layers of defensive, self-healing engineering safeguards** to guarantee 100% uptime and seamless performance:

### 1. The "Traffic Cop" Protection (Throttling & Debouncing)
* **The Vulnerability:** Live drilling simulators stream telemetry updates every second. If the frontend bombarded the backend with heavy database queries on every tick, the browser network stack would choke, queue hundreds of requests, and freeze the tab with a *"Page Unresponsive"* browser crash.
* **Our Defensive Solution:**
  * **Lookahead Debouncing:** The proactive formation lookahead endpoint (`/api/wells/{id}/lookahead`) only fires when the drill bit has advanced by **at least 5.0 meters** (`Math.abs(currentDepth - lastCheckedDepthRef.current) >= 5.0`).
  * **Semantic RAG Throttling:** When a critical drilling hazard (like a Gas Kick) triggers, the system queries the RAG knowledge repository **once** using `alertActiveRef`, locks the alert in memory, and prevents redundant database queries on subsequent telemetry ticks.

### 2. The "Self-Cleaning Memory" (Ring Buffer Capping)
* **The Vulnerability:** Continuous real-time charting over a multi-hour drilling session can accumulate hundreds of thousands of data points, resulting in massive JavaScript memory leaks that crash the user's browser tab.
* **Our Defensive Solution:**
  * **Sliding Window Ring Buffer:** The real-time trajectory and sensor charting states in `App.jsx` strictly enforce a **50-point cap** (`.slice(-50)`). Older data points are automatically pruned from active memory as new ones arrive.
  * **Zero Memory Creep:** The application can run continuously overnight on rig monitors without memory expansion.

### 3. The "Don't Interrupt the Driver" Guard (3D WebGL Protection)
* **The Vulnerability:** In GPU-accelerated 3D WebGL graphics, if an incoming telemetry packet forces a full scene layout re-render while the user is actively dragging the mouse to rotate or zoom, the WebGL event loop drops the pointer lock, causing severe stuttering, frozen cameras, or GPU canvas crashes.
* **Our Defensive Solution:**
  * **Active Interaction Sensor (`isInteractingRef`):** When the user presses the mouse button to rotate, zoom, or pan in `Trajectory3DViewer.jsx`, the component detects active manipulation and holds depth marker updates in background memory.
  * **Constant UI Revision (`uirevision`):** Layouts are memoized so incoming data points never reset the user's rotated camera orientation.
  * **60 FPS Fluidity:** The 3D subsurface viewer delivers uninterrupted 60 FPS rotation, and the drill bit seamlessly catches up to the latest depth the instant the mouse is released.

### 4. The "Ghost Tab Cleaner" (WebSocket Connection Lifecycle Management)
* **The Vulnerability:** If a user closes a browser tab, refreshes the page, or experiences a network blip, poorly managed WebSocket servers attempt to push data to dead socket handles, resulting in `BrokenPipeError` or socket leaks that crash the Python server.
* **Our Defensive Solution:**
  * **Dead Connection Pruning:** Implemented in `backend/simulator.py` via `WebSocketConnectionManager`.
  * If a client tab drops or disconnects, the broadcaster catches the socket exception, safely removes the dead connection from `self.active_connections`, and continues broadcasting smoothly to all other connected tabs without server interruption.
  * **Automatic Client Reconnection:** The frontend WebSocket listener automatically attempts reconnection every 3 seconds if the connection ever drops.

### 5. The "Safety Net on Every Wire" (Defensive Fallbacks & 100% Offline Independence)
* **The Vulnerability:** Many AI projects crash during live presentations because they depend on third-party cloud APIs (e.g., OpenAI, Google Cloud, Pinecone, external tile servers). A venue Wi-Fi failure, expired API key, or rate-limit throttle immediately breaks the application.
* **Our Defensive Solution:**
  * **100% Offline-First Architecture:** The database (PostgreSQL + PostGIS), embedding models (`BAAI/bge-small-en-v1.5`), ML classifiers (LightGBM), and document parsers run **completely locally** on the host machine. The platform operates flawlessly without internet access.
  * **Strict Type and Null Safety:** Every database query, API serializer, and frontend component includes fallback defaults (e.g., `event.depth_start_tvd || 0.0`, `upcoming_formations?.[0] || {}`). Missing historical data produces clean, user-friendly empty states instead of fatal runtime exceptions.

