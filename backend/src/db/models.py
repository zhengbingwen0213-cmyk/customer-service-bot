"""Database models extended from the PyCore SQLAlchemy template."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Project ORM base."""

    pass


class User(Base):
    """Employee account used by the MVP login and data-visibility rules."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    assigned_tickets: Mapped[list[Ticket]] = relationship(back_populates="assignee")
    uploaded_documents: Mapped[list[Document]] = relationship(back_populates="uploaded_by")


class Customer(Base):
    """Minimal customer profile referenced by tickets and basic memories."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tickets: Mapped[list[Ticket]] = relationship(back_populates="customer")
    memories: Mapped[list[CustomerMemory]] = relationship(back_populates="customer")


class Ticket(Base):
    """Customer-service ticket lifecycle: open -> processing -> completed."""

    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'processing', 'completed')", name="ck_tickets_status"),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_tickets_priority"),
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_assignee_status", "assignee_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    assignee_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    related_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignee: Mapped[User | None] = relationship(back_populates="assigned_tickets")
    customer: Mapped[Customer] = relationship(back_populates="tickets")
    messages: Mapped[list[ConversationMessage]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base):
    """Ticket conversation message ordered by creation time."""

    __tablename__ = "conversation_messages"
    __table_args__ = (
        CheckConstraint(
            "sender IN ('customer', 'employee', 'bot')",
            name="ck_conversation_messages_sender",
        ),
        Index("ix_conversation_messages_ticket_created", "ticket_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender: Mapped[str] = mapped_column(String(32), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    used_assistant_answer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ticket: Mapped[Ticket] = relationship(back_populates="messages")


class QaItem(Base):
    """Managed QA knowledge item."""

    __tablename__ = "qa_items"
    __table_args__ = (
        CheckConstraint("status IN ('enabled', 'disabled')", name="ck_qa_items_status"),
        Index("ix_qa_items_status_updated", "status", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="enabled")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Document(Base):
    """Document metadata for local upload and indexing state."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'completed', 'failed')",
            name="ck_documents_status",
        ),
        Index("ix_documents_status_updated", "status", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    uploaded_by: Mapped[User] = relationship(back_populates="uploaded_documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    """Searchable chunk extracted from a completed document."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_document_index", "document_id", "chunk_index"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped[Document] = relationship(back_populates="chunks")


class VectorIndex(Base):
    """Traceable vector-index metadata and optional serialized embedding payload."""

    __tablename__ = "vector_indexes"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('qa', 'document_chunk')",
            name="ck_vector_indexes_source_type",
        ),
        Index("ix_vector_indexes_source", "source_type", "source_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=1024)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_vector: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class CustomerMemory(Base):
    """MVP long-term memory placeholder for basic customer facts."""

    __tablename__ = "customer_memories"
    __table_args__ = (
        Index("ix_customer_memories_customer_key", "customer_id", "memory_key", unique=True),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    memory_key: Mapped[str] = mapped_column(String(128), nullable=False)
    memory_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_ticket_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    customer: Mapped[Customer] = relationship(back_populates="memories")
