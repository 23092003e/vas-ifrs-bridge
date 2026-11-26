"""SQLAlchemy ORM model definitions."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversations: Mapped[list[Conversation]] = relationship(back_populates="tenant")
    documents: Mapped[list[Document]] = relationship(back_populates="tenant")
    gl_uploads: Mapped[list[GLUpload]] = relationship(back_populates="tenant")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tenant: Mapped[Tenant | None] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("conversations.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    model_used: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    gcs_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # pending | processing | ready | failed
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    qdrant_collection: Mapped[str | None] = mapped_column(String(255))
    doc_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tenant: Mapped[Tenant] = relationship(back_populates="documents")


class GLUpload(Base):
    __tablename__ = "gl_uploads"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    gcs_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # pending | processing | mapped | failed
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    mapped_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    content_sha256: Mapped[str | None] = mapped_column(String(64))
    accounts: Mapped[list[dict] | None] = mapped_column(JSONB)
    mapping_snapshot: Mapped[list[dict] | None] = mapped_column(JSONB)

    tenant: Mapped[Tenant] = relationship(back_populates="gl_uploads")
    adjustments: Mapped[list[AdjustmentEntry]] = relationship(back_populates="gl_upload")


class AdjustmentEntry(Base):
    __tablename__ = "adjustment_entries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    gl_upload_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("gl_uploads.id"), nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True
    )
    account_code: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str | None] = mapped_column(String(255))
    ifrs_account: Mapped[str | None] = mapped_column(String(50))
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | approved | rejected
    approved_by: Mapped[str | None] = mapped_column(String(255))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lines: Mapped[list[dict] | None] = mapped_column(JSONB)
    created_by: Mapped[str | None] = mapped_column(String(255))

    gl_upload: Mapped[GLUpload] = relationship(back_populates="adjustments")


class GLMappingRule(Base):
    __tablename__ = "gl_mapping_rules"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tenants.id"), primary_key=True
    )
    vas_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    ifrs_code: Mapped[str] = mapped_column(String(100), nullable=False)


class GLReport(Base):
    __tablename__ = "gl_reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False, index=True
    )
    upload_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("gl_uploads.id"), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    tenant_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100))
    diff: Mapped[dict | None] = mapped_column(JSONB)
    request_id: Mapped[str | None] = mapped_column(String(100))
    ip: Mapped[str | None] = mapped_column(String(45))
    ua: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
