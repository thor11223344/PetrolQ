import os
import threading

# LLM Configuration
# Placeholder for Gemini API key, OpenAI API key, or a local Ollama endpoint.
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key-here")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/v1") # Default fallback for local Ollama (OpenAI compatible)
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3")

embedding_model = None
_embedding_lock = threading.Lock()

def get_embedding(text: str) -> list[float]:
    """
    Helper function to generate embeddings using fastembed.
    Lazy-loaded on first call to prevent OOM on memory-constrained servers.
    """
    global embedding_model
    if embedding_model is None:
        with _embedding_lock:
            if embedding_model is None:
                try:
                    from fastembed import TextEmbedding
                    cache_dir = os.path.join(os.getcwd(), "temp_uploads", "fastembed_cache")
                    os.makedirs(cache_dir, exist_ok=True)
                    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=cache_dir)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to load embedding model: {e}")
                    raise RuntimeError("Embedding model could not be initialized.") from e
            
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()
