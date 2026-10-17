from datetime import datetime
from typing import Optional, List
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import generate_uuid, utc_now


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    target_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="CREATED", index=True)
    # CREATED, VALIDATING, DISCOVERING, EXTRACTING, RESEARCHING, VERIFYING, ANALYZING, SAVING, EMAIL_PREPARATION, APPROVAL_PENDING, SENDING, COMPLETED, FAILED, CANCELLED, PARTIALLY_COMPLETED, RETRY_PENDING
    triggered_by: Mapped[str] = mapped_column(String(100), default="MANUAL")
    config_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    executions: Mapped[List["AgentExecution"]] = relationship("AgentExecution", back_populates="run", cascade="all, delete-orphan")
    checkpoints: Mapped[List["WorkflowCheckpoint"]] = relationship("WorkflowCheckpoint", back_populates="run", cascade="all, delete-orphan")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    research_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    input_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    output_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="executions")


class WorkflowCheckpoint(Base):
    __tablename__ = "workflow_checkpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    research_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    state_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON snapshot
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="checkpoints")
