from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.audit import IntegrationConfig
from app.models.workspace import User
from app.security.crypto import decrypt_secret, encrypt_secret

router = APIRouter(prefix="/integrations", tags=["Integration Credentials"])


class IntegrationConfigRequest(BaseModel):
    provider_type: str  # openai, anthropic, resend, sendgrid, ses
    secret_key: str
    is_enabled: bool = True


class IntegrationConfigResponse(BaseModel):
    id: str
    workspace_id: str
    provider_type: str
    is_enabled: bool
    masked_key: str


@router.get("", response_model=List[IntegrationConfigResponse])
async def list_integrations(
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """List configured integration credentials with masked keys."""
    query = select(IntegrationConfig).where(IntegrationConfig.workspace_id == workspace_id)
    res = await db.execute(query)
    configs = res.scalars().all()

    out = []
    for c in configs:
        try:
            plain = decrypt_secret(c.encrypted_credentials)
            masked = plain[:4] + "..." + plain[-4:] if len(plain) > 8 else "***"
        except Exception:
            masked = "***"
        out.append(
            IntegrationConfigResponse(
                id=c.id,
                workspace_id=c.workspace_id,
                provider_type=c.provider_type,
                is_enabled=c.is_enabled,
                masked_key=masked,
            )
        )
    return out


@router.post("")
async def save_integration_config(
    data: IntegrationConfigRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Store encrypted third-party provider credential (AES-GCM-256)."""
    encrypted = encrypt_secret(data.secret_key)
    query = select(IntegrationConfig).where(
        and_(
            IntegrationConfig.workspace_id == workspace_id,
            IntegrationConfig.provider_type == data.provider_type.lower(),
        )
    )
    res = await db.execute(query)
    existing = res.scalars().first()

    if existing:
        existing.encrypted_credentials = encrypted
        existing.is_enabled = data.is_enabled
    else:
        new_conf = IntegrationConfig(
            workspace_id=workspace_id,
            provider_type=data.provider_type.lower(),
            encrypted_credentials=encrypted,
            is_enabled=data.is_enabled,
        )
        db.add(new_conf)

    await db.commit()
    return {"message": f"Integration config for {data.provider_type} saved successfully."}
