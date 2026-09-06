import os
from sentence_transformers import SentenceTransformer

# LLM Configuration
# Placeholder for Gemini API key, OpenAI API key, or a local Ollama endpoint.
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key-here")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/v1") # Default fallback for local Ollama (OpenAI compatible)
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3")

# Initialize Local Embedding Model
# We use BAAI/bge-small-en-v1.5 as requested for efficient local embeddings.
# Loaded globally so it only initializes once when the module is imported.
try:
    # Initialize the model 
    embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
except Exception:
    import logging
    logging.getLogger(__name__).warning("Failed to load embedding model.")
    embedding_model = None

def get_embedding(text: str) -> list[float]:
    """
    Helper function to generate embeddings using the local model.
    """
    if embedding_model is None:
        raise RuntimeError("Embedding model is not loaded.")
    return embedding_model.encode(text).tolist()
