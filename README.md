# PetrolQ - SIH 2026 Solution

PetrolQ is an AI-powered Nearby Wells Intelligence System  designed to serve as a decision-support platform for drilling operations. It extracts and structures historical drilling knowledge using AI, NLP, and OCR to provide interactive geospatial mapping of offset wells, semantic search over historical events, and correlation of drilling parameters. By acting as an institutional memory alongside real-time monitoring systems, it enables engineers to proactively identify risks and make fast, data-driven decisions.

## 🌐 Regional Basin Coverage & Data Provenance Disclosure

| Basin / Region | Wells Available | Calibration & Data Provenance Status |
| :--- | :--- | :--- |
| **Upper Assam Shelf** | 11 Wells (`OIL-BAGHJAN-1`, `OIL-NAHARKATIYA-1`, etc.) | **Calibrated Baseline**: Derived from Equinor's Volve open field dataset (North Sea) and FORCE 2020 ML Competition log benchmark, relabeled to Assam stratigraphy and calibrated with Eaton (1972) / Teale (1965) physics rules. |
| **Rajasthan Basin** | 5 Wells (`OIL-RAJ-BAGHEWALA-1` to `5`) | **Regionally Calibrated**: Calibrated geomechanical physics using authentic Indian formations (Pariwar, Baisakhi, Jodhpur Sandstone, Bilara Carbonates), basin normal compaction trends $\Delta t_n(z)$, and Teale MSE wear curves. |
| **KG Deepwater** | 5 Wells (`OIL-KG-DEEPWATER-1` to `5`) | **Regionally Calibrated**: Subsea geomechanical calibration with seafloor overburdens, Godavari Gumbo bit-balling dynamics, and HPHT narrow-margin PP-FG safe drilling corridors. |
| **Mizoram Fold Belt** | 5 Wells (`OIL-MZ-AIZAWL-1` to `5`) | **Regionally Calibrated**: High-tectonic-stress calibration covering Bokabil, Bhuban, and Disang formations with tectonic overpressures and dipping-bed packoff diagnostics. |

> **Transparency Policy:** All wells and UI views feature explicit per-item `SourceTag` provenance badges (`Volve`, `FORCE20`, `Synthetic`, or `Regionally Calibrated`) to provide full operational visibility into geomechanical data models.

## Prerequisites

- **Python:** 3.10 or higher
- **Node.js:** v18 or higher (with npm)
- **Database:** PostgreSQL with the **PostGIS** and **pgvector** extensions enabled

## Backend Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - **Windows:**
     ```cmd
     .\venv\Scripts\activate
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables:**
   Create a `.env` file in the root directory (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Configure your `DATABASE_URL` and choose your preferred AI model provider:

   ### 🤖 Bring Your Own AI Model (Gemini, Claude, OpenAI, or Ollama)
   PetrolQ includes a **universal AI model factory** with automatic provider detection, structured JSON extraction, and safety guardrails. You can use any of the following:

   - **Google Gemini (Recommended for free cloud tiers):**
     ```env
     LLM_PROVIDER=gemini
     GEMINI_API_KEY=AIzaSy...
     GEMINI_MODEL_NAME=gemini-1.5-flash
     ```
   - **Anthropic Claude:**
     ```env
     LLM_PROVIDER=claude
     ANTHROPIC_API_KEY=sk-ant-...
     ANTHROPIC_MODEL_NAME=claude-3-5-haiku-20241022
     ```
   - **OpenAI:**
     ```env
     LLM_PROVIDER=openai
     OPENAI_API_KEY=sk-proj-...
     OPENAI_MODEL_NAME=gpt-4o-mini
     ```
   - **Local Ollama (100% Free & Offline):**
     ```env
     LLM_PROVIDER=ollama
     OLLAMA_ENDPOINT=http://localhost:11434/v1
     OLLAMA_MODEL_NAME=llama3
     ```
   - **Auto-Detect (`LLM_PROVIDER=auto`):**
     Simply paste whichever key you have into `.env` (e.g. `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`), and PetrolQ will automatically pick the right model provider! If no key is set, it checks for a local Ollama server, or gracefully falls back to deterministic rule-based NLP so the app **never crashes**.

5. **Initialize and Seed the Database:**
   Ensure your PostgreSQL instance is running, then run the pipeline and seeding scripts:
   ```bash
   python scripts/run_pipeline.py
   python scripts/seed_database.py
   ```

6. **Start the Backend Server:**
   ```bash
   uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

## Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

## Quick Start (Running Both Servers)

Instead of starting the backend and frontend separately, you can launch both simultaneously using the root configuration:

**Option 1: Using npm concurrently (Cross-platform)**
1. In the root directory, install the root dependencies (like concurrently):
   ```bash
   npm install
   ```
2. Run the dev script:
   ```bash
   npm run dev
   ```

**Option 2: Using the batch script (Windows)**
Simply double-click the `start.bat` file or run it from the command line:
```cmd
.\start.bat
```

## Running the Test Suite

To run the automated test suite, ensure your virtual environment is active and run:
```bash
python -m pytest tests/
```

## Running Fully Offline

If you plan to run the application on a demo machine with zero internet connectivity, follow these steps:

1. **Pre-download the Map Tiles**:
   Run the tile downloader script while still connected to the internet. This will pull raster tiles for the Upper Assam basin and save them to `backend/static/tiles/`:
   ```bash
   python scripts/download_tiles.py
   ```

2. **Enable Offline Map Rendering**:
   In the `frontend` directory, create a `.env` file (if you haven't already) and add the following line:
   ```env
   VITE_OFFLINE_MODE=true
   ```
   This instructs the frontend map to use the locally downloaded tiles instead of external CartoDB styles.

3. **Embedding Model Cache**:
   The NLP embedding model (`BAAI/bge-small-en-v1.5`) uses the HuggingFace cache automatically. Ensure you have started the backend at least once while online so the model weights are downloaded to `~/.cache/huggingface/hub/`. Upon starting offline, the system will seamlessly load the local weights.
   > **Note:** When starting entirely offline, the `huggingface_hub` library will spend a few minutes retrying connections for model updates before falling back to the cache. To prevent this slow startup, you can add `HF_HUB_OFFLINE=1` to your backend environment variables or set it before running `uvicorn`.