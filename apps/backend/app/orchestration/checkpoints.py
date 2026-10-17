import json
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.research_repo import ResearchRepository


class CheckpointManager:
    """Manages recording and retrieving workflow state checkpoints."""

    @staticmethod
    async def save_checkpoint(
        session: AsyncSession,
        run_id: str,
        state: str,
        step_index: int,
        state_data: Dict[str, Any],
    ) -> None:
        repo = ResearchRepository(session)
        await repo.create_checkpoint(
            run_id=run_id,
            state=state,
            step_index=step_index,
            state_data=state_data,
        )
