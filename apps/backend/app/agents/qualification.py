from typing import List
from app.agents.base import BaseAgent
from app.schemas.contracts import BusinessInsight, CompanyProfile, DimensionScore, LeadQualificationResult, VerificationResult


class LeadQualificationAgent(BaseAgent):
    """
    Agent 7: Lead Qualification Agent.
    Implements deterministic weighted multi-factor scoring (0-100)
    with transparent dimension explanations.
    """

    def __init__(self, qualification_threshold: int = 60):
        super().__init__(name="LeadQualificationAgent")
        self.threshold = qualification_threshold

    def calculate_industry_score(self, industry: str) -> DimensionScore:
        lower = industry.lower() if industry else ""
        high_value = ["software", "technology", "saas", "cloud", "ai", "data", "finance", "healthcare"]
        if any(kw in lower for kw in high_value):
            return DimensionScore(
                dimension_name="industry_relevance",
                score=25,
                max_score=25,
                rationale=f"Industry '{industry}' closely aligns with core high-value target vertical.",
            )
        elif lower and lower != "unknown":
            return DimensionScore(
                dimension_name="industry_relevance",
                score=15,
                max_score=25,
                rationale=f"Industry '{industry}' represents a secondary target vertical.",
            )
        return DimensionScore(
            dimension_name="industry_relevance",
            score=5,
            max_score=25,
            rationale="Industry is unknown or unverified.",
        )

    def calculate_service_score(self, profile: CompanyProfile) -> DimensionScore:
        offerings_count = len(profile.products_services)
        if offerings_count >= 3:
            return DimensionScore(
                dimension_name="service_compatibility",
                score=25,
                max_score=25,
                rationale=f"Strong service compatibility with {offerings_count} distinct identified offerings.",
            )
        elif offerings_count >= 1:
            return DimensionScore(
                dimension_name="service_compatibility",
                score=18,
                max_score=25,
                rationale="Identified at least one relevant service offering matching platform capabilities.",
            )
        return DimensionScore(
            dimension_name="service_compatibility",
            score=8,
            max_score=25,
            rationale="Limited explicit product/service information discovered.",
        )

    def calculate_scale_score(self, employee_range: str) -> DimensionScore:
        lower = employee_range.lower() if employee_range else ""
        if "50-200" in lower or "201-500" in lower or "500+" in lower or "1000" in lower:
            return DimensionScore(
                dimension_name="company_characteristics",
                score=20,
                max_score=20,
                rationale=f"Target scale '{employee_range}' satisfies ideal commercial customer profile.",
            )
        elif "11-50" in lower or "10-50" in lower:
            return DimensionScore(
                dimension_name="company_characteristics",
                score=14,
                max_score=20,
                rationale=f"Growth-stage size '{employee_range}' within acceptable bounds.",
            )
        return DimensionScore(
            dimension_name="company_characteristics",
            score=8,
            max_score=20,
            rationale="Organization size not definitively verified or early-stage.",
        )

    def calculate_opportunity_score(self, insights: BusinessInsight) -> DimensionScore:
        opps = len(insights.market_opportunities)
        challenges = len(insights.operational_challenges_hypotheses)
        if opps >= 2 and challenges >= 1:
            return DimensionScore(
                dimension_name="opportunity_signals",
                score=20,
                max_score=20,
                rationale="High opportunity density with multiple market expansion and operational synergy signals.",
            )
        elif opps >= 1:
            return DimensionScore(
                dimension_name="opportunity_signals",
                score=12,
                max_score=20,
                rationale="Moderate opportunity signals identified.",
            )
        return DimensionScore(
            dimension_name="opportunity_signals",
            score=5,
            max_score=20,
            rationale="Low specific opportunity signals identified in public disclosures.",
        )

    def calculate_evidence_score(self, verification: VerificationResult) -> DimensionScore:
        conf = verification.overall_confidence_score
        score = int(round(conf * 10))
        return DimensionScore(
            dimension_name="evidence_quality",
            score=score,
            max_score=10,
            rationale=f"Evidence audit confidence score is {conf:.2f} based on verified public citations.",
        )

    async def execute_task(
        self,
        profile: CompanyProfile,
        insights: BusinessInsight,
        verification: VerificationResult,
    ) -> LeadQualificationResult:
        dimensions = [
            self.calculate_industry_score(profile.industry),
            self.calculate_service_score(profile),
            self.calculate_scale_score(profile.employee_range),
            self.calculate_opportunity_score(insights),
            self.calculate_evidence_score(verification),
        ]

        total = sum(d.score for d in dimensions)
        is_qualified = total >= self.threshold

        return LeadQualificationResult(
            company_name=profile.name,
            total_score=total,
            is_qualified=is_qualified,
            threshold=self.threshold,
            dimension_scores=dimensions,
            recommended_pipeline_stage="Qualified Lead" if is_qualified else "Prospect Identified",
        )


qualification_agent = LeadQualificationAgent()
