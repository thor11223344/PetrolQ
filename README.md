# PetrolQ - SIH 2026 Solution

PetrolQ is an AI-powered Nearby Wells Intelligence System  designed to serve as a decision-support platform for drilling operations. It extracts and structures historical drilling knowledge using AI, NLP, and OCR to provide interactive geospatial mapping of offset wells, semantic search over historical events, and correlation of drilling parameters. By acting as an institutional memory alongside real-time monitoring systems, it enables engineers to proactively identify risks and make fast, data-driven decisions.

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
   Create a `.env` file in the root directory (copy from `.env.example` if available) and ensure your database credentials are correct. If using the document extraction feature, set the LLM variables (defaults to a local Ollama endpoint):
   ```env
   LLM_API_KEY=your-api-key-here
   LLM_ENDPOINT=http://localhost:11434/v1
   ```

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