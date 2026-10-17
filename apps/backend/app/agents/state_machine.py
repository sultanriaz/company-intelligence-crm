from enum import Enum
from typing import Set


class WorkflowState(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    DISCOVERING = "DISCOVERING"
    EXTRACTING = "EXTRACTING"
    RESEARCHING = "RESEARCHING"
    VERIFYING = "VERIFYING"
    ANALYZING = "ANALYZING"
    SAVING = "SAVING"
    EMAIL_PREPARATION = "EMAIL_PREPARATION"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    SENDING = "SENDING"
    COMPLETED = "COMPLETED"

    # Terminal / Recovery States
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    RETRY_PENDING = "RETRY_PENDING"


VALID_TRANSITIONS: dict[WorkflowState, Set[WorkflowState]] = {
    WorkflowState.CREATED: {WorkflowState.VALIDATING, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.VALIDATING: {WorkflowState.DISCOVERING, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.DISCOVERING: {WorkflowState.EXTRACTING, WorkflowState.FAILED, WorkflowState.CANCELLED, WorkflowState.RETRY_PENDING},
    WorkflowState.EXTRACTING: {WorkflowState.RESEARCHING, WorkflowState.PARTIALLY_COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED, WorkflowState.RETRY_PENDING},
    WorkflowState.RESEARCHING: {WorkflowState.VERIFYING, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.VERIFYING: {WorkflowState.ANALYZING, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.ANALYZING: {WorkflowState.SAVING, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.SAVING: {WorkflowState.EMAIL_PREPARATION, WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.EMAIL_PREPARATION: {WorkflowState.APPROVAL_PENDING, WorkflowState.SENDING, WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.APPROVAL_PENDING: {WorkflowState.SENDING, WorkflowState.CANCELLED, WorkflowState.COMPLETED},
    WorkflowState.SENDING: {WorkflowState.COMPLETED, WorkflowState.FAILED},
    WorkflowState.RETRY_PENDING: {WorkflowState.DISCOVERING, WorkflowState.EXTRACTING, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.COMPLETED: set(),
    WorkflowState.FAILED: set(),
    WorkflowState.CANCELLED: set(),
    WorkflowState.PARTIALLY_COMPLETED: {WorkflowState.RESEARCHING, WorkflowState.SAVING, WorkflowState.COMPLETED},
}


def is_valid_transition(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """Checks whether a state machine transition is legally permitted."""
    allowed = VALID_TRANSITIONS.get(from_state, set())
    return to_state in allowed
