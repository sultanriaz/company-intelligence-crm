import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """
    Strips markdown code blocks, backticks, and comments to reliably parse JSON
    from LLM responses.
    """
    text = text.strip()
    # If wrapped in ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try finding the first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            substring = text[start : end + 1]
            return json.loads(substring)
        raise


class BaseLLMAdapter:
    """Abstract base adapter for LLM generation."""

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        output_schema: Type[T],
    ) -> T:
        raise NotImplementedError


class MockLLMAdapter(BaseLLMAdapter):
    """
    Deterministic mock LLM adapter for offline testing, local demo,
    and hermetic CI execution without live credentials.
    """

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        output_schema: Type[T],
    ) -> T:
        schema_name = output_schema.__name__

        if schema_name == "CompanyProfile":
            data = {
                "name": "Acme Innovations Inc",
                "legal_name": "Acme Innovations Corporation",
                "primary_domain": "acme.example.com",
                "industry": "Enterprise Software & Cloud AI",
                "employee_range": "50-200",
                "description": "Acme Innovations builds automated data integration and machine learning pipelines for B2B enterprises.",
                "headquarters": "San Francisco, CA, USA",
                "products_services": [
                    "Cloud Data Pipeline Platform",
                    "Automated ETL Sync",
                    "AI Prediction Engine",
                ],
                "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "AWS"],
                "leadership": ["Alice Vance (CEO)", "Bob Sterling (CTO)"],
                "contact_channels": [
                    {
                        "channel_type": "email",
                        "value": "contact@acme.example.com",
                        "source_url": "https://acme.example.com/contact",
                    }
                ],
                "facts": [
                    {
                        "field": "industry",
                        "value": "Enterprise Software & Cloud AI",
                        "source_url": "https://acme.example.com/about",
                        "retrieved_at": "2026-10-17T12:00:00Z",
                        "confidence": 0.95,
                        "verification_status": "verified",
                    },
                    {
                        "field": "products",
                        "value": "Cloud Data Pipeline Platform, Automated ETL Sync",
                        "source_url": "https://acme.example.com/products",
                        "retrieved_at": "2026-10-17T12:00:00Z",
                        "confidence": 0.92,
                        "verification_status": "verified",
                    },
                    {
                        "field": "headquarters",
                        "value": "San Francisco, CA, USA",
                        "source_url": "https://acme.example.com/contact",
                        "retrieved_at": "2026-10-17T12:00:00Z",
                        "confidence": 0.98,
                        "verification_status": "verified",
                    },
                ],
            }
            return output_schema.model_validate(data)

        elif schema_name == "VerificationResult":
            data = {
                "company_name": "Acme Innovations Inc",
                "domain": "acme.example.com",
                "verified_facts": [
                    {
                        "field": "industry",
                        "value": "Enterprise Software & Cloud AI",
                        "source_url": "https://acme.example.com/about",
                        "retrieved_at": "2026-10-17T12:00:00Z",
                        "confidence": 0.95,
                        "verification_status": "verified",
                    },
                    {
                        "field": "headquarters",
                        "value": "San Francisco, CA, USA",
                        "source_url": "https://acme.example.com/contact",
                        "retrieved_at": "2026-10-17T12:00:00Z",
                        "confidence": 0.98,
                        "verification_status": "verified",
                    },
                ],
                "provisional_facts": [],
                "conflicting_facts": [],
                "overall_confidence_score": 0.96,
                "verification_notes": [
                    "Domain ownership verified via primary SSL host.",
                    "All extracted leadership references cited from verified team page.",
                ],
            }
            return output_schema.model_validate(data)

        elif schema_name == "BusinessInsight":
            data = {
                "company_name": "Acme Innovations Inc",
                "executive_summary": "Acme Innovations is a high-growth cloud data platform provider focusing on automated ETL pipelines and B2B workflow integrations.",
                "target_market": "Mid-market and enterprise technology organizations seeking real-time data synchronization.",
                "operational_challenges_hypotheses": [
                    {
                        "challenge": "Scaling distributed data transformations across heterogeneous multi-cloud environments.",
                        "hypothesis_rationale": "Public documentation highlights growing customer volume and custom on-prem connector demands.",
                        "needs_validation": True,
                    }
                ],
                "market_opportunities": [
                    "Expansion into automated AI-driven ETL monitoring.",
                    "Modernizing legacy database migrations for financial services clients.",
                ],
                "company_specific_value_proposition": "Providing turn-key automated pipeline orchestration that reduces engineering maintenance by 40%.",
                "recommended_outreach_angle": "Highlighting seamless multi-cloud observability and zero-downtime database replication.",
                "identified_research_gaps": ["Exact current enterprise client count not published publicly."],
            }
            return output_schema.model_validate(data)

        elif schema_name == "EmailDraftResult":
            data = {
                "subject": "Optimizing Data Pipeline Observability for Acme Innovations",
                "body_text": (
                    "Hi Alice,\n\n"
                    "I noticed Acme Innovations' recent work expanding automated cloud ETL pipelines. "
                    "Many teams scaling distributed pipelines face overhead maintaining multi-cloud data sync.\n\n"
                    "We specialize in automated pipeline orchestration and real-time monitoring that helps engineering teams "
                    "maintain continuous data flow with minimal downtime.\n\n"
                    "Would you be open to a brief 10-minute conversation next Tuesday to share insights?\n\n"
                    "Best regards,\n"
                    "Outreach Team\n\n"
                    "Unsubscribe: https://company-intelligence.local/unsubscribe"
                ),
                "body_html": (
                    "<p>Hi Alice,</p>"
                    "<p>I noticed Acme Innovations' recent work expanding automated cloud ETL pipelines. "
                    "Many teams scaling distributed pipelines face overhead maintaining multi-cloud data sync.</p>"
                    "<p>We specialize in automated pipeline orchestration and real-time monitoring that helps engineering teams "
                    "maintain continuous data flow with minimal downtime.</p>"
                    "<p>Would you be open to a brief 10-minute conversation next Tuesday to share insights?</p>"
                    "<p>Best regards,<br>Outreach Team</p>"
                    "<hr><p><small><a href='https://company-intelligence.local/unsubscribe'>Unsubscribe</a></small></p>"
                ),
                "recipient_email": "alice@acme.example.com",
                "recipient_name": "Alice Vance",
                "referenced_fact_fields": ["industry", "products"],
                "value_proposition_used": "Automated pipeline orchestration reducing engineering maintenance.",
                "tone": "professional",
                "draft_status": "PENDING_APPROVAL",
            }
            return output_schema.model_validate(data)

        # Fallback default empty model
        return output_schema()


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI API adapter using standard HTTP or LangChain."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        output_schema: Type[T],
    ) -> T:
        if not self.api_key:
            logger.warning("No OpenAI API key configured. Falling back to MockLLMAdapter.")
            return await MockLLMAdapter().generate_structured(prompt, system_instruction, output_schema)

        import httpx
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system_instruction}\nRespond ONLY with valid JSON matching the requested schema."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            resp_data = resp.json()
            content = resp_data["choices"][0]["message"]["content"]
            parsed_json = extract_json_from_llm_response(content)
            return output_schema.model_validate(parsed_json)


def get_llm_adapter() -> BaseLLMAdapter:
    """Factory function returning the configured LLM adapter."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIAdapter()
    return MockLLMAdapter()
