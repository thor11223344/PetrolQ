import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from nlp.llm_factory import (
    detect_active_provider,
    get_configured_providers,
    is_llm_available,
    get_llm,
    get_llm_status,
    PROVIDER_GEMINI,
    PROVIDER_CLAUDE,
    PROVIDER_OPENAI,
    PROVIDER_OLLAMA,
    PROVIDER_OFFLINE
)
from nlp.extractor import DrillingIncidentSchema, IncidentExtractionResult
from main import app

client = TestClient(app)

# ==============================================================================
# 1. PROVIDER DETECTION TESTS
# ==============================================================================

def test_detect_provider_explicit_gemini():
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "AIzaTestKey123"}, clear=True):
        provider, model = detect_active_provider()
        assert provider == PROVIDER_GEMINI
        assert "gemini" in model.lower()

def test_detect_provider_explicit_claude():
    with patch.dict(os.environ, {"LLM_PROVIDER": "claude", "ANTHROPIC_API_KEY": "sk-ant-testkey"}, clear=True):
        provider, model = detect_active_provider()
        assert provider == PROVIDER_CLAUDE
        assert "claude" in model.lower()

def test_detect_provider_explicit_openai():
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-proj-testkey"}, clear=True):
        provider, model = detect_active_provider()
        assert provider == PROVIDER_OPENAI
        assert "gpt" in model.lower()

def test_detect_provider_explicit_ollama():
    with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL_NAME": "mistral"}, clear=True):
        provider, model = detect_active_provider()
        assert provider == PROVIDER_OLLAMA
        assert model == "mistral"

def test_detect_provider_auto_precedence():
    # Gemini set first
    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaTest123"}, clear=True):
        provider, _ = detect_active_provider()
        assert provider == PROVIDER_GEMINI

    # Claude set
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-123"}, clear=True):
        provider, _ = detect_active_provider()
        assert provider == PROVIDER_CLAUDE

    # OpenAI set
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-123"}, clear=True):
        provider, _ = detect_active_provider()
        assert provider == PROVIDER_OPENAI

def test_detect_provider_offline_when_no_keys():
    with patch.dict(os.environ, {"LLM_API_KEY": "your-api-key-here"}, clear=True):
        with patch("nlp.llm_factory._is_port_open", return_value=False):
            provider, model = detect_active_provider()
            assert provider == PROVIDER_OFFLINE
            assert is_llm_available() is False

# ==============================================================================
# 2. FACTORY INSTANTIATION TESTS
# ==============================================================================

def test_factory_instantiates_gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_openai import ChatOpenAI
    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaDummyKey"}, clear=True):
        llm = get_llm(provider=PROVIDER_GEMINI, model="gemini-1.5-pro")
        assert isinstance(llm, (ChatGoogleGenerativeAI, ChatOpenAI))
        model_name = getattr(llm, "model", None) or getattr(llm, "model_name", "")
        assert "gemini-1.5-pro" in model_name

def test_factory_instantiates_claude():
    from langchain_anthropic import ChatAnthropic
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-dummy"}, clear=True):
        llm = get_llm(provider=PROVIDER_CLAUDE, model="claude-3-5-sonnet-20241022")
        assert isinstance(llm, ChatAnthropic)
        assert llm.model == "claude-3-5-sonnet-20241022"

def test_factory_instantiates_openai():
    from langchain_openai import ChatOpenAI
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy"}, clear=True):
        llm = get_llm(provider=PROVIDER_OPENAI, model="gpt-4o")
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4o"

def test_factory_instantiates_ollama():
    from langchain_openai import ChatOpenAI
    with patch.dict(os.environ, {"OLLAMA_ENDPOINT": "http://localhost:11434/v1", "OLLAMA_MODEL_NAME": "deepseek-r1"}, clear=True):
        llm = get_llm(provider=PROVIDER_OLLAMA)
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "deepseek-r1"
        assert "11434" in str(llm.openai_api_base)

def test_factory_structured_output_binding():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaDummyKey", "OPENAI_API_KEY": "sk-dummy"}, clear=True):
        gemini_llm = get_llm(provider=PROVIDER_GEMINI)
        openai_llm = get_llm(provider=PROVIDER_OPENAI)
        
        structured_gemini = gemini_llm.with_structured_output(IncidentExtractionResult)
        structured_openai = openai_llm.with_structured_output(IncidentExtractionResult)
        
        assert structured_gemini is not None
        assert structured_openai is not None

# ==============================================================================
# 3. API ENDPOINT TESTS
# ==============================================================================

def test_api_ai_status_endpoint():
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_provider" in data
    assert "active_model" in data
    assert "available_providers" in data
    assert "provider_details" in data
    assert "gemini" in data["provider_details"]
    assert "claude" in data["provider_details"]
    assert "openai" in data["provider_details"]
    assert "ollama" in data["provider_details"]

def test_api_ai_synthesize_endpoint_offline_or_online():
    payload = {
        "query": "Mitigate stuck pipe in Barail formation",
        "well_id": "OIL-BAGHJAN-1",
        "depth_tvd": 2650.0,
        "max_records": 3
    }
    response = client.post("/api/ai/synthesize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "provider" in data
    assert "summary" in data
    assert len(data["summary"]) > 0
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert "citations" in data
    assert data["guardrail_verified"] is True
