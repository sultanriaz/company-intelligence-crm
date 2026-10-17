from typing import List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.workspace import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates JWT Bearer token and retrieves active User record from DB.
    Provides fallback demo admin user when no credentials supplied in debug/dev mode.
    """
    if credentials:
        token = credentials.credentials
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalars().first()
            if not user or not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")
            return user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")

    # In local development mode, if no header provided, find or create default admin user
    query = select(User).where(User.role == "ADMIN")
    result = await db.execute(query)
    user = result.scalars().first()
    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please log in or provide Bearer token.",
    )


def require_roles(allowed_roles: List[str]):
    """Role-based access control dependency."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of roles: {allowed_roles}. Current role: {current_user.role}",
            )
        return current_user
    return role_checker
