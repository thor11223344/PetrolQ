import os
from sentence_transformers import SentenceTransformer

# LLM Configuration
# Placeholder for Gemini API key, OpenAI API key, or a local Ollama endpoint.
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key-here")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate") # Default fallback for local Ollama
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3")

# Initialize Local Embedding Model
# We use BAAI/bge-small-en-v1.5 as requested for efficient local embeddings.
# Loaded globally so it only initializes once when the module is imported.
print("Initializing local embedding model (BAAI/bge-small-en-v1.5)...")
try:
    # Initialize the model 
    embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    print("Embedding model loaded successfully.")
except Exception as e:
    print(f"Warning: Failed to load embedding model. Ensure dependencies are installed and internet is available for first download. Error: {e}")
    embedding_model = None

def get_embedding(text: str) -> list[float]:
    """
    Helper function to generate embeddings using the local model.
    """
    if embedding_model is None:
        raise RuntimeError("Embedding model is not loaded.")
    return embedding_model.encode(text).tolist()
