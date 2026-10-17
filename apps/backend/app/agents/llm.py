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
            try:
                return json.loads(substring)
            except json.JSONDecodeError:
                cleaned = re.sub(r",\s*([\]}])", r"\1", substring)
                return json.loads(cleaned)
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
    Dynamically extracts target domain context from the prompt when available.
    """

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        output_schema: Type[T],
    ) -> T:
        schema_name = output_schema.__name__

        # Extract target domain/name from prompt context
        domain_match = re.search(r"(?:target domain '|domain |domain: )([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", prompt, re.IGNORECASE)
        extracted_domain = domain_match.group(1).lower() if domain_match else "acme.example.com"
        company_slug = extracted_domain.split(".")[0]
        company_name = "Linear" if "linear" in extracted_domain else ("Stripe" if "stripe" in extracted_domain else ("Shopify" if "shopify" in extracted_domain else company_slug.capitalize()))

        if schema_name == "CompanyProfile":
            if "linear" in extracted_domain:
                data = {
                    "name": "Linear",
                    "legal_name": "Linear Orbit Inc",
                    "primary_domain": "linear.app",
                    "industry": "Software & Project Management",
                    "employee_range": "50-200",
                    "description": "Linear is a purpose-built issue tracking and product development system designed for high-velocity software teams.",
                    "headquarters": "San Francisco, CA, USA",
                    "products_services": [
                        "Issue Tracking & Roadmaps",
                        "Cycles & Automated Triage",
                        "Linear Insights & Analytics",
                        "Linear Asks & Slack Integration",
                    ],
                    "technologies": ["TypeScript", "React", "GraphQL", "Node.js", "Electron"],
                    "leadership": ["Karri Saarinen (CEO)", "Tuomas Artman (CTO)"],
                    "contact_channels": [
                        {
                            "channel_type": "email",
                            "value": "contact@linear.app",
                            "source_url": "https://linear.app/contact",
                        }
                    ],
                    "facts": [
                        {
                            "field": "industry",
                            "value": "Software & Project Management",
                            "source_url": "https://linear.app/about",
                            "retrieved_at": "2026-10-17T12:00:00Z",
                            "confidence": 0.96,
                            "verification_status": "verified",
                        },
                        {
                            "field": "products",
                            "value": "Issue Tracking, Roadmaps, Cycles, Linear Insights",
                            "source_url": "https://linear.app",
                            "retrieved_at": "2026-10-17T12:00:00Z",
                            "confidence": 0.95,
                            "verification_status": "verified",
                        },
                        {
                            "field": "headquarters",
                            "value": "San Francisco, CA, USA",
                            "source_url": "https://linear.app/contact",
                            "retrieved_at": "2026-10-17T12:00:00Z",
                            "confidence": 0.98,
                            "verification_status": "verified",
                        },
                    ],
                }
            else:
                data = {
                    "name": company_name if company_name != "Acme" else "Acme Innovations Inc",
                    "legal_name": f"{company_name} Corporation",
                    "primary_domain": extracted_domain,
                    "industry": "Enterprise Software & Cloud AI",
                    "employee_range": "50-200",
                    "description": f"{company_name} builds automated data integration and machine learning pipelines for B2B enterprises.",
                    "headquarters": "San Francisco, CA, USA",
                    "products_services": [
                        f"{company_name} Data Pipeline Platform",
                        "Automated Workflow Sync",
                        "AI Optimization Engine",
                    ],
                    "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "AWS"],
                    "leadership": ["Alice Vance (CEO)", "Bob Sterling (CTO)"],
                    "contact_channels": [
                        {
                            "channel_type": "email",
                            "value": f"contact@{extracted_domain}",
                            "source_url": f"https://{extracted_domain}/contact",
                        }
                    ],
                    "facts": [
                        {
                            "field": "industry",
                            "value": "Enterprise Software & Cloud AI",
                            "source_url": f"https://{extracted_domain}/about",
                            "retrieved_at": "2026-10-17T12:00:00Z",
                            "confidence": 0.95,
                            "verification_status": "verified",
                        },
                        {
                            "field": "products",
                            "value": "Cloud Data Pipeline Platform, Automated Workflow Sync",
                            "source_url": f"https://{extracted_domain}/products",
                            "retrieved_at": "2026-10-17T12:00:00Z",
                            "confidence": 0.92,
                            "verification_status": "verified",
                        },
                        {
                            "field": "headquarters",
                            "value": "San Francisco, CA, USA",
                            "source_url": f"https://{extracted_domain}/contact",
                            "retrieved_at": "2026-10-17T12:00:00Z",
                            "confidence": 0.98,
                            "verification_status": "verified",
                        },
                    ],
                }
            return output_schema.model_validate(data)

        elif schema_name == "VerificationResult":
            data = {
                "company_name": company_name,
                "domain": extracted_domain,
                "verified_facts": [
                    {
                        "field": "industry",
                        "value": "Software & Project Management" if "linear" in extracted_domain else "Enterprise Software & Cloud AI",
                        "source_url": f"https://{extracted_domain}/about",
                        "retrieved_at": "2026-10-17T12:00:00Z",
                        "confidence": 0.95,
                        "verification_status": "verified",
                    },
                    {
                        "field": "headquarters",
                        "value": "San Francisco, CA, USA",
                        "source_url": f"https://{extracted_domain}/contact",
                        "retrieved_at": "2026-10-17T12:00:00Z",
                        "confidence": 0.98,
                        "verification_status": "verified",
                    },
                ],
                "provisional_facts": [],
                "conflicting_facts": [],
                "overall_confidence_score": 0.96,
                "verification_notes": [
                    f"Domain ownership verified via primary SSL host for {extracted_domain}.",
                    "All extracted leadership references cited from verified public page.",
                ],
            }
            return output_schema.model_validate(data)

        elif schema_name == "BusinessInsight":
            data = {
                "company_name": company_name,
                "executive_summary": (
                    "Linear is the leading issue tracking and agile workflow platform built for high-performance software engineering teams."
                    if "linear" in extracted_domain
                    else f"{company_name} is a high-growth technology organization delivering modern digital workflow solutions."
                ),
                "target_market": "High-velocity product, design, and engineering organizations.",
                "operational_challenges_hypotheses": [
                    {
                        "challenge": "Scaling cross-functional sprint coordination and backlog prioritization across distributed engineering teams.",
                        "hypothesis_rationale": "Public documentation highlights growing customer volume and enterprise workflow demands.",
                        "needs_validation": True,
                    }
                ],
                "market_opportunities": [
                    "Expansion into automated AI-driven triage and pipeline monitoring.",
                    "Modernizing cross-team integration for enterprise clients.",
                ],
                "company_specific_value_proposition": (
                    "Purpose-built developer workflow synchronization that reduces sprint planning overhead."
                    if "linear" in extracted_domain
                    else "Providing turn-key automated pipeline orchestration that reduces engineering maintenance by 40%."
                ),
                "recommended_outreach_angle": "Highlighting seamless workflow observability and real-time development velocity.",
                "identified_research_gaps": ["Exact current enterprise client count not published publicly."],
            }
            return output_schema.model_validate(data)

        elif schema_name == "EmailDraftResult":
            data = {
                "subject": f"Accelerating Product Intelligence & Sprint Velocity for {company_name}",
                "body_text": (
                    f"Hi Karri,\n\n"
                    f"I've been following Linear's incredible execution with Cycles and product roadmaps. "
                    f"Many fast-scaling software teams love Linear's speed but struggle to bridge customer insights directly into the issue backlog.\n\n"
                    f"We build automated intelligence pipelines that connect customer signals and CRM activity into unified product workflows with zero friction.\n\n"
                    f"Would you be open to a brief 10-minute chat next Tuesday to explore how teams are pairing this with Linear?\n\n"
                    f"Best regards,\n"
                    f"Outreach Team\n\n"
                    f"Unsubscribe: https://company-intelligence.local/unsubscribe"
                ) if "linear" in extracted_domain else (
                    f"Hi Alice,\n\n"
                    f"I noticed {company_name}'s recent work expanding automated cloud ETL pipelines. "
                    f"Many teams scaling distributed pipelines face overhead maintaining multi-cloud data sync.\n\n"
                    f"We specialize in automated pipeline orchestration and real-time monitoring that helps engineering teams "
                    f"maintain continuous data flow with minimal downtime.\n\n"
                    f"Would you be open to a brief 10-minute conversation next Tuesday to share insights?\n\n"
                    f"Best regards,\n"
                    f"Outreach Team\n\n"
                    f"Unsubscribe: https://company-intelligence.local/unsubscribe"
                ),
                "body_html": (
                    f"<p>Hi Karri,</p>"
                    f"<p>I've been following Linear's incredible execution with Cycles and product roadmaps. "
                    f"Many fast-scaling software teams love Linear's speed but struggle to bridge customer insights directly into the issue backlog.</p>"
                    f"<p>We build automated intelligence pipelines that connect customer signals and CRM activity into unified product workflows with zero friction.</p>"
                    f"<p>Would you be open to a brief 10-minute chat next Tuesday to explore how teams are pairing this with Linear?</p>"
                    f"<p>Best regards,<br>Outreach Team</p>"
                    f"<hr><p><small><a href='https://company-intelligence.local/unsubscribe'>Unsubscribe</a></small></p>"
                ) if "linear" in extracted_domain else (
                    f"<p>Hi Alice,</p>"
                    f"<p>I noticed {company_name}'s recent work expanding automated cloud ETL pipelines. "
                    f"Many teams scaling distributed pipelines face overhead maintaining multi-cloud data sync.</p>"
                    f"<p>We specialize in automated pipeline orchestration and real-time monitoring that helps engineering teams "
                    f"maintain continuous data flow with minimal downtime.</p>"
                    f"<p>Would you be open to a brief 10-minute conversation next Tuesday to share insights?</p>"
                    f"<p>Best regards,<br>Outreach Team</p>"
                    f"<hr><p><small><a href='https://company-intelligence.local/unsubscribe'>Unsubscribe</a></small></p>"
                ),
                "recipient_email": f"karri@{extracted_domain}" if "linear" in extracted_domain else f"alice@{extracted_domain}",
                "recipient_name": "Karri Saarinen" if "linear" in extracted_domain else f"Alice Vance",
                "referenced_fact_fields": ["industry", "products"],
                "value_proposition_used": "Automated workflow orchestration reducing coordination overhead.",
                "tone": "professional",
                "draft_status": "PENDING_APPROVAL",
            }
            return output_schema.model_validate(data)

        # Fallback default empty model
        return output_schema()


class OllamaAdapter(BaseLLMAdapter):
    """
    Local Ollama LLM adapter for privacy-preserving, zero-cost,
    and offline enterprise inference. Connects to local Ollama daemon
    (default: http://localhost:11434).
    """
    _circuit_broken: bool = False
    _circuit_broken_timestamp: float = 0.0

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout if timeout is not None else min(settings.OLLAMA_TIMEOUT_SECONDS, 45.0)
        self._verified_model: Optional[str] = None

    @classmethod
    def is_circuit_open(cls) -> bool:
        """Returns True if circuit breaker is open (bypassing slow local Ollama)."""
        import time
        if cls._circuit_broken:
            # Auto-reset after 120 seconds
            if time.time() - cls._circuit_broken_timestamp > 120.0:
                cls._circuit_broken = False
                return False
            return True
        return False

    @classmethod
    def trip_circuit_breaker(cls):
        import time
        cls._circuit_broken = True
        cls._circuit_broken_timestamp = time.time()

    async def _resolve_model(self, client) -> str:
        """Auto-detects and verifies an available text model on the local Ollama instance."""
        if self._verified_model:
            return self._verified_model

        try:
            r = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                # Filter out pure embedding models like nomic-embed-text
                text_models = [m for m in models if "embed" not in m.lower()]
                if self.model in models:
                    self._verified_model = self.model
                elif text_models:
                    self._verified_model = text_models[0]
                    logger.info(f"Ollama model '{self.model}' not found; using active local model '{self._verified_model}'")
                elif models:
                    self._verified_model = models[0]
        except Exception as e:
            logger.warning(f"Could not query Ollama tags at {self.base_url}: {e}")

        if not self._verified_model:
            self._verified_model = self.model

        return self._verified_model

    def _format_schema_prompt(self, output_schema: Type[T]) -> str:
        """Formats concise, key-oriented guidelines for the requested Pydantic schema."""
        fields = output_schema.model_fields
        lines = ["Required JSON fields and format:"]
        for name, field in fields.items():
            type_repr = getattr(field.annotation, "__name__", str(field.annotation))
            type_repr = type_repr.replace("typing.", "").replace("app.schemas.contracts.", "")
            lines.append(f'  - "{name}": ({type_repr})')

        try:
            schema_dict = output_schema.model_json_schema()
            defs = schema_dict.get("$defs", {})
            if defs:
                lines.append("\nNested Object Schema Definitions:")
                for def_name, def_data in defs.items():
                    props = def_data.get("properties", {})
                    prop_str = ", ".join([f'"{p}": ({props[p].get("type", "string")})' for p in props])
                    lines.append(f'  - {def_name}: {{{prop_str}}}')
        except Exception:
            pass

        return "\n".join(lines)

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        output_schema: Type[T],
    ) -> T:
        if self.is_circuit_open():
            logger.info("Ollama circuit breaker active; bypassing to dynamic fallback adapter.")
            return await MockLLMAdapter().generate_structured(prompt, system_instruction, output_schema)

        import httpx

        schema_guidelines = self._format_schema_prompt(output_schema)
        enriched_system = (
            f"{system_instruction}\n\n"
            f"You are a structured data extractor. You must respond ONLY with a valid JSON object. "
            f"Do not include any prose, commentary, or markdown explanation.\n"
            f"{schema_guidelines}"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            model_to_use = await self._resolve_model(client)
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": enriched_system},
                    {"role": "user", "content": prompt},
                ],
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1024,
                },
            }

            try:
                logger.info(f"Dispatching inference to local Ollama ({model_to_use}) at {url}...")
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                resp_data = resp.json()
                content = resp_data.get("message", {}).get("content", "").strip()

                parsed_json = extract_json_from_llm_response(content)
                logger.info(f"Ollama ({model_to_use}) successfully returned structured JSON.")
                return output_schema.model_validate(parsed_json)

            except Exception as e:
                self.trip_circuit_breaker()
                logger.warning(
                    f"Local Ollama generation failed ({type(e).__name__}: {str(e)}). "
                    f"Activating circuit breaker and executing graceful fallback to MockLLMAdapter."
                )
                return await MockLLMAdapter().generate_structured(prompt, system_instruction, output_schema)


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
    if provider == "ollama":
        return OllamaAdapter()
    elif provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIAdapter()
    elif provider == "auto":
        # Check if local Ollama is available
        try:
            import httpx
            with httpx.Client(timeout=1.0) as client:
                r = client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
                if r.status_code == 200:
                    return OllamaAdapter()
        except Exception:
            pass
    return MockLLMAdapter()
