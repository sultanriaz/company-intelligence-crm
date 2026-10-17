from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import generate_uuid, utc_now


class LeadScore(Base):
    __tablename__ = "lead_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    industry_score: Mapped[int] = mapped_column(Integer, default=0)
    service_score: Mapped[int] = mapped_column(Integer, default=0)
    scale_score: Mapped[int] = mapped_column(Integer, default=0)
    opportunity_score: Mapped[int] = mapped_column(Integer, default=0)
    evidence_score: Mapped[int] = mapped_column(Integer, default=0)
    is_qualified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    qualification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="lead_score")
    explanations: Mapped[List["LeadScoreExplanation"]] = relationship("LeadScoreExplanation", back_populates="lead_score", cascade="all, delete-orphan", lazy="selectin")


class LeadScoreExplanation(Base):
    __tablename__ = "lead_score_explanations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_score_id: Mapped[str] = mapped_column(String(36), ForeignKey("lead_scores.id", ondelete="CASCADE"), nullable=False, index=True)
    dimension: Mapped[str] = mapped_column(String(50), nullable=False)
    score_assigned: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=25)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    lead_score: Mapped["LeadScore"] = relationship("LeadScore", back_populates="explanations")


class CRMActivity(Base):
    __tablename__ = "crm_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # NOTE, CALL, EMAIL_SENT, STATUS_CHANGE, RESEARCH_DONE
    details: Mapped[str] = mapped_column(Text, nullable=False)  # JSON or text description
    created_by: Mapped[str] = mapped_column(String(100), default="SYSTEM")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
