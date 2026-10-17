from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import generate_uuid, utc_now


class EmailDraft(Base):
    __tablename__ = "email_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("email_campaigns.id", ondelete="CASCADE"), nullable=True, index=True)
    contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    referenced_facts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of cited fact IDs
    status: Mapped[str] = mapped_column(String(50), default="PENDING_APPROVAL", index=True)  # PENDING_APPROVAL, APPROVED, REJECTED, SENT
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    campaign: Mapped[Optional["EmailCampaign"]] = relationship("EmailCampaign", back_populates="drafts")
    contact: Mapped["Contact"] = relationship("Contact")
    approvals: Mapped[List["EmailApproval"]] = relationship("EmailApproval", back_populates="draft", cascade="all, delete-orphan")


class EmailApproval(Base):
    __tablename__ = "email_approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    draft_id: Mapped[str] = mapped_column(String(36), ForeignKey("email_drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # APPROVED, REJECTED, EDITED
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    draft: Mapped["EmailDraft"] = relationship("EmailDraft", back_populates="approvals")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("email_drafts.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(50), default="mock")
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)  # PENDING, SENT, DELIVERED, BOUNCED, FAILED, COMPLAINT
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    events: Mapped[List["EmailEvent"]] = relationship("EmailEvent", back_populates="message", cascade="all, delete-orphan")


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email_message_id: Mapped[str] = mapped_column(String(36), ForeignKey("email_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # DELIVERED, OPENED, CLICKED, BOUNCED, COMPLAINT, UNSUBSCRIBED
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON raw webhook payload
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    message: Mapped["EmailMessage"] = relationship("EmailMessage", back_populates="events")


class EmailSuppression(Base):
    __tablename__ = "email_suppressions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(50), default="UNSUBSCRIBE")  # BOUNCE, COMPLAINT, UNSUBSCRIBE, MANUAL
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("workspace_id", "email", name="uq_workspace_email_suppression"),
    )
