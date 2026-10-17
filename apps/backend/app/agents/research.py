from typing import List
from app.agents.base import BaseAgent
from app.agents.llm import get_llm_adapter
from app.schemas.contracts import CompanyProfile, ScrapedPage
from app.security.prompt_guard import wrap_untrusted_content_defensively


class CompanyResearchAgent(BaseAgent):
    """
    Agent 4: Company Research Agent.
    Synthesizes company intelligence from scraped web pages into a structured profile.
    Mandates source URL citations for every fact.
    """

    def __init__(self):
        super().__init__(name="CompanyResearchAgent")

    async def execute_task(
        self,
        domain: str,
        scraped_pages: List[ScrapedPage],
    ) -> CompanyProfile:
        combined_text_blocks = []
        for p in scraped_pages[:10]:
            clean_snippet = p.clean_text[:4000]
            block = f"--- Source URL: {p.url} ---\n{clean_snippet}"
            combined_text_blocks.append(block)

        raw_corpus = "\n\n".join(combined_text_blocks)
        guarded_corpus = wrap_untrusted_content_defensively(raw_corpus, label="SCRAPED_COMPANY_DATA")

        system_instruction = (
            "You are a rigorous Principal Corporate Intelligence Researcher. "
            "Extract structured company information based ONLY on the provided text. "
            "DO NOT hallucinate or assume metrics. If a fact is not stated in the source text, "
            "set it to 'Unknown'. Every fact must cite its exact source_url."
        )

        prompt = (
            f"Analyze the following scraped company data for target domain '{domain}'.\n\n"
            f"{guarded_corpus}\n\n"
            "Return a complete CompanyProfile JSON structure including:\n"
            "- name, legal_name, primary_domain\n"
            "- industry, employee_range, description, headquarters\n"
            "- products_services, technologies, leadership\n"
            "- contact_channels (with exact source_url)\n"
            "- facts: list of key facts (field, value, source_url, confidence, verification_status)"
        )

        llm = get_llm_adapter()
        profile = await llm.generate_structured(prompt, system_instruction, CompanyProfile)
        profile.primary_domain = domain.lower()
        return profile


research_agent = CompanyResearchAgent()
