import time
from typing import Any, Dict, Optional, Tuple
from app.core.logging import logger


class BaseAgent:
    """Base class for all specialized platform agents."""

    def __init__(self, name: str):
        self.name = name

    async def execute_task(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    async def run(self, *args, **kwargs) -> Tuple[Any, int, Optional[str]]:
        """
        Executes agent task and measures duration in milliseconds.
        Returns: (result, duration_ms, error_message)
        """
        start = time.perf_counter()
        logger.info(f"Agent [{self.name}] starting execution...")
        try:
            result = await self.execute_task(*args, **kwargs)
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info(f"Agent [{self.name}] completed successfully in {duration_ms}ms.")
            return result, duration_ms, None
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Agent [{self.name}] failed after {duration_ms}ms: {error_msg}")
            return None, duration_ms, error_msg
