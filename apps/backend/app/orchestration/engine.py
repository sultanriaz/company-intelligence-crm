import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import supervisor_agent
from app.models.research import ResearchRun
from app.repositories.research_repo import ResearchRepository
from app.schemas.contracts import ResearchRequest, WorkflowExecutionResult


class WorkflowOrchestrationEngine:
    """
    High-level engine to launch, monitor, and resume company research workflows.
    """

    async def start_research_run(
        self,
        session: AsyncSession,
        workspace_id: str,
        target_url: str,
        company_name: Optional[str] = None,
        crawl_depth: int = 2,
        max_pages: int = 15,
        include_email_generation: bool = True,
        triggered_by: str = "MANUAL",
        allow_local_for_testing: bool = False,
    ) -> WorkflowExecutionResult:
        research_repo = ResearchRepository(session)

        # 1. Create ResearchRun in database
        config_snapshot = {
            "crawl_depth": crawl_depth,
            "max_pages": max_pages,
            "include_email_generation": include_email_generation,
            "target_url": target_url,
        }
        run = ResearchRun(
            workspace_id=workspace_id,
            target_url=target_url,
            status="CREATED",
            triggered_by=triggered_by,
            config_snapshot=json.dumps(config_snapshot),
        )
        session.add(run)
        await session.flush()

        request = ResearchRequest(
            workspace_id=workspace_id,
            target_url=target_url,
            company_name=company_name,
            crawl_depth=crawl_depth,
            max_pages=max_pages,
            include_email_generation=include_email_generation,
            trigger_source=triggered_by,
        )

        # 2. Delegate to Supervisor Agent
        result = await supervisor_agent.execute_workflow(
            session=session,
            run=run,
            request=request,
            allow_local_for_testing=allow_local_for_testing,
        )

        return result


orchestration_engine = WorkflowOrchestrationEngine()
