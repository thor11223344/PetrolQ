import os
import threading

# ---------------------------------------------------------------------------
# Multi-Provider LLM Configuration (Gemini, Claude, OpenAI, Ollama)
# ---------------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")

# Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

# Anthropic Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
ANTHROPIC_MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-5-haiku-20241022")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# Ollama (Local)
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/v1")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3")

# Backward compatibility fallbacks
LLM_API_KEY = os.getenv("LLM_API_KEY", "your-api-key-here")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", OLLAMA_ENDPOINT)
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
                    from fastembed import TextEmbedding  # type: ignore
                    cache_dir = os.path.join(os.getcwd(), "temp_uploads", "fastembed_cache")
                    os.makedirs(cache_dir, exist_ok=True)
                    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=cache_dir)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to load embedding model: {e}")
                    raise RuntimeError("Embedding model could not be initialized.") from e
            
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()
