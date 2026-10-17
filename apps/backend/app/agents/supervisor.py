from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.agents.discovery import discovery_agent
from app.agents.scraping import scraping_agent
from app.agents.research import research_agent
from app.agents.verification import verification_agent
from app.agents.insights import insights_agent
from app.agents.qualification import qualification_agent
from app.agents.crm_sync import crm_sync_agent
from app.agents.email_draft import email_draft_agent
from app.agents.delivery import delivery_agent
from app.agents.state_machine import WorkflowState, is_valid_transition
from app.core.logging import logger
from app.models.research import ResearchRun
from app.orchestration.budget import ExecutionBudgetTracker
from app.orchestration.checkpoints import CheckpointManager
from app.repositories.email_repo import EmailRepository
from app.repositories.research_repo import ResearchRepository
from app.schemas.contracts import (
    DiscoveryResult,
    EmailDraftResult,
    LeadQualificationResult,
    ResearchRequest,
    ScrapedPage,
    WorkflowExecutionResult,
)
from app.security.ssrf import validate_target_url


class SupervisorAgent(BaseAgent):
    """
    Agent 1: Supervisor / Orchestrator.
    Coordinates specialized agents through an explicit deterministic state machine,
    persisting checkpoints, logging execution metrics, and enforcing budget constraints.
    """

    def __init__(self):
        super().__init__(name="SupervisorOrchestrator")

    async def execute_workflow(
        self,
        session: AsyncSession,
        run: ResearchRun,
        request: ResearchRequest,
        allow_local_for_testing: bool = False,
    ) -> WorkflowExecutionResult:
        research_repo = ResearchRepository(session)
        email_repo = EmailRepository(session)
        budget = ExecutionBudgetTracker()
        steps_completed: List[str] = []
        errors: List[str] = []
        step_index = 0

        current_state = WorkflowState.CREATED

        async def transition_to(new_state: WorkflowState, data_snapshot: Dict[str, Any]) -> None:
            nonlocal current_state, step_index
            if not is_valid_transition(current_state, new_state):
                logger.warning(f"Unorthodox state transition from {current_state} to {new_state}")
            current_state = new_state
            step_index += 1
            steps_completed.append(new_state.value)
            await research_repo.update_run_status(run.id, new_state.value)
            await CheckpointManager.save_checkpoint(
                session=session,
                run_id=run.id,
                state=new_state.value,
                step_index=step_index,
                state_data=data_snapshot,
            )

        try:
            # Step 1: VALIDATING
            await transition_to(WorkflowState.VALIDATING, {"target_url": request.target_url})
            safe_url = validate_target_url(request.target_url, allow_local_for_testing=allow_local_for_testing)
            domain = urlparse(safe_url).netloc.lower()

            # Step 2: DISCOVERING (Agent 2)
            await transition_to(WorkflowState.DISCOVERING, {"domain": domain})
            discovery_res, dur, err = await discovery_agent.run(request, allow_local_for_testing=allow_local_for_testing)
            await research_repo.record_execution(
                run_id=run.id,
                agent_name=discovery_agent.name,
                state=WorkflowState.DISCOVERING.value,
                output_payload=discovery_res.model_dump() if discovery_res else None,
                duration_ms=dur,
                error_message=err,
            )
            if err or not discovery_res:
                raise RuntimeError(f"Discovery agent failed: {err}")
            budget.add_usage(tokens=50, cost_usd=0.0001)

            # Step 3: EXTRACTING (Agent 3)
            await transition_to(WorkflowState.EXTRACTING, {"pages_count": len(discovery_res.pages)})
            scraped_pages, dur, err = await scraping_agent.run(discovery_res, allow_local_for_testing=allow_local_for_testing)
            await research_repo.record_execution(
                run_id=run.id,
                agent_name=scraping_agent.name,
                state=WorkflowState.EXTRACTING.value,
                output_payload={"pages_scraped": len(scraped_pages) if scraped_pages else 0},
                duration_ms=dur,
                error_message=err,
            )
            if err or not scraped_pages:
                raise RuntimeError(f"Scraping agent failed: {err}")
            budget.add_usage(tokens=100, cost_usd=0.0002)

            # Step 4: RESEARCHING (Agent 4)
            await transition_to(WorkflowState.RESEARCHING, {"scraped_pages_count": len(scraped_pages)})
            profile, dur, err = await research_agent.run(domain, scraped_pages)
            await research_repo.record_execution(
                run_id=run.id,
                agent_name=research_agent.name,
                state=WorkflowState.RESEARCHING.value,
                output_payload=profile.model_dump() if profile else None,
                tokens_used=1200,
                cost_usd=0.002,
                duration_ms=dur,
                error_message=err,
            )
            if err or not profile:
                raise RuntimeError(f"Research agent failed: {err}")
            budget.add_usage(tokens=1200, cost_usd=0.002)

            # Step 5: VERIFYING (Agent 5)
            await transition_to(WorkflowState.VERIFYING, {"facts_extracted": len(profile.facts)})
            verification, dur, err = await verification_agent.run(profile)
            await research_repo.record_execution(
                run_id=run.id,
                agent_name=verification_agent.name,
                state=WorkflowState.VERIFYING.value,
                output_payload=verification.model_dump() if verification else None,
                tokens_used=600,
                cost_usd=0.001,
                duration_ms=dur,
                error_message=err,
            )
            if err or not verification:
                raise RuntimeError(f"Verification agent failed: {err}")
            budget.add_usage(tokens=600, cost_usd=0.001)

            # Step 6: ANALYZING (Agent 6)
            await transition_to(WorkflowState.ANALYZING, {"confidence": verification.overall_confidence_score})
            insights, dur, err = await insights_agent.run(profile, verification)
            await research_repo.record_execution(
                run_id=run.id,
                agent_name=insights_agent.name,
                state=WorkflowState.ANALYZING.value,
                output_payload=insights.model_dump() if insights else None,
                tokens_used=1000,
                cost_usd=0.0015,
                duration_ms=dur,
                error_message=err,
            )
            if err or not insights:
                raise RuntimeError(f"Insights agent failed: {err}")
            budget.add_usage(tokens=1000, cost_usd=0.0015)

            # Step 7: QUALIFYING (Agent 7)
            lead_score, dur, err = await qualification_agent.run(profile, insights, verification)
            await research_repo.record_execution(
                run_id=run.id,
                agent_name=qualification_agent.name,
                state="QUALIFYING",
                output_payload=lead_score.model_dump() if lead_score else None,
                duration_ms=dur,
                error_message=err,
            )
            if err or not lead_score:
                raise RuntimeError(f"Qualification agent failed: {err}")

            # Step 8: SAVING (Agent 8)
            await transition_to(WorkflowState.SAVING, {"lead_score": lead_score.total_score})
            crm_result, dur, err = await crm_sync_agent.run(
                session=session,
                workspace_id=request.workspace_id,
                profile=profile,
                verification=verification,
                insights=insights,
                lead_score=lead_score,
                run_id=run.id,
            )
            await research_repo.record_execution(
                run_id=run.id,
                agent_name=crm_sync_agent.name,
                state=WorkflowState.SAVING.value,
                output_payload=crm_result.model_dump() if crm_result else None,
                duration_ms=dur,
                error_message=err,
            )
            if err or not crm_result:
                raise RuntimeError(f"CRM sync agent failed: {err}")

            # Update run with company_id
            run.company_id = crm_result.company_id

            draft_id: Optional[str] = None
            approval_status: Optional[str] = None

            # Step 9: EMAIL_PREPARATION (Agent 9)
            if request.include_email_generation and lead_score.is_qualified:
                await transition_to(WorkflowState.EMAIL_PREPARATION, {"company_id": crm_result.company_id})
                email_draft, dur, err = await email_draft_agent.run(
                    profile=profile,
                    insights=insights,
                    verification=verification,
                )
                await research_repo.record_execution(
                    run_id=run.id,
                    agent_name=email_draft_agent.name,
                    state=WorkflowState.EMAIL_PREPARATION.value,
                    output_payload=email_draft.model_dump() if email_draft else None,
                    tokens_used=800,
                    cost_usd=0.0012,
                    duration_ms=dur,
                    error_message=err,
                )
                budget.add_usage(tokens=800, cost_usd=0.0012)

                if email_draft:
                    # Find or get primary contact
                    from app.repositories.contact_repo import ContactRepository
                    contact_repo = ContactRepository(session)
                    contacts = await contact_repo.list_by_company(request.workspace_id, crm_result.company_id)
                    target_contact = contacts[0] if contacts else None

                    if target_contact:
                        saved_draft = await email_repo.create_draft(
                            contact_id=target_contact.id,
                            subject=email_draft.subject,
                            body_html=email_draft.body_html,
                            body_text=email_draft.body_text,
                            referenced_facts=",".join(email_draft.referenced_fact_fields),
                        )
                        draft_id = saved_draft.id
                        approval_status = saved_draft.status

                        # Step 10: APPROVAL_PENDING
                        await transition_to(WorkflowState.APPROVAL_PENDING, {"draft_id": draft_id})

            # Terminal Completion
            await transition_to(WorkflowState.COMPLETED, {
                "company_id": crm_result.company_id,
                "score": lead_score.total_score,
                "is_qualified": lead_score.is_qualified,
            })

            return WorkflowExecutionResult(
                run_id=run.id,
                status="COMPLETED",
                company_id=crm_result.company_id,
                company_name=profile.name,
                steps_completed=steps_completed,
                lead_score=lead_score.total_score,
                is_qualified=lead_score.is_qualified,
                email_draft_id=draft_id,
                email_approval_status=approval_status,
                total_duration_ms=int(budget.get_elapsed_seconds() * 1000),
                total_cost_usd=round(budget.accumulated_cost_usd, 4),
            )

        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            errors.append(error_message)
            logger.error(f"Workflow execution failed on run {run.id}: {error_message}")
            await research_repo.update_run_status(run.id, WorkflowState.FAILED.value, error_message=error_message)
            await CheckpointManager.save_checkpoint(
                session=session,
                run_id=run.id,
                state=WorkflowState.FAILED.value,
                step_index=step_index + 1,
                state_data={"error": error_message},
            )
            return WorkflowExecutionResult(
                run_id=run.id,
                status="FAILED",
                steps_completed=steps_completed,
                total_duration_ms=int(budget.get_elapsed_seconds() * 1000),
                total_cost_usd=round(budget.accumulated_cost_usd, 4),
                errors=errors,
            )


supervisor_agent = SupervisorAgent()
