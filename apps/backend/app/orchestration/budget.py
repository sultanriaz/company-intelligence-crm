import time
from app.core.config import settings
from app.core.exceptions import WorkflowExecutionException


class ExecutionBudgetTracker:
    """
    Enforces maximum cost and execution timeout limits per workflow run:
    - Default max cost: $2.00 USD
    - Default max duration: 300 seconds
    """

    def __init__(
        self,
        max_cost_usd: float = None,
        max_duration_seconds: int = None,
    ):
        self.max_cost_usd = max_cost_usd if max_cost_usd is not None else settings.AGENT_MAX_COST_USD_PER_RUN
        self.max_duration_seconds = max_duration_seconds if max_duration_seconds is not None else settings.AGENT_MAX_EXECUTION_SECONDS
        self.start_time = time.time()
        self.total_tokens: int = 0
        self.accumulated_cost_usd: float = 0.0

    def add_usage(self, tokens: int, cost_usd: float = 0.0) -> None:
        self.total_tokens += tokens
        self.accumulated_cost_usd += cost_usd
        self.assert_within_limits()

    def get_elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def assert_within_limits(self) -> None:
        elapsed = self.get_elapsed_seconds()
        if elapsed > self.max_duration_seconds:
            raise WorkflowExecutionException(
                f"Workflow exceeded maximum allowed duration of {self.max_duration_seconds}s (elapsed: {elapsed:.1f}s)."
            )
        if self.accumulated_cost_usd > self.max_cost_usd:
            raise WorkflowExecutionException(
                f"Workflow exceeded maximum cost budget of ${self.max_cost_usd:.2f} USD (accumulated: ${self.accumulated_cost_usd:.4f} USD)."
            )
