import os
from sentence_transformers import SentenceTransformer

# LLM Configuration
# Placeholder for Gemini API key, OpenAI API key, or a local Ollama endpoint.
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key-here")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/v1") # Default fallback for local Ollama (OpenAI compatible)
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3")

embedding_model = None

def get_embedding(text: str) -> list[float]:
    """
    Helper function to generate embeddings using the local model.
    Lazy-loaded on first call to prevent OOM on memory-constrained servers.
    """
    global embedding_model
    if embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to load embedding model: {e}")
            raise RuntimeError("Embedding model could not be initialized.") from e
            
    return embedding_model.encode(text).tolist()
