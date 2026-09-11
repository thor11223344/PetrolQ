import os
import sys
from pathlib import Path

# Ensure paths
BASE_DIR = Path(__file__).resolve().parent
sys.path.extend([str(BASE_DIR), str(BASE_DIR / "backend")])

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting PetrolQ API server on 0.0.0.0:{port}...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, workers=1)
