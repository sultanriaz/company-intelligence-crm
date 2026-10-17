from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import generate_uuid, utc_now


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    primary_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    employee_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PROSPECT", index=True)  # PROSPECT, RESEARCHING, QUALIFIED, CONTACTED, UNQUALIFIED, CUSTOMER
    pipeline_stage_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("crm_stages.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="companies")
    domains: Mapped[List["CompanyDomain"]] = relationship("CompanyDomain", back_populates="company", cascade="all, delete-orphan", lazy="selectin")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="company", cascade="all, delete-orphan", lazy="selectin")
    sources: Mapped[List["CompanySource"]] = relationship("CompanySource", back_populates="company", cascade="all, delete-orphan", lazy="selectin")
    facts: Mapped[List["ResearchFact"]] = relationship("ResearchFact", back_populates="company", cascade="all, delete-orphan", lazy="selectin")
    reports: Mapped[List["ResearchReport"]] = relationship("ResearchReport", back_populates="company", cascade="all, delete-orphan", lazy="selectin")
    lead_score: Mapped[Optional["LeadScore"]] = relationship("LeadScore", back_populates="company", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    stage: Mapped[Optional["CRMStage"]] = relationship("CRMStage", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("workspace_id", "primary_domain", name="uq_workspace_company_domain"),
    )


class CompanyDomain(Base):
    __tablename__ = "company_domains"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="domains")

    __table_args__ = (
        UniqueConstraint("company_id", "domain", name="uq_company_domain"),
    )


class CompanySource(Base):
    __tablename__ = "company_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    http_status: Mapped[int] = mapped_column(Integer, default=200)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="sources")


class ResearchFact(Base):
    __tablename__ = "research_facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")  # VERIFIED, PROVISIONAL, CONTRADICTED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="facts")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    challenges_hypotheses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON formatted string
    opportunities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)          # JSON formatted string
    tech_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)             # JSON formatted string
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="reports")
