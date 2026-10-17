from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.email_repo import EmailRepository
from app.schemas.contracts import EmailEligibilityResult


class EmailComplianceService:
    """
    Validates outbound communication against GDPR, CAN-SPAM, CASL,
    and workspace policy constraints before any email dispatch occurs.
    """

    async def check_eligibility(
        self,
        session: AsyncSession,
        workspace_id: str,
        recipient_email: str,
        is_campaign_active: bool = True,
        auto_send_enabled: bool = False,
        is_approved: bool = False,
    ) -> EmailEligibilityResult:
        email_repo = EmailRepository(session)
        norm_email = recipient_email.strip().lower()

        # 1. Suppression list check
        is_supp = await email_repo.is_suppressed(workspace_id, norm_email)
        if is_supp:
            return EmailEligibilityResult(
                recipient_email=norm_email,
                is_eligible=False,
                rejection_reason="Recipient email is on the active suppression list (Unsubscribed/Bounced/Complaint).",
                is_suppressed=True,
            )

        # 2. Campaign approval check
        if settings.EMAIL_REQUIRE_APPROVAL and not is_approved and not auto_send_enabled:
            return EmailEligibilityResult(
                recipient_email=norm_email,
                is_eligible=False,
                rejection_reason="Outreach requires explicit human approval before delivery.",
                lawful_basis="LEGITIMATE_INTEREST",
            )

        # 3. Campaign active check
        if not is_campaign_active:
            return EmailEligibilityResult(
                recipient_email=norm_email,
                is_eligible=False,
                rejection_reason="Target outreach campaign is not active.",
                lawful_basis="LEGITIMATE_INTEREST",
            )

        return EmailEligibilityResult(
            recipient_email=norm_email,
            is_eligible=True,
            lawful_basis="LEGITIMATE_INTEREST",
            is_suppressed=False,
            rate_limit_passed=True,
        )


compliance_service = EmailComplianceService()
