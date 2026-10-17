import pytest
from app.agents.llm import OllamaAdapter, get_llm_adapter
from app.schemas.contracts import CompanyProfile, BusinessInsight
from app.core.config import settings


def test_ollama_adapter_initialization():
    adapter = OllamaAdapter(base_url="http://localhost:11434", model="mistral:latest", timeout=60.0)
    assert adapter.base_url == "http://localhost:11434"
    assert adapter.model == "mistral:latest"
    assert adapter.timeout == 60.0


def test_ollama_adapter_format_schema_prompt():
    adapter = OllamaAdapter()
    guidelines = adapter._format_schema_prompt(CompanyProfile)
    assert "Required JSON fields and format:" in guidelines
    assert '"name":' in guidelines
    assert '"primary_domain":' in guidelines
    assert '"facts":' in guidelines


@pytest.mark.asyncio
async def test_ollama_adapter_fallback_on_unreachable_host():
    # Point to a non-existent port to test graceful fallback
    adapter = OllamaAdapter(base_url="http://127.0.0.1:59999", model="nonexistent", timeout=0.5)
    result = await adapter.generate_structured(
        prompt="Analyze Acme Corp.",
        system_instruction="Extract company profile.",
        output_schema=CompanyProfile,
    )
    # Must gracefully return a valid model rather than crashing
    assert isinstance(result, CompanyProfile)
    assert result.name is not None


@pytest.mark.asyncio
async def test_ollama_live_local_structured_generation():
    """Verifies that if local Ollama is reachable, generate_structured succeeds."""
    adapter = OllamaAdapter(base_url="http://localhost:11434", model="mistral:latest", timeout=120.0)
    result = await adapter.generate_structured(
        prompt="Acme Corp is a B2B SaaS company building automated data pipelines.",
        system_instruction="Extract company profile. Return valid JSON.",
        output_schema=CompanyProfile,
    )
    assert isinstance(result, CompanyProfile)
    assert result.name is not None

