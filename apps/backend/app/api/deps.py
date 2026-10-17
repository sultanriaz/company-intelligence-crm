from fastapi import Depends
from app.auth.dependencies import get_current_user, require_roles
from app.models.workspace import User


async def get_current_workspace_id(current_user: User = Depends(get_current_user)) -> str:
    """Convenience dependency returning the authenticated user's workspace_id."""
    return current_user.workspace_id
